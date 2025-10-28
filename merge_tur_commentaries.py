#!/usr/bin/env python3
"""
Tur Commentary Merger - Merges Tur texts with commentaries and cleans text
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
import itertools
import unicodedata  # (not strictly used yet but good for future normalization)

HEBREW_LETTERS = "אבגדהוזחטיכלמנסעפצקרשת"


class TurMerger:
    """Merges Tur texts with their commentaries."""

    SECTIONS = [
        "Orach Chaim",
        "Yoreh Deah",
        "Even HaEzer",
        "Choshen Mishpat"
    ]

    # Mapping of section names to their file names
    SECTION_FILE_MAP = {
        "Orach Chaim": "Orach Chaim.json",
        "Yoreh Deah": "Yoreh Deah.json",
        "Even HaEzer": "Even HaEzer.json",
        "Choshen Mishpat": "Choshen Mishpat.json"
    }

    # Mapping of commentaries to their file name patterns
    COMMENTARY_PATTERNS = {
        "Bach": "Tur {section}.json",
        "Beit Yosef": "Tur {section}, Vilna, 1923.json",
        "Darkhei Moshe": "Tur {section}, Vilna, 1923.json",
        "Drisha": "Tur {section}, Vilna, 1923.json",
        "Prisha": "Tur {section}, Vilna, 1923.json"
    }

    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            base_path = Path.cwd() / "Tur"

        self.base_path = Path(base_path)
        logger.info(f"Base path set to: {self.base_path}")

        if not self.base_path.exists():
            logger.error(f"Base path does not exist: {self.base_path}")
            raise FileNotFoundError(f"Directory not found: {self.base_path}")

        self.commentary_path = self.base_path / "Commentary"

        if not self.commentary_path.exists():
            logger.warning(f"Commentary directory not found: {self.commentary_path}")

    def clean_text(self, text: str) -> str:
        """
        Clean text from non-formatting symbols and unwanted characters.
        Preserves Hebrew text and basic formatting.
        """
        if not isinstance(text, str):
            return text

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove excessive whitespace while preserving single spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove special control characters but keep newlines and tabs for formatting
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

        # Remove common markup artifacts (curly braces only, preserve square brackets)
        text = re.sub(r'\{[^}]*\}', '', text)  # Remove content in curly braces

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def clean_text_recursive(self, data: Any) -> Any:
        """Recursively clean text in nested structures."""
        if isinstance(data, str):
            return self.clean_text(data)
        elif isinstance(data, list):
            return [self.clean_text_recursive(item) for item in data]
        elif isinstance(data, dict):
            return {key: self.clean_text_recursive(value) for key, value in data.items()}
        else:
            return data

    def load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file (handles Git LFS files)."""
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                if content.startswith('version https://git-lfs.github.com'):
                    logger.warning(f"File is Git LFS pointer: {file_path}")
                    logger.warning("Please run 'git lfs pull' to fetch actual content")
                    return None

                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def get_main_text_path(self, section: str) -> Path:
        """Get path to main text file for a section."""
        filename = self.SECTION_FILE_MAP.get(section)
        if not filename:
            raise ValueError(f"Unknown section: {section}")
        return self.base_path / filename

    def find_commentaries_for_section(self, section: str) -> List[Dict[str, Path]]:
        """Find all commentary files for a given section."""
        commentaries = []

        if not self.commentary_path.exists():
            logger.warning(f"Commentary directory not found: {self.commentary_path}")
            return commentaries

        logger.info(f"Looking for commentaries on section: {section}")

        try:
            for commentary_name, pattern in self.COMMENTARY_PATTERNS.items():
                commentary_dir = self.commentary_path / commentary_name / "Hebrew"

                if not commentary_dir.exists():
                    logger.warning(f"Commentary directory not found: {commentary_dir}")
                    continue

                # Generate the expected filename
                filename = pattern.format(section=section)
                filepath = commentary_dir / filename

                if filepath.exists():
                    commentaries.append({
                        'name': commentary_name,
                        'path': filepath
                    })
                    logger.info(f"  Found commentary: {commentary_name}")
                else:
                    logger.debug(f"  Commentary file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error searching for commentaries: {e}")

        logger.info(f"Total commentaries found: {len(commentaries)}")
        return commentaries

    def extract_text_array(self, text_data: Any) -> Any:
        """
        Extract the actual text array from different JSON formats.

        Handles:
        1. Direct array: {"text": [[...], [...]]}
        2. Dict with empty key: {"text": {"": [[...], [...]]}}
        3. Dict with keys: {"text": {"key1": [...], "key2": [...]}}
        """
        if text_data is None:
            return []

        # If it's already a list, return it
        if isinstance(text_data, list):
            return text_data

        # If it's a dict, try to extract the array
        if isinstance(text_data, dict):
            # Try empty string key first
            if "" in text_data:
                logger.info("  Detected dict format with empty key")
                return text_data[""]

            # Try to find the first non-empty value that's a list
            for key, value in text_data.items():
                if isinstance(value, list):
                    logger.info(f"  Detected dict format with key: '{key}'")
                    return value

            logger.warning("  Dict format detected but no list found")
            return []

        return []
    def _split_siman_into_seifim(self, siman_text: str) -> List[str]:
        """
        Split a single siman string (which currently includes ALL seifim)
        into a list of seif strings.

        Strategy:
        - Look for <i data-commentator="..." data-order="N.1">
          where N = 1,2,3,... (start of a new seif).
        - We'll split on those boundaries and keep the marker text with the seif.

        If we can't detect multiple סעיפים, we just return [whole siman_text].
        """

        if not isinstance(siman_text, str):
            return [str(siman_text)]

        # Normalize newlines/whitespace a bit
        txt = siman_text.replace("\r", "\n")

        # We create an artificial delimiter before each new סעיף marker of the form data-order="N.1"
        # Example match: <i data-commentator="Bach" data-order="12.1"></i>
        # We'll look for data-order="<number>.1"
        pattern = r'(<i\s+data-commentator="[^"]+"\s+data-order="(\d+)\.1"[^>]*></i>)'

        # We want to keep the marker with the סעיף text, so we'll split but keep delimiters.
        parts = re.split(pattern, txt)

        # After re.split with a capturing group, the list looks like:
        # [pre, full_marker, "12", post, full_marker, "13", post, ...]
        # We'll reconstruct סעיפים by walking that.

        seifim: List[str] = []
        current = ""

        it = iter(parts)
        first_chunk = next(it, "")

        # If the text BEFORE the first marker has content, we keep it as סעיף 1 prefix,
        # but usually siman opens right away with marker "1.1".
        current += first_chunk

        for marker, seif_num, after_marker_text in zip(it, it, it):
            # If we already collected text for a סעיף, push it before starting a new one
            if current.strip():
                seifim.append(current.strip())

            # start new סעיף beginning with this marker + following text
            current = marker + after_marker_text

        # push last סעיף
        if current.strip():
            seifim.append(current.strip())

        # If we only got one סעיף, fallback = no real split
        if len(seifim) <= 1:
            return [txt.strip()]

        return seifim

    def extract_text_array(self, text_data: Any) -> List[List[Any]]:
        """
        Given the section-level object (e.g. main_data['text']['Orach Chaim']),
        return a list where each element is ONE siman,
        and each siman is a list of seif strings.

        Expected shape from source (per your mapping):
            {
                "Introduction": [...],
                "": [
                    [ "Siman1_Seif1", "Siman1_Seif2", ... ],  # Siman 1
                    [ "Siman2_Seif1", "Siman2_Seif2", ... ],  # Siman 2
                    ...
                ]
            }

        We will:
        - Prefer the "" key if present (that holds the simanim list you care about).
        - Otherwise, fall back to any list value.
        """

        if text_data is None:
            return []

        # Case: already the 2D array [siman][seif]
        if isinstance(text_data, list):
            return text_data

        # Case: dict like {"Introduction": [], "": [ [..],[..], ... ]}
        if isinstance(text_data, dict):
            if "" in text_data and isinstance(text_data[""], list):
                return text_data[""]
            # fallback: find first list value
            for v in text_data.values():
                if isinstance(v, list):
                    return v

        # Unknown structure
        return []
    def normalize_text_structure(self, text_data: Any) -> List[List[str]]:
        """
        Output:
            main_text[siman_idx][seif_idx] = clean string for that seif.

        Handles the actual Tur structure you showed:
        text_data -> { "Introduction": [], "": [ [ "WHOLE SIMAN 1" ], [ "WHOLE SIMAN 2" ], ... ] }

        Each siman is currently a list with one giant string that actually contains
        ALL סעיפים. We now split that string into סעיפים using _split_siman_into_seifim().
        """

        raw_simanim = self.extract_text_array(text_data)
        normalized: List[List[str]] = []

        for siman_raw in raw_simanim:
            # siman_raw should represent ONE siman.
            # In your data it's usually: [ "entire siman text with all seifim embedded" ]
            # but let's be defensive.

            if not isinstance(siman_raw, list):
                siman_candidates = [siman_raw]
            else:
                siman_candidates = siman_raw

            # Merge all pieces of this siman into one big string (in case it's split)
            # Then we'll slice it into סעיפים.
            merged_siman_text_parts: List[str] = []

            for piece in siman_candidates:
                if isinstance(piece, list):
                    # if for some reason it's nested like ["text", "more text"]
                    merged_siman_text_parts.extend(
                        [seg for seg in piece if isinstance(seg, str)]
                    )
                elif isinstance(piece, str):
                    merged_siman_text_parts.append(piece)
                else:
                    merged_siman_text_parts.append(str(piece))

            merged_siman_text = " ".join(p.strip() for p in merged_siman_text_parts if p.strip())

            # Now split this siman into סעיפים:
            seif_list = self._split_siman_into_seifim(merged_siman_text)

            # Clean whitespace
            seif_list = [s.strip() for s in seif_list if s.strip()]

            # Fallback
            if not seif_list:
                seif_list = [""]

            normalized.append(seif_list)

        return normalized
    def align_commentary_to_seifim(self, commentary_simanim: List[List[Any]]) -> List[List[str]]:
        """
        commentary_simanim is currently [siman][chunk(s)].
        Each siman may be one long block that actually covers multiple סעיפים,
        marked with the same <i data-order="N.1"> anchors.

        We will:
        - join all chunks in that siman to single string
        - split into סעיפים using _split_siman_into_seifim
        - return [siman][seif]
        """
        aligned: List[List[str]] = []

        for siman_raw in commentary_simanim:
            if not isinstance(siman_raw, list):
                siman_raw = [siman_raw]

            parts = []
            for piece in siman_raw:
                if isinstance(piece, list):
                    parts.extend([seg for seg in piece if isinstance(seg, str)])
                elif isinstance(piece, str):
                    parts.append(piece)
                else:
                    parts.append(str(piece))

            merged = " ".join(p.strip() for p in parts if isinstance(p, str) and p.strip())

            seif_list = self._split_siman_into_seifim(merged)
            seif_list = [s.strip() for s in seif_list if s.strip()]
            if not seif_list:
                seif_list = [""]

            aligned.append(seif_list)

        return aligned




    def normalize_commentary_structure(self, text_data: Any) -> List[List[List[str]]]:
        """
        Normalize commentary structure to 3D array [siman][seif][comment].

        Handles two formats:
        1. Array format: [[[comment1], [comment1, comment2]], ...]
        2. Dict format: {"1": [[comment1], [comment1, comment2]], "2": [...], ...}
        """
        # If it's a dict with numeric string keys (Tur format)
        if isinstance(text_data, dict):
            logger.info("  Detected dict format for commentary")
            # Filter out non-numeric keys
            numeric_keys = []
            for key in text_data.keys():
                try:
                    int(key)
                    numeric_keys.append(key)
                except (ValueError, TypeError):
                    pass

            # Sort by numeric value
            numeric_keys.sort(key=lambda x: int(x))
            logger.info(f"  Found {len(numeric_keys)} simanim in commentary")

            normalized = []
            for key in numeric_keys:
                siman_data = text_data[key]
                if isinstance(siman_data, list):
                    seifim = []
                    for seif_item in siman_data:
                        if isinstance(seif_item, list):
                            seifim.append(seif_item)
                        elif isinstance(seif_item, str):
                            seifim.append([seif_item])
                        else:
                            seifim.append([])
                    normalized.append(seifim)
                elif isinstance(siman_data, str):
                    normalized.append([[siman_data]])
                else:
                    normalized.append([[]])
            return normalized

        # Original logic for array format
        text_array = self.extract_text_array(text_data)

        if isinstance(text_array, list):
            normalized = []
            for siman_item in text_array:
                if isinstance(siman_item, list):
                    seifim = []
                    for seif_item in siman_item:
                        if isinstance(seif_item, list):
                            seifim.append(seif_item)
                        elif isinstance(seif_item, str):
                            seifim.append([seif_item])
                        else:
                            seifim.append([])
                    normalized.append(seifim)
                elif isinstance(siman_item, str):
                    normalized.append([[siman_item]])
                else:
                    normalized.append([[]])
            return normalized
        return []

    def merge_section(
        self,
        section: str,
        commentaries_to_include: Optional[List[str]] = None,
        output_format: str = "structured",
        clean_text: bool = True
    ) -> Dict[str, Any]:
        """Merge a section with its commentaries."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Merging section: Tur, {section}")
        logger.info(f"{'='*60}")

        main_text_path = self.get_main_text_path(section)
        logger.info(f"Loading main text from: {main_text_path}")

        main_data = self.load_json(main_text_path)

        if not main_data:
            logger.error(f"Failed to load main text for {section}")
            return {}

        # Extract text for the specific section FIRST, before any cleaning
        # Tur JSON files contain all sections in a dict: {"Orach Chaim": [...], "Yoreh Deah": [...], ...}
        text_data = main_data.get('text', [])
        if isinstance(text_data, dict) and section in text_data:
            logger.info(f"Extracting section '{section}' from multi-section file")
            text_data = text_data[section]

        main_text = self.normalize_text_structure(text_data)
        logger.info(f"Loaded {len(main_text)} simanim from main text")

        # Clean text if requested (after normalization, on the structured data)
        if clean_text:
            logger.info("Cleaning text from non-formatting symbols...")
            main_text = self.clean_text_recursive(main_text)

        if len(main_text) == 0:
            logger.error(f"No simanim found in main text! Check JSON structure.")
            logger.error(f"Text field type: {type(main_data.get('text'))}")
            if isinstance(main_data.get('text'), dict):
                logger.error(f"Text dict keys: {list(main_data.get('text', {}).keys())}")
            return {}

        available_commentaries = self.find_commentaries_for_section(section)
        commentary_data = {}

        for comm in available_commentaries:
            if commentaries_to_include and comm['name'] not in commentaries_to_include:
                logger.info(f"Skipping commentary (not in include list): {comm['name']}")
                continue

            data = self.load_json(comm['path'])
            if data and 'text' in data:
                # Extract text for the specific section FIRST (commentary files may also have multi-section format)
                comm_text_data = data['text']
                if isinstance(comm_text_data, dict) and section in comm_text_data:
                    logger.info(f"  Extracting section '{section}' from commentary")
                    comm_text_data = comm_text_data[section]

                commentary_text = self.normalize_commentary_structure(comm_text_data)
                commentary_text = self.align_commentary_to_seifim(commentary_text)


                # Clean commentary text if requested (after normalization)
                if clean_text:
                    commentary_text = self.clean_text_recursive(commentary_text)

                commentary_data[comm['name']] = {
                    'text': commentary_text
                }
                logger.info(f"Loaded commentary: {comm['name']} ({len(commentary_text)} simanim)")

        if output_format == "structured":
            merged = self._create_structured_output(
                section, main_text, commentary_data, main_data
            )
        else:
            merged = self._create_flat_output(
                section, main_text, commentary_data, main_data
            )

        return merged

    def _create_structured_output(
        self,
        section: str,
        main_text: List[List[str]],
        commentary_data: Dict[str, Dict],
        original_data: Dict
    ) -> Dict[str, Any]:
        """Create structured output with nested objects."""
        simanim = []

        for siman_idx, seifim in enumerate(main_text):
            siman_num = siman_idx + 1
            seif_list = []

            for seif_idx, seif_text in enumerate(seifim):
                seif_num = seif_idx + 1

                commentaries = {}
                for comm_name, comm_info in commentary_data.items():
                    comm_text = comm_info['text']
                    if siman_idx < len(comm_text) and seif_idx < len(comm_text[siman_idx]):
                        comments = comm_text[siman_idx][seif_idx]
                        if comments:
                            commentaries[comm_name] = {
                                'comments': comments
                            }

                seif_obj = {
                    'seif': seif_num,
                    'text': seif_text,
                    'commentaries': commentaries
                }
                seif_list.append(seif_obj)

            siman_obj = {
                'siman': siman_num,
                'seifim': seif_list
            }
            simanim.append(siman_obj)

        merged = {
            'title': f"Tur, {section}",
            'metadata': {
                'source': original_data.get('title', f"Tur, {section}"),
                'schema': original_data.get('schema', {}),
                'total_simanim': len(simanim),
                'commentaries_included': list(commentary_data.keys())
            },
            'simanim': simanim
        }

        return merged

    def _create_flat_output(
        self,
        section: str,
        main_text: List[List[str]],
        commentary_data: Dict[str, Dict],
        original_data: Dict
    ) -> Dict[str, Any]:
        """Create flat output keeping original array structure."""
        text_with_commentaries = []

        for siman_idx, seifim in enumerate(main_text):
            seif_list = []

            for seif_idx, seif_text in enumerate(seifim):
                commentaries = {}
                for comm_name, comm_info in commentary_data.items():
                    comm_text = comm_info['text']
                    if siman_idx < len(comm_text) and seif_idx < len(comm_text[siman_idx]):
                        comments = comm_text[siman_idx][seif_idx]
                        if comments:
                            commentaries[comm_name] = {
                                'comments': comments
                            }

                seif_obj = {
                    'text': seif_text,
                    'commentaries': commentaries
                }
                seif_list.append(seif_obj)

            text_with_commentaries.append(seif_list)

        merged = original_data.copy()
        merged['text'] = text_with_commentaries
        merged['commentaries_included'] = list(commentary_data.keys())

        return merged

    def merge_all_sections(
        self,
        output_dir: str,
        commentaries_to_include: Optional[List[str]] = None,
        output_format: str = "structured",
        clean_text: bool = True
    ):
        """Merge all sections and save to output directory."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for section in self.SECTIONS:
            try:
                merged = self.merge_section(
                    section,
                    commentaries_to_include,
                    output_format,
                    clean_text
                )

                if merged:
                    section_name = section.replace(" ", "_").replace("'", "")
                    output_file = output_path / f"Tur_{section_name}_merged.json"

                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(merged, f, ensure_ascii=False, indent=2)

                    logger.info(f"✓ Saved merged file: {output_file}")

                    summary_file = output_path / f"Tur_{section_name}_summary.txt"
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        f.write(f"Section: Tur, {section}\n")
                        f.write(f"Total Simanim: {len(merged.get('simanim', merged.get('text', [])))}\n")
                        f.write(f"Commentaries Included ({len(merged.get('metadata', merged).get('commentaries_included', []))}):\n")
                        for comm in merged.get('metadata', merged).get('commentaries_included', []):
                            f.write(f"  - {comm}\n")

                    logger.info(f"✓ Saved summary: {summary_file}\n")
                else:
                    logger.error(f"✗ Failed to merge section: {section}\n")

            except Exception as e:
                logger.error(f"✗ Error processing section {section}: {e}\n")
                import traceback
                traceback.print_exc()
                continue


def load_config_file(config_path: str) -> Optional[Dict]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Merge Tur texts with their commentaries"
    )
    parser.add_argument(
        '--section',
        choices=[
            'Orach Chaim',
            'Yoreh Deah',
            'Even HaEzer',
            'Choshen Mishpat',
            'all'
        ],
        default='all',
        help='Section to merge (default: all)'
    )
    parser.add_argument(
        '--output-dir',
        default='./Tur/Merged_Output',
        help='Output directory for merged files (default: ./Tur/Merged_Output)'
    )
    parser.add_argument(
        '--format',
        choices=['structured', 'flat'],
        default='structured',
        help='Output format: structured (nested objects) or flat (array with commentary fields)'
    )
    parser.add_argument(
        '--commentaries',
        nargs='*',
        help='Specific commentaries to include (default: all)'
    )
    parser.add_argument(
        '--base-path',
        default=None,
        help='Base path to Tur directory (default: ./Tur)'
    )
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Skip text cleaning (default: clean text)'
    )
    parser.add_argument(
        '--config',
        help='Path to configuration JSON file'
    )

    args = parser.parse_args()

    config = None
    if args.config:
        config = load_config_file(args.config)
        if config:
            logger.info(f"Loaded configuration from: {args.config}")

    try:
        merger = TurMerger(base_path=args.base_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("\nPlease ensure the 'Tur' directory exists.")
        logger.error("You can specify a custom path with --base-path")
        return

    commentaries_to_include = args.commentaries
    clean_text = not args.no_clean

    if args.section == 'all':
        logger.info("\n" + "="*60)
        logger.info("MERGING ALL SECTIONS")
        logger.info("="*60 + "\n")
        merger.merge_all_sections(
            output_dir=args.output_dir,
            commentaries_to_include=commentaries_to_include,
            output_format=args.format,
            clean_text=clean_text
        )
    else:
        merged = merger.merge_section(
            args.section,
            commentaries_to_include=commentaries_to_include,
            output_format=args.format,
            clean_text=clean_text
        )

        if merged:
            output_path = Path(args.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            section_name = args.section.replace(" ", "_").replace("'", "")
            output_file = output_path / f"Tur_{section_name}_merged.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ Saved merged file: {output_file}")

    logger.info("\n" + "="*60)
    logger.info("MERGE COMPLETE!")
    logger.info("="*60)


if __name__ == '__main__':
    main()
