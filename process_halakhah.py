#!/usr/bin/env python3
"""Utility to normalize Halakhah texts into Siman/Seif JSON files.

This script reads every JSON file that lives under ``Halakhah`` and
produces a cleaned structure where each leaf node is organized into
Simanim (chapters) and Seifim (paragraphs).  For ``Chayyei Adam`` the
matching ``Nishmat Adam`` commentary is merged directly into the output
structure.  Each processed book is written as an individual JSON file in
``Halakhah_processed``.

Usage:
    python process_halakhah.py
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT_DIR = Path(__file__).resolve().parent
HALAKHAH_DIR = ROOT_DIR / "Halakhah"
OUTPUT_DIR = ROOT_DIR / "Halakhah_processed"


SIMAN_TITLE_RE = re.compile(r"\s*<big><strong>(.*?)</strong></big>", re.IGNORECASE | re.DOTALL)


def flatten_to_html(value: Any) -> str:
    """Return a single HTML string for ``value``.

    Values inside the Sefaria exports can be deeply nested lists.  We
    collapse those structures into a simple string, preserving the
    existing inline HTML by concatenating fragments with ``<br>``.
    """

    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Iterable):
        parts: List[str] = []
        for piece in value:
            fragment = flatten_to_html(piece)
            if fragment:
                parts.append(fragment)
        return "<br>".join(parts)
    return str(value).strip()


def html_to_plain(text: str) -> str:
    """Remove HTML markup and normalise whitespace for ``text``."""

    if not text:
        return ""

    normalized = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    normalized = re.sub(r"<[^>]+>", "", normalized)
    normalized = unescape(normalized)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u2028", "\n").replace("\u2029", "\n")
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r"\xa0", " ", normalized)
    return normalized.strip()


def extract_siman_title(text_html: str) -> Optional[str]:
    match = SIMAN_TITLE_RE.match(text_html or "")
    if match:
        return html_to_plain(match.group(1))
    return None


def build_schema_lookup(schema: Dict[str, Any]) -> Dict[Tuple[str, ...], Dict[str, Optional[str]]]:
    """Create a mapping from title paths to schema metadata."""

    mapping: Dict[Tuple[str, ...], Dict[str, Optional[str]]] = {}

    def walk(node: Dict[str, Any], path: Tuple[str, ...]) -> None:
        title_en = node.get("enTitle")
        title_he = node.get("heTitle")
        new_path = path
        if title_en:
            new_path = path + (title_en,)
            mapping[new_path] = {"title": title_en, "heTitle": title_he}
        for child in node.get("nodes", []) or []:
            if isinstance(child, dict):
                walk(child, new_path)

    for root in schema.get("nodes", []) or []:
        if isinstance(root, dict):
            walk(root, tuple())

    return mapping


@dataclass
class ProcessResult:
    node: Dict[str, Any]
    plain_segments: List[str]


def process_siman(data: Any, commentary: Any) -> ProcessResult:
    seifim: List[Dict[str, Any]] = []
    plain_segments: List[str] = []

    if data is None:
        return ProcessResult({"seifim": seifim}, plain_segments)

    if isinstance(data, list):
        values = data
    else:
        values = [data]

    for index, raw in enumerate(values, start=1):
        seif_html = flatten_to_html(raw)
        if not seif_html.strip():
            continue
        seif_plain = html_to_plain(seif_html)

        commentary_payload: Dict[str, Any] = {}
        comment_entry = None
        if commentary is not None:
            if isinstance(commentary, list) and index - 1 < len(commentary):
                comment_entry = commentary[index - 1]
            elif not isinstance(commentary, list) and index == 1:
                comment_entry = commentary
        comment_html = flatten_to_html(comment_entry)
        if comment_html.strip():
            commentary_payload["Nishmat Adam"] = {
                "text_html": comment_html,
                "text_plain": html_to_plain(comment_html),
            }

        seif_record: Dict[str, Any] = {
            "number": index,
            "text_html": seif_html,
            "text_plain": seif_plain,
        }
        if commentary_payload:
            seif_record["commentary"] = commentary_payload

        seifim.append(seif_record)
        plain_segments.append(seif_plain)

    return ProcessResult({"seifim": seifim}, plain_segments)


def process_node(
    key: Optional[str],
    value: Any,
    *,
    commentary: Any,
    schema_lookup: Dict[Tuple[str, ...], Dict[str, Optional[str]]],
    path: Tuple[str, ...],
) -> ProcessResult:
    node_payload: Dict[str, Any] = {}
    plain_segments: List[str] = []

    current_path = path + ((key,) if key else tuple())
    schema_meta = schema_lookup.get(tuple(current_path))

    if key is not None:
        node_payload["key"] = key

    if schema_meta:
        if schema_meta.get("title"):
            node_payload["title"] = schema_meta["title"]
        if schema_meta.get("heTitle"):
            node_payload["heTitle"] = schema_meta["heTitle"]
    elif key:
        node_payload["title"] = key

    if isinstance(value, dict):
        child_nodes: List[Dict[str, Any]] = []
        for child_key, child_value in value.items():
            child_commentary = commentary.get(child_key) if isinstance(commentary, dict) else None
            child_result = process_node(
                child_key,
                child_value,
                commentary=child_commentary,
                schema_lookup=schema_lookup,
                path=current_path,
            )
            if child_result.node:
                child_nodes.append(child_result.node)
            plain_segments.extend(child_result.plain_segments)
        if child_nodes:
            node_payload["nodes"] = child_nodes
        return ProcessResult(node_payload, plain_segments)

    if isinstance(value, list):
        simanim: List[Dict[str, Any]] = []
        for index, siman_content in enumerate(value, start=1):
            commentary_chunk = None
            if isinstance(commentary, list) and index - 1 < len(commentary):
                commentary_chunk = commentary[index - 1]
            siman_result = process_siman(siman_content, commentary_chunk)
            siman_record: Dict[str, Any] = {
                "number": index,
                "seifim": siman_result.node["seifim"],
            }
            if siman_result.node["seifim"]:
                maybe_title = extract_siman_title(siman_result.node["seifim"][0]["text_html"])
                if maybe_title:
                    siman_record["title"] = maybe_title
            simanim.append(siman_record)
            plain_segments.extend(siman_result.plain_segments)
        node_payload["simanim"] = simanim
    else:
        siman_result = process_siman(value, commentary)
        siman_record = {
            "number": 1,
            "seifim": siman_result.node["seifim"],
        }
        if siman_result.node["seifim"]:
            maybe_title = extract_siman_title(siman_result.node["seifim"][0]["text_html"])
            if maybe_title:
                siman_record["title"] = maybe_title
        node_payload["simanim"] = [siman_record]
        plain_segments.extend(siman_result.plain_segments)

    return ProcessResult(node_payload, plain_segments)


def process_book(path: Path, *, commentary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    text_tree = data.get("text", {})
    schema_lookup = build_schema_lookup(data.get("schema", {}))

    book_nodes: List[Dict[str, Any]] = []
    plain_segments: List[str] = []

    if isinstance(text_tree, dict):
        items = list(text_tree.items())
    else:
        items = [(None, text_tree)]

    for key, value in items:
        if isinstance(commentary, dict) and key is not None:
            commentary_subtree = commentary.get(key)
        else:
            commentary_subtree = commentary if key is None else None
        display_key = key
        if display_key is None:
            display_key = data.get("title") or "Text"
        result = process_node(
            display_key,
            value,
            commentary=commentary_subtree,
            schema_lookup=schema_lookup,
            path=tuple(),
        )
        book_nodes.append(result.node)
        plain_segments.extend(result.plain_segments)

    metadata: Dict[str, Any] = {
        "title": data.get("title"),
        "heTitle": data.get("heTitle"),
        "language": data.get("language"),
        "versionTitle": data.get("versionTitle"),
        "versionSource": data.get("versionSource"),
        "sections": book_nodes,
        "plain_text": "\n\n".join(segment for segment in plain_segments if segment),
    }

    if "categories" in data:
        metadata["categories"] = data["categories"]

    return metadata


def determine_commentary(book_path: Path) -> Optional[Dict[str, Any]]:
    """Return commentary tree for Chayyei Adam when needed."""

    if book_path.parts[-3:] == ("Chayyei Adam", "Hebrew", "merged.json"):
        commentary_path = book_path.parent.parent / "Nishmat Adam" / "Hebrew" / "merged.json"
        if commentary_path.exists():
            with commentary_path.open(encoding="utf-8") as handle:
                return json.load(handle).get("text", {})
    return None


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    for json_path in sorted(HALAKHAH_DIR.rglob("*.json")):
        if json_path.is_dir():
            continue
        if "Nishmat Adam" in json_path.parts:
            # Handled as commentary for Chayyei Adam; no standalone export
            continue
        commentary_tree = determine_commentary(json_path)
        processed = process_book(json_path, commentary=commentary_tree)
        output_name = json_path.parent.parent.name
        if json_path.name not in {"merged.json"}:
            # Preserve the specific edition name for alternate versions.
            stem = json_path.stem.replace(" ", "_")
            output_name = f"{output_name}__{stem}"
        output_file = OUTPUT_DIR / f"{output_name}.json"
        output_file.write_text(json.dumps(processed, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {output_file.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
