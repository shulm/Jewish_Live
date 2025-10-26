#!/usr/bin/env python3
"""
Shulchan Arukh Commentary Merger

This script merges Shulchan Arukh texts with their commentaries,
storing each commentary as a separate JSON field for flexible
selection and removal in the future.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShulchanArukhMerger:
    """Merges Shulchan Arukh texts with their commentaries."""

    SECTIONS = [
        "Shulchan Arukh, Orach Chayim",
        "Shulchan Arukh, Yoreh De'ah",
        "Shulchan Arukh, Choshen Mishpat",
        "Shulchan Arukh, Even HaEzer"
    ]

    def __init__(self, base_path: str = "/home/user/Jewish_Live/Shulchan Arukh"):
        self.base_path = Path(base_path)
        self.commentary_path = self.base_path / "Commentary"

    def load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file (handles Git LFS files)."""
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Check if it's a Git LFS pointer
                if content.startswith('version https://git-lfs.github.com'):
                    logger.warning(f"File is Git LFS pointer: {file_path}")
                    logger.warning("Please run 'git lfs pull' to fetch actual content")
                    return None

                return json.loads(content)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def get_main_text_path(self, section: str) -> Path:
        """Get path to main text file for a section."""
        return self.base_path / section / "Hebrew" / "merged.json"

    def find_commentaries_for_section(self, section: str) -> List[Dict[str, Path]]:
        """Find all commentary files for a given section."""
        commentaries = []

        if not self.commentary_path.exists():
            logger.warning(f"Commentary directory not found: {self.commentary_path}")
            return commentaries

        # Search through all commentary directories
        for author_dir in self.commentary_path.iterdir():
            if not author_dir.is_dir():
                continue

            for commentary_dir in author_dir.iterdir():
                if not commentary_dir.is_dir():
                    continue

                # Check if this commentary is for the current section
                commentary_name = commentary_dir.name
                if section.split(", ")[-1] in commentary_name:
                    merged_file = commentary_dir / "Hebrew" / "merged.json"
                    if merged_file.exists():
                        commentaries.append({
                            'name': commentary_name,
                            'author': author_dir.name,
                            'path': merged_file
                        })
                        logger.info(f"Found commentary: {commentary_name}")

        return commentaries

    def normalize_text_structure(self, text_data: Any) -> List[List[str]]:
        """Normalize text structure to 2D array [siman][seif]."""
        if isinstance(text_data, list):
            # Ensure it's a 2D array
            normalized = []
            for item in text_data:
                if isinstance(item, list):
                    normalized.append(item)
                elif isinstance(item, str):
                    normalized.append([item])
                else:
                    normalized.append([])
            return normalized
        return []

    def normalize_commentary_structure(self, text_data: Any) -> List[List[List[str]]]:
        """Normalize commentary structure to 3D array [siman][seif][comment]."""
        if isinstance(text_data, list):
            normalized = []
            for siman_item in text_data:
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
        output_format: str = "structured"
    ) -> Dict[str, Any]:
        """
        Merge a section with its commentaries.

        Args:
            section: Section name (e.g., "Shulchan Arukh, Orach Chayim")
            commentaries_to_include: List of commentary names to include (None = all)
            output_format: "structured" or "flat"
                - structured: Nested structure with siman/seif objects
                - flat: Keep original array structure but add commentary fields

        Returns:
            Merged JSON structure
        """
        logger.info(f"Merging section: {section}")

        # Load main text
        main_text_path = self.get_main_text_path(section)
        main_data = self.load_json(main_text_path)

        if not main_data:
            logger.error(f"Failed to load main text for {section}")
            return {}

        # Extract text array
        main_text = self.normalize_text_structure(main_data.get('text', []))
        logger.info(f"Loaded {len(main_text)} simanim from main text")

        # Find and load commentaries
        available_commentaries = self.find_commentaries_for_section(section)
        commentary_data = {}

        for comm in available_commentaries:
            if commentaries_to_include and comm['name'] not in commentaries_to_include:
                continue

            data = self.load_json(comm['path'])
            if data and 'text' in data:
                commentary_text = self.normalize_commentary_structure(data['text'])
                commentary_data[comm['name']] = {
                    'author': comm['author'],
                    'text': commentary_text
                }
                logger.info(f"Loaded commentary: {comm['name']} ({len(commentary_text)} simanim)")

        # Create merged structure
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

                # Collect commentaries for this seif
                commentaries = {}
                for comm_name, comm_info in commentary_data.items():
                    comm_text = comm_info['text']
                    if siman_idx < len(comm_text) and seif_idx < len(comm_text[siman_idx]):
                        comments = comm_text[siman_idx][seif_idx]
                        if comments:  # Only include if not empty
                            commentaries[comm_name] = {
                                'author': comm_info['author'],
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

        # Build final structure
        merged = {
            'title': section,
            'metadata': {
                'source': original_data.get('title', section),
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
                # Collect commentaries for this seif
                commentaries = {}
                for comm_name, comm_info in commentary_data.items():
                    comm_text = comm_info['text']
                    if siman_idx < len(comm_text) and seif_idx < len(comm_text[siman_idx]):
                        comments = comm_text[siman_idx][seif_idx]
                        if comments:
                            commentaries[comm_name] = {
                                'author': comm_info['author'],
                                'comments': comments
                            }

                seif_obj = {
                    'text': seif_text,
                    'commentaries': commentaries
                }
                seif_list.append(seif_obj)

            text_with_commentaries.append(seif_list)

        # Build final structure
        merged = original_data.copy()
        merged['text'] = text_with_commentaries
        merged['commentaries_included'] = list(commentary_data.keys())

        return merged

    def merge_all_sections(
        self,
        output_dir: str,
        commentaries_to_include: Optional[List[str]] = None,
        output_format: str = "structured"
    ):
        """Merge all sections and save to output directory."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for section in self.SECTIONS:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {section}")
            logger.info(f"{'='*60}")

            merged = self.merge_section(section, commentaries_to_include, output_format)

            if merged:
                # Create output filename
                section_name = section.replace("Shulchan Arukh, ", "").replace(" ", "_")
                output_file = output_path / f"{section_name}_merged.json"

                # Save merged data
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(merged, f, ensure_ascii=False, indent=2)

                logger.info(f"Saved merged file: {output_file}")

                # Save summary
                summary_file = output_path / f"{section_name}_summary.txt"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(f"Section: {section}\n")
                    f.write(f"Total Simanim: {len(merged.get('simanim', merged.get('text', [])))}\n")
                    f.write(f"Commentaries Included:\n")
                    for comm in merged.get('metadata', merged).get('commentaries_included', []):
                        f.write(f"  - {comm}\n")

                logger.info(f"Saved summary: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Merge Shulchan Arukh texts with their commentaries"
    )
    parser.add_argument(
        '--section',
        choices=[
            'Orach Chayim',
            'Yoreh De\'ah',
            'Choshen Mishpat',
            'Even HaEzer',
            'all'
        ],
        default='all',
        help='Section to merge (default: all)'
    )
    parser.add_argument(
        '--output-dir',
        default='./merged_output',
        help='Output directory for merged files (default: ./merged_output)'
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
        default='/home/user/Jewish_Live/Shulchan Arukh',
        help='Base path to Shulchan Arukh directory'
    )

    args = parser.parse_args()

    # Create merger instance
    merger = ShulchanArukhMerger(base_path=args.base_path)

    # Merge sections
    if args.section == 'all':
        merger.merge_all_sections(
            output_dir=args.output_dir,
            commentaries_to_include=args.commentaries,
            output_format=args.format
        )
    else:
        section = f"Shulchan Arukh, {args.section}"
        merged = merger.merge_section(
            section,
            commentaries_to_include=args.commentaries,
            output_format=args.format
        )

        if merged:
            output_path = Path(args.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            section_name = args.section.replace(" ", "_").replace("'", "")
            output_file = output_path / f"{section_name}_merged.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved merged file: {output_file}")

    logger.info("\nMerge complete!")


if __name__ == '__main__':
    main()
