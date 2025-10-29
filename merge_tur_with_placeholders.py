#!/usr/bin/env python3
"""
Tur Commentary Merger with Placeholder-based Insertion

This script merges Tur texts with their commentaries by parsing placeholder tags
in the main text and inserting commentary at those specific positions.

Placeholders in main text look like: <i data-commentator="Bach" data-order="1.1"></i>
The script extracts these and matches them with commentary entries.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse
import logging
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TurPlaceholderMerger:
    """Merges Tur texts with commentaries using placeholder-based insertion."""

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

    def clean_text(self, text: str, remove_placeholders: bool = True) -> str:
        """Clean text from HTML tags and excessive whitespace."""
        if not isinstance(text, str):
            return text

        # Remove placeholder tags if requested
        if remove_placeholders:
            text = re.sub(r'<i\s+data-commentator="[^"]*"\s+data-order="[^"]*"[^>]*></i>', '', text)

        # Remove other HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def extract_placeholders(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract placeholder information from text.
        Returns list of (commentator, order) tuples.
        """
        pattern = r'<i\s+data-commentator="([^"]*)"\s+data-order="([^"]*)"[^>]*></i>'
        matches = re.findall(pattern, text)
        return matches

    def split_text_by_placeholders(self, text: str, commentary_name: str) -> List[Dict[str, Any]]:
        """
        Split text into segments based on placeholders for a specific commentary.
        Returns list of dictionaries with 'type' (text/placeholder) and 'content'/'order'.
        """
        pattern = r'(<i\s+data-commentator="([^"]*)"\s+data-order="([^"]*)"[^>]*></i>)'

        segments = []
        last_end = 0

        for match in re.finditer(pattern, text):
            # Add text before placeholder
            if match.start() > last_end:
                text_segment = text[last_end:match.start()].strip()
                if text_segment:
                    segments.append({
                        'type': 'text',
                        'content': self.clean_text(text_segment, remove_placeholders=False)
                    })

            # Add placeholder info if it matches our commentary
            commentator = match.group(2)
            order = match.group(3)

            if commentator == commentary_name or commentator == self.COMMENTARIES.get(commentary_name, {}).get('display_name'):
                segments.append({
                    'type': 'placeholder',
                    'commentator': commentator,
                    'order': order
                })

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            text_segment = text[last_end:].strip()
            if text_segment:
                segments.append({
                    'type': 'text',
                    'content': self.clean_text(text_segment, remove_placeholders=False)
                })

        return segments

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

    def flatten_to_strings(self, data: Any, clean_text: bool = True) -> List[str]:
        """Flatten nested lists/dicts into a list of strings."""
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
                # Handle special keys like 'paragraphs'
                if 'paragraphs' in item:
                    _recurse(item['paragraphs'])
                else:
                    for value in item.values():
                        _recurse(value)
                return

            text = self.clean_text(str(item)) if clean_text else str(item)
            text = text.strip()
            if text:
                flattened.append(text)

        _recurse(data)
        return flattened

    def extract_simanim(self, section_data: Any) -> List[Tuple[int, Any]]:
        """Return a list of (siman_number, content) pairs from raw section data."""

        if section_data is None:
            return []

        # Handle list format
        if isinstance(section_data, list):
            results = []
            for idx, content in enumerate(section_data, start=1):
                results.append((idx, content))
            return results

        # Handle dict format
        if isinstance(section_data, dict):
            # Check for empty-string key with list value
            if "" in section_data and isinstance(section_data[""], list):
                logger.info(f"  Found array under empty string key with {len(section_data[''])} simanim")
                return [(idx, content) for idx, content in enumerate(section_data[""], start=1)]

            # Extract from numbered keys
            simanim = []
            for key, value in section_data.items():
                if value is None:
                    continue

                siman_num = None

                # Try to parse as integer
                if isinstance(key, int):
                    siman_num = key
                else:
                    # Extract leading integer from keys like "1", "Siman 1", "1a"
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
        clean_text: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Merge one section with one commentary using placeholder-based insertion.
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

        # Handle inconsistent naming for Choshen Mishpat
        if section == "Choshen Mishpat" and "{section}, Vilna" in comm_info["file"]:
            commentary_file = commentary_dir / comm_info["file"].replace("{section}, Vilna", "{section} Vilna").format(section=section)
            if not commentary_file.exists():
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

        # Merge simanim
        merged_simanim = []

        for siman_num, main_content in main_simanim:
            # Get commentary for this siman
            comm_content = commentary_dict.get(siman_num, [])
            commentary_segments = self.flatten_to_strings(comm_content, clean_text=clean_text)

            # Convert main content to strings to analyze
            main_strings = self.flatten_to_strings(main_content, clean_text=False)
            combined_text = " ".join(main_strings)

            # Check if there are placeholders for this commentary
            placeholders = self.extract_placeholders(combined_text)
            relevant_placeholders = [
                (c, o) for c, o in placeholders
                if c == commentary_display or c == commentary_name
            ]

            entries = []

            if relevant_placeholders:
                # Parse by placeholders and insert commentary
                segments = self.split_text_by_placeholders(combined_text, commentary_display)

                # Create a mapping of order to commentary text
                order_to_comment = {}
                for idx, comment in enumerate(commentary_segments):
                    # Try to match order like "1.1", "1.2", etc.
                    order_key = f"{siman_num}.{idx + 1}"
                    order_to_comment[order_key] = comment

                segment_index = 0
                comment_index = 0

                for seg in segments:
                    if seg['type'] == 'text':
                        segment_index += 1
                        entries.append({
                            "text": {
                                "content": seg['content'],
                                "source": {
                                    "work": "Tur",
                                    "section": section,
                                    "siman": siman_num,
                                    "category": "primary",
                                    "segment_index": segment_index
                                }
                            }
                        })
                    elif seg['type'] == 'placeholder':
                        # Insert commentary at placeholder
                        order = seg['order']
                        comment_text = order_to_comment.get(order, "")

                        if not comment_text and comment_index < len(commentary_segments):
                            # Fallback to sequential commentary if order doesn't match
                            comment_text = commentary_segments[comment_index]

                        if comment_text:
                            comment_index += 1
                            entries.append({
                                "commentary": {
                                    "content": comment_text,
                                    "source": {
                                        "work": commentary_display,
                                        "section": section,
                                        "siman": siman_num,
                                        "category": "commentary",
                                        "commentary_name": commentary_display,
                                        "order": order,
                                        "comment_index": comment_index
                                    }
                                }
                            })
            else:
                # No placeholders, just add text and then all commentary
                clean_combined = self.clean_text(combined_text)
                if clean_combined:
                    entries.append({
                        "text": {
                            "content": clean_combined,
                            "source": {
                                "work": "Tur",
                                "section": section,
                                "siman": siman_num,
                                "category": "primary"
                            }
                        }
                    })

                # Add all commentary entries
                for idx, comment_text in enumerate(commentary_segments, start=1):
                    entries.append({
                        "commentary": {
                            "content": comment_text,
                            "source": {
                                "work": commentary_display,
                                "section": section,
                                "siman": siman_num,
                                "category": "commentary",
                                "commentary_name": commentary_display,
                                "comment_index": idx
                            }
                        }
                    })

            if entries:
                merged_simanim.append({
                    "siman": siman_num,
                    "entries": entries
                })

        result = {
            "title": f"Tur {section}",
            "commentary": commentary_name,
            "commentary_display": commentary_display,
            "total_simanim": len(merged_simanim),
            "source": {
                "main_text": {
                    "work": "Tur",
                    "section": section,
                    "file": self.SECTION_FILE_MAP[section]
                },
                "commentary": {
                    "work": commentary_display,
                    "internal_name": commentary_name,
                    "section": section,
                    "file": comm_info["file"].format(section=section)
                }
            },
            "simanim": merged_simanim
        }

        return result

    def merge_all(
        self,
        output_dir: str,
        sections: Optional[List[str]] = None,
        commentaries: Optional[List[str]] = None,
        clean_text: bool = True
    ):
        """Merge all sections with all commentaries, creating separate files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        sections_to_process = sections if sections else self.SECTIONS
        commentaries_to_process = commentaries if commentaries else list(self.COMMENTARIES.keys())

        success_count = 0
        fail_count = 0

        for section in sections_to_process:
            for commentary in commentaries_to_process:
                try:
                    merged = self.merge_section_with_commentary(
                        section,
                        commentary,
                        clean_text
                    )

                    if merged:
                        # Create filename: Tur_Orach_Chaim_Bach.json
                        section_clean = section.replace(" ", "_")
                        output_file = output_path / f"Tur_{section_clean}_{commentary}.json"

                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(merged, f, ensure_ascii=False, indent=2)

                        logger.info(f"✓ Saved: {output_file}")
                        success_count += 1
                    else:
                        logger.error(f"✗ Failed to merge {section} with {commentary}")
                        fail_count += 1

                except Exception as e:
                    logger.error(f"✗ Error processing {section}/{commentary}: {e}")
                    fail_count += 1
                    import traceback
                    traceback.print_exc()

        logger.info(f"\nCompleted: {success_count} successful, {fail_count} failed")


def main():
    parser = argparse.ArgumentParser(
        description="Merge Tur texts with commentaries using placeholder-based insertion"
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
        '--base-path',
        default=None,
        help='Base path to Tur directory (default: ./Tur)'
    )

    args = parser.parse_args()

    try:
        merger = TurPlaceholderMerger(base_path=args.base_path)

        sections = [args.section] if args.section else None
        commentaries = [args.commentary] if args.commentary else None
        clean_text = not args.no_clean

        logger.info("\n" + "="*60)
        logger.info("TUR COMMENTARY MERGER - PLACEHOLDER-BASED INSERTION")
        logger.info("="*60 + "\n")

        merger.merge_all(
            output_dir=args.output_dir,
            sections=sections,
            commentaries=commentaries,
            clean_text=clean_text
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
