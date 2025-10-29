#!/usr/bin/env python3
"""
Tur Commentary Merger - Creates separate JSON files for each commentary

This script merges Tur texts with their commentaries, creating a separate
output file for each commentary. Structure is simple: siman-based only.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Iterable
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TurCommentaryMerger:
    """Merges Tur texts with commentaries, creating separate files per commentary."""

    SECTIONS = [
        "Orach Chaim",
        "Yoreh Deah",
        "Even HaEzer",
        "Choshen Mishpat"
    ]

    SECTION_FILE_MAP = {
        "Orach Chaim": "Orach Chaim.json",
        "Yoreh Deah": "Yoreh Deah.json",
        "Even HaEzer": "Even HaEzer.json",
        "Choshen Mishpat": "Choshen Mishpat.json"
    }

    # Map commentary names to their directory and file patterns
    COMMENTARIES = {
        "Bach": {
            "dir": "Bach",
            "file": "Tur {section}.json",
            "display_name": "Bach"
        },
        "Beit_Yosef": {
            "dir": "Beit Yosef",
            "file": "Tur {section}, Vilna, 1923.json",
            "display_name": "Beit Yosef"
        },
        "Darkhei_Moshe": {
            "dir": "Darkhei Moshe",
            "file": "Tur {section}, Vilna, 1923.json",
            "display_name": "Darkhei Moshe"
        },
        "Drisha": {
            "dir": "Drisha",
            "file": "Tur {section}, Vilna, 1923.json",
            "display_name": "Drisha"
        },
        "Prisha": {
            "dir": "Prisha",
            "file": "Tur {section}, Vilna, 1923.json",
            "display_name": "Prisha"
        }
    }

    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            base_path = Path.cwd() / "Tur"

        self.base_path = Path(base_path)
        logger.info(f"Base path set to: {self.base_path}")

        if not self.base_path.exists():
            raise FileNotFoundError(f"Directory not found: {self.base_path}")

        self.commentary_path = self.base_path / "Commentary"

    def clean_text(self, text: str) -> str:
        """Clean text from HTML tags and excessive whitespace."""
        if not isinstance(text, str):
            return text

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    PLACEHOLDER_PATTERN = re.compile(r'<i\b([^>]*)></i>', re.IGNORECASE)
    ATTR_PATTERN = re.compile(r'([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*"([^"]*)"')

    def flatten_to_strings(self, data: Any, clean_text: bool = True) -> List[str]:
        """Flatten nested lists/dicts into a list of clean strings."""

        flattened: List[str] = []

        def _recurse(item: Any):
            if item is None:
                return

            if isinstance(item, str):
                text = self.clean_text(item) if clean_text else item
                text = text.strip()
                if text:
                    flattened.append(text)
                return

            if isinstance(item, list):
                for sub in item:
                    _recurse(sub)
                return

            if isinstance(item, dict):
                for value in item.values():
                    _recurse(value)
                return

            text = self.clean_text(str(item)) if clean_text else str(item)
            text = text.strip()
            if text:
                flattened.append(text)

        _recurse(data)
        return flattened

    def _parse_tag_attributes(self, tag_contents: str) -> Dict[str, str]:
        """Parse HTML-style attributes from a tag string."""

        attributes: Dict[str, str] = {}
        for match in self.ATTR_PATTERN.finditer(tag_contents or ""):
            key = match.group(1)
            value = match.group(2)
            if key not in attributes:
                attributes[key] = value
        return attributes

    def _generate_commentary_keys(self, siman_num: int, index: int) -> List[str]:
        """Generate lookup keys for a commentary segment."""

        keys: List[str] = []

        def _add(candidate: str):
            if candidate and candidate not in keys:
                keys.append(candidate)

        base_forms = [
            f"{siman_num}.{index}",
            f"{siman_num}.{index:02d}",
            f"{siman_num}.{index:03d}",
            f"{siman_num}-{index}",
            f"{siman_num}:{index}",
        ]

        for form in base_forms:
            _add(form)

        for width in (1, 2, 3):
            _add(str(index).zfill(width))

        return keys

    def _normalise_order_candidates(self, order: str, siman_num: int) -> List[str]:
        """Create a list of candidate keys that might match an order attribute."""

        if not order:
            return []

        order = order.strip()
        candidates: List[str] = []

        def _add(candidate: Optional[str]):
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        collapsed = re.sub(r"\s+", "", order)
        _add(order)
        _add(collapsed)
        _add(collapsed.replace('-', '.'))
        _add(collapsed.replace(':', '.'))

        numbers = re.findall(r"\d+", collapsed)
        if numbers:
            first = numbers[0]
            last = numbers[-1]
            _add(first)
            _add(last)
            _add(f"{first}.{last}")
            _add(f"{first}-{last}")
            _add(f"{first}:{last}")

            try:
                last_int = int(last)
            except ValueError:
                last_int = None

            if last_int is not None:
                _add(str(last_int))
                _add(f"{last_int:02d}")
                _add(f"{last_int:03d}")
                _add(f"{first}.{last_int}")
                _add(f"{first}.{last_int:02d}")
                _add(f"{first}-{last_int}")
                _add(f"{first}:{last_int}")

                if first != str(siman_num):
                    _add(f"{siman_num}.{last_int}")
                    _add(f"{siman_num}.{last_int:02d}")
                    _add(f"{siman_num}-{last_int}")
                    _add(f"{siman_num}:{last_int}")

        return candidates

    def _prepare_commentary_segments(
        self,
        siman_num: int,
        commentary_segments: Iterable[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """Create indexed commentary segments and lookup mapping."""

        segments: List[Dict[str, Any]] = []
        index_map: Dict[str, List[Dict[str, Any]]] = {}

        for idx, raw_text in enumerate(commentary_segments, start=1):
            if raw_text is None:
                continue

            raw_str = str(raw_text)
            clean_str = self.clean_text(raw_str)

            segment = {
                "index": idx,
                "raw": raw_str,
                "clean": clean_str,
                "keys": self._generate_commentary_keys(siman_num, idx)
            }

            segments.append(segment)

            for key in segment["keys"]:
                index_map.setdefault(key, []).append(segment)

        return segments, index_map

    def _resolve_commentary_segment(
        self,
        order: Optional[str],
        siman_num: int,
        segments: List[Dict[str, Any]],
        index_map: Dict[str, List[Dict[str, Any]]],
        used_indices: set
    ) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
        """Match a commentary segment based on order, falling back as needed."""

        if order:
            for candidate in self._normalise_order_candidates(order, siman_num):
                for segment in index_map.get(candidate, []):
                    if segment["index"] in used_indices:
                        continue
                    used_indices.add(segment["index"])
                    return segment, "matched", candidate

        for segment in segments:
            if segment["index"] in used_indices:
                continue
            used_indices.add(segment["index"])
            preferred = segment["keys"][0] if segment["keys"] else None
            return segment, "fallback", preferred

        return None, "missing", None

    def _build_text_payload(
        self,
        content: str,
        raw: str,
        section: str,
        siman_num: int,
        text_index: int
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "content": content,
            "source": {
                "type": "primary",
                "work": "Tur",
                "section": section,
                "siman": siman_num,
                "segment_index": text_index
            }
        }

        raw_stripped = raw.strip()
        if raw_stripped and raw_stripped != content:
            payload["raw"] = raw_stripped

        return payload

    def _build_commentary_payload(
        self,
        segment: Optional[Dict[str, Any]],
        status: str,
        order: Optional[str],
        commentator: str,
        commentary_display: str,
        commentary_key: str,
        section: str,
        siman_num: int,
        clean_text: bool,
        matched_key: Optional[str]
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "commentator": commentator,
            "order": order,
            "status": status,
            "source": {
                "type": "commentary",
                "work": commentary_display,
                "section": section,
                "siman": siman_num,
                "commentary_key": commentary_key
            }
        }

        if matched_key:
            payload["resolved_order"] = matched_key

        if segment:
            payload["source"]["comment_index"] = segment["index"]

            if clean_text:
                payload["content"] = segment["clean"]
            else:
                payload["content"] = segment["raw"].strip()

            if segment["raw"] and (not clean_text or segment["clean"] != segment["raw"]):
                payload["raw"] = segment["raw"]
        else:
            payload["content"] = None

        return payload

    def _consume_main_segment(
        self,
        raw_segment: str,
        section: str,
        siman_num: int,
        commentary_display: str,
        commentary_key: str,
        segments: List[Dict[str, Any]],
        index_map: Dict[str, List[Dict[str, Any]]],
        used_indices: set,
        text_index: int,
        clean_text: bool
    ) -> Tuple[List[Dict[str, Any]], int]:
        entries: List[Dict[str, Any]] = []
        buffer = ""
        cursor = 0

        for match in self.PLACEHOLDER_PATTERN.finditer(raw_segment):
            buffer += raw_segment[cursor:match.start()]
            entry: Dict[str, Any] = {}

            if buffer:
                processed = self.clean_text(buffer) if clean_text else buffer.strip()
                if processed:
                    text_index += 1
                    entry["text"] = self._build_text_payload(
                        processed,
                        buffer,
                        section,
                        siman_num,
                        text_index
                    )

            attr_text = match.group(1) or ""
            attrs = self._parse_tag_attributes(attr_text)
            commentator = attrs.get("data-commentator") or commentary_display
            order = attrs.get("data-order")

            segment, status, matched_key = self._resolve_commentary_segment(
                order,
                siman_num,
                segments,
                index_map,
                used_indices
            )

            entry["commentary"] = self._build_commentary_payload(
                segment,
                status,
                order,
                commentator,
                commentary_display,
                commentary_key,
                section,
                siman_num,
                clean_text,
                matched_key
            )

            if entry:
                entries.append(entry)

            buffer = ""
            cursor = match.end()

        buffer += raw_segment[cursor:]
        if buffer:
            processed = self.clean_text(buffer) if clean_text else buffer.strip()
            if processed:
                text_index += 1
                entries.append({
                    "text": self._build_text_payload(
                        processed,
                        buffer,
                        section,
                        siman_num,
                        text_index
                    )
                })

        return entries, text_index

    def _build_embedded_entries(
        self,
        main_content: Any,
        comm_content: Any,
        section: str,
        siman_num: int,
        commentary_display: str,
        commentary_key: str,
        clean_text: bool
    ) -> List[Dict[str, Any]]:
        main_segments = self.flatten_to_strings(main_content, clean_text=False)
        commentary_segments = self.flatten_to_strings(comm_content, clean_text=False)

        segments, index_map = self._prepare_commentary_segments(siman_num, commentary_segments)
        used_indices: set = set()
        entries: List[Dict[str, Any]] = []
        text_index = 0

        for raw_segment in main_segments:
            if not raw_segment:
                continue
            new_entries, text_index = self._consume_main_segment(
                raw_segment,
                section,
                siman_num,
                commentary_display,
                commentary_key,
                segments,
                index_map,
                used_indices,
                text_index,
                clean_text
            )
            entries.extend(new_entries)

        unused_segments = [seg for seg in segments if seg["index"] not in used_indices]
        if unused_segments:
            logger.warning(
                "  %d commentary segments unplaced for siman %s", len(unused_segments), siman_num
            )

            for segment in unused_segments:
                entries.append({
                    "commentary": self._build_commentary_payload(
                        segment,
                        "unplaced",
                        segment["keys"][0] if segment["keys"] else None,
                        commentary_display,
                        commentary_display,
                        commentary_key,
                        section,
                        siman_num,
                        clean_text,
                        segment["keys"][0] if segment["keys"] else None
                    )
                })

        return entries

    def load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file."""
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                if content.startswith('version https://git-lfs.github.com'):
                    logger.warning(f"File is Git LFS pointer: {file_path}")
                    return None

                return json.loads(content)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def extract_simanim(self, section_data: Any) -> List[tuple]:
        """Return a list of ``(siman_number, content)`` pairs from raw section data."""

        def _from_sequence(items: List[Any]) -> List[tuple]:
            results: List[tuple] = []
            for idx, content in enumerate(items, start=1):
                results.append((idx, content))
            return results

        if section_data is None:
            return []

        if isinstance(section_data, list):
            return _from_sequence(section_data)

        if isinstance(section_data, dict):
            # Primary Tur data often sits under an empty-string key with a list value.
            if "" in section_data and isinstance(section_data[""], list):
                logger.info(
                    "  Found array under empty string key with %d simanim",
                    len(section_data[""])
                )
                return _from_sequence(section_data[""])

            simanim: List[tuple] = []
            for key, value in section_data.items():
                if value is None:
                    continue

                siman_num: Optional[int] = None

                if isinstance(key, int):
                    siman_num = key
                else:
                    # Extract a leading integer from keys like "1", "Siman 1", "1a"
                    match = re.search(r"\d+", str(key))
                    if match:
                        siman_num = int(match.group())

                if siman_num is None:
                    continue

                simanim.append((siman_num, value))

            simanim.sort(key=lambda x: x[0])
            return simanim

        return []

    def merge_section_with_commentary(
        self,
        section: str,
        commentary_name: str,
        clean_text: bool = True,
        output_format: str = "embedded"
    ) -> Optional[Dict[str, Any]]:
        """
        Merge one section with one commentary.
        Returns a simple structure with simanim containing text and commentary.
        """
        logger.info(f"\nMerging {section} with {commentary_name}")

        # Load main text
        main_file = self.base_path / self.SECTION_FILE_MAP[section]
        main_data = self.load_json(main_file)
        if not main_data:
            logger.error(f"Failed to load main text from {main_file}")
            return None

        # Extract section data
        section_data = main_data.get('text', {}).get(section)
        if not section_data:
            logger.error(f"Section '{section}' not found in main text")
            return None

        main_simanim = self.extract_simanim(section_data)
        logger.info(f"  Loaded {len(main_simanim)} simanim from main text")

        # Load commentary
        comm_info = self.COMMENTARIES[commentary_name]
        commentary_dir = self.commentary_path / comm_info["dir"] / "Hebrew"
        commentary_display = comm_info.get("display_name", commentary_name)

        # Handle inconsistent naming for Choshen Mishpat (no comma before Vilna in some files)
        if section == "Choshen Mishpat" and "{section}, Vilna" in comm_info["file"]:
            # Try without comma first
            commentary_file = commentary_dir / comm_info["file"].replace("{section}, Vilna", "{section} Vilna").format(section=section)
            if not commentary_file.exists():
                # Try with comma
                commentary_file = commentary_dir / comm_info["file"].format(section=section)
        else:
            commentary_file = commentary_dir / comm_info["file"].format(section=section)

        commentary_data = self.load_json(commentary_file)

        commentary_simanim = []
        if commentary_data:
            comm_section_data = commentary_data.get('text', {}).get(section)
            if comm_section_data:
                commentary_simanim = self.extract_simanim(comm_section_data)
                logger.info(f"  Loaded {len(commentary_simanim)} simanim from {commentary_name}")
            else:
                logger.warning(f"  Section not found in commentary")
        else:
            logger.warning(f"  Failed to load commentary from {commentary_file}")

        # Create commentary dict for quick lookup
        commentary_dict = {siman_num: content for siman_num, content in commentary_simanim}

        merged_simanim = []
        for siman_num, main_content in main_simanim:
            comm_content = commentary_dict.get(siman_num, [])

            if output_format == "embedded":
                entries = self._build_embedded_entries(
                    main_content,
                    comm_content,
                    section,
                    siman_num,
                    commentary_display,
                    commentary_name,
                    clean_text
                )

                siman_record = {
                    "siman": siman_num,
                    "entries": entries
                }

            elif output_format == "sequence":
                main_segments = self.flatten_to_strings(main_content, clean_text=clean_text)
                commentary_segments = self.flatten_to_strings(comm_content, clean_text=clean_text)

                sequence: List[Dict[str, Any]] = []

                for idx, segment in enumerate(main_segments, start=1):
                    sequence.append({
                        "type": "text",
                        "text": segment,
                        "source": {
                            "work": "Tur",
                            "section": section,
                            "siman": siman_num,
                            "category": "primary",
                            "segment_index": idx
                        }
                    })

                for idx, comment_text in enumerate(commentary_segments, start=1):
                    sequence.append({
                        "type": "commentary",
                        "commentary": comment_text,
                        "source": {
                            "work": commentary_display,
                            "section": section,
                            "siman": siman_num,
                            "category": "commentary",
                            "commentary_name": commentary_display,
                            "comment_index": idx
                        }
                    })

                siman_record = {
                    "siman": siman_num,
                    "sequence": sequence
                }

            else:
                main_segments = self.flatten_to_strings(main_content, clean_text=clean_text)
                commentary_segments = self.flatten_to_strings(comm_content, clean_text=clean_text)
                main_text = " ".join(main_segments)
                siman_record = {
                    "siman": siman_num,
                    "text": main_text,
                    "commentary": commentary_segments
                }

            merged_simanim.append(siman_record)

        metadata: Dict[str, Any] = {
            "title": f"Tur {section}",
            "section": section,
            "commentary_key": commentary_name,
            "commentary_display": commentary_display,
            "output_format": output_format,
            "sources": {
                "primary": {
                    "work": f"Tur {section}",
                    "path": str(main_file)
                },
                "commentary": {
                    "work": commentary_display,
                    "key": commentary_name,
                    "path": str(commentary_file)
                }
            }
        }

        if isinstance(main_data, dict) and "meta" in main_data:
            metadata["sources"]["primary"]["meta"] = main_data["meta"]

        if commentary_data and isinstance(commentary_data, dict) and "meta" in commentary_data:
            metadata["sources"]["commentary"]["meta"] = commentary_data["meta"]

        result = {
            "metadata": metadata,
            "total_simanim": len(merged_simanim),
            "simanim": merged_simanim
        }

        return result

    def merge_all(
        self,
        output_dir: str,
        sections: Optional[List[str]] = None,
        commentaries: Optional[List[str]] = None,
        clean_text: bool = True,
        output_format: str = "embedded"
    ):
        """Merge all sections with all commentaries, creating separate files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        sections_to_process = sections if sections else self.SECTIONS
        commentaries_to_process = commentaries if commentaries else list(self.COMMENTARIES.keys())

        for section in sections_to_process:
            for commentary in commentaries_to_process:
                try:
                    merged = self.merge_section_with_commentary(
                        section,
                        commentary,
                        clean_text,
                        output_format
                    )

                    if merged:
                        # Create filename: Tur_Orach_Chaim_Bach.json
                        section_clean = section.replace(" ", "_")
                        output_file = output_path / f"Tur_{section_clean}_{commentary}.json"

                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(merged, f, ensure_ascii=False, indent=2)

                        logger.info(f"✓ Saved: {output_file}")
                    else:
                        logger.error(f"✗ Failed to merge {section} with {commentary}")

                except Exception as e:
                    logger.error(f"✗ Error processing {section}/{commentary}: {e}")
                    import traceback
                    traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description="Merge Tur texts with commentaries (separate files per commentary)"
    )
    parser.add_argument(
        '--section',
        choices=['Orach Chaim', 'Yoreh Deah', 'Even HaEzer', 'Choshen Mishpat'],
        help='Specific section to merge (default: all)'
    )
    parser.add_argument(
        '--commentary',
        choices=['Bach', 'Beit_Yosef', 'Darkhei_Moshe', 'Drisha', 'Prisha'],
        help='Specific commentary to merge (default: all)'
    )
    parser.add_argument(
        '--output-dir',
        default='./Tur/Merged_Commentaries',
        help='Output directory (default: ./Tur/Merged_Commentaries)'
    )
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Skip text cleaning'
    )
    parser.add_argument(
        '--output-format',
        choices=['embedded', 'sequence', 'simple'],
        default='embedded',
        help='Output format for merged files (default: embedded)'
    )
    parser.add_argument(
        '--base-path',
        default=None,
        help='Base path to Tur directory (default: ./Tur)'
    )

    args = parser.parse_args()

    try:
        merger = TurCommentaryMerger(base_path=args.base_path)

        sections = [args.section] if args.section else None
        commentaries = [args.commentary] if args.commentary else None
        clean_text = not args.no_clean
        output_format = args.output_format

        logger.info("\n" + "="*60)
        logger.info("TUR COMMENTARY MERGER - SEPARATE FILES")
        logger.info("="*60 + "\n")

        merger.merge_all(
            output_dir=args.output_dir,
            sections=sections,
            commentaries=commentaries,
            clean_text=clean_text,
            output_format=output_format
        )

        logger.info("\n" + "="*60)
        logger.info("MERGE COMPLETE!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
