#!/usr/bin/env python3
"""
Tur Commentary Merger - Creates separate JSON files for each commentary

This script merges Tur texts with their commentaries, creating a separate
output file for each commentary. Structure is simple: siman-based only.
"""

import json
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

    def get_simanim_from_dict(self, data_dict: Dict) -> List[tuple]:
        """
        Extract simanim from dict structure, returning list of (siman_num, content).

        Handles two formats:
        1. Numeric keys: {"1": [...], "2": [...], ...}
        2. Empty string key with array: {"": [[...], [...], ...]}
        """
        if not isinstance(data_dict, dict):
            return []

        # Check if there's an empty string key with an array (Tur format)
        if "" in data_dict and isinstance(data_dict[""], list):
            logger.info(f"  Found array under empty string key with {len(data_dict[''])} simanim")
            simanim = []
            for i, content in enumerate(data_dict[""]):
                siman_num = i + 1  # Array index 0 = siman 1
                simanim.append((siman_num, content))
            return simanim

        # Otherwise try numeric string keys
        simanim = []
        for key, value in data_dict.items():
            try:
                siman_num = int(key)
                simanim.append((siman_num, value))
            except (ValueError, TypeError):
                # Skip non-numeric keys like "Introduction"
                pass

        # Sort by siman number
        simanim.sort(key=lambda x: x[0])
        return simanim

    def merge_section_with_commentary(
        self,
        section: str,
        commentary_name: str,
        clean_text: bool = True,
        output_format: str = "sequence"
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

        main_simanim = self.get_simanim_from_dict(section_data)
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
                commentary_simanim = self.get_simanim_from_dict(comm_section_data)
                logger.info(f"  Loaded {len(commentary_simanim)} simanim from {commentary_name}")
            else:
                logger.warning(f"  Section not found in commentary")
        else:
            logger.warning(f"  Failed to load commentary from {commentary_file}")

        # Create commentary dict for quick lookup
        commentary_dict = {siman_num: content for siman_num, content in commentary_simanim}

        # Merge
        merged_simanim = []
        for siman_num, main_content in main_simanim:
            main_segments = self.flatten_to_strings(main_content, clean_text=clean_text)
            main_text = " ".join(main_segments)

            comm_content = commentary_dict.get(siman_num, [])
            commentary_segments = self.flatten_to_strings(comm_content, clean_text=clean_text)

            if output_format == "sequence":
                sequence: List[Dict[str, Any]] = []

                sequence.append({
                    "type": "text",
                    "content": main_text,
                    "source": {
                        "work": "Tur",
                        "section": section,
                        "siman": siman_num,
                        "category": "primary"
                    }
                })

                for idx, comment_text in enumerate(commentary_segments, start=1):
                    sequence.append({
                        "type": "commentary",
                        "name": commentary_display,
                        "content": comment_text,
                        "source": {
                            "work": commentary_display,
                            "section": section,
                            "siman": siman_num,
                            "category": "commentary",
                            "comment_index": idx
                        }
                    })

                siman_record: Dict[str, Any] = {
                    "siman": siman_num,
                    "entries": sequence
                }
            else:
                siman_record = {
                    "siman": siman_num,
                    "text": main_text,
                    "commentary": commentary_segments
                }

            merged_simanim.append(siman_record)

        result = {
            "title": f"Tur {section}",
            "commentary": commentary_name,
            "commentary_display": commentary_display,
            "total_simanim": len(merged_simanim),
            "output_format": output_format,
            "simanim": merged_simanim
        }

        return result

    def merge_all(
        self,
        output_dir: str,
        sections: Optional[List[str]] = None,
        commentaries: Optional[List[str]] = None,
        clean_text: bool = True,
        output_format: str = "sequence"
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
        choices=['sequence', 'simple'],
        default='sequence',
        help='Output format for merged files (default: sequence)'
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
