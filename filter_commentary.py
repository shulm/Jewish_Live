#!/usr/bin/env python3
"""
Extract Single Commentary from Merged Files

Takes merged JSON files (with all commentaries) and extracts just one specific
commentary, creating new JSON files with main text + single commentary.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommentaryFilter:
    """Filter merged files to extract single commentary."""

    SECTIONS = [
        "Orach_Chayim",
        "Yoreh_Deah",
        "Even_HaEzer",
        "Choshen_Mishpat"
    ]

    def __init__(self, merged_dir: str = "./merged_output"):
        self.merged_dir = Path(merged_dir)
        
        if not self.merged_dir.exists():
            raise FileNotFoundError(f"Merged directory not found: {self.merged_dir}")
        
        logger.info(f"Merged files directory: {self.merged_dir}")

    def load_merged_file(self, section: str) -> Optional[Dict[str, Any]]:
        """Load a merged JSON file."""
        file_path = self.merged_dir / f"{section}_merged.json"
        
        try:
            logger.info(f"Loading: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def get_available_commentaries(self, data: Dict) -> List[str]:
        """Get list of commentaries in a merged file."""
        metadata = data.get('metadata', {})
        return metadata.get('commentaries_included', [])

    def extract_single_commentary(
        self,
        commentary_name: str,
        output_dir: str
    ):
        """
        Extract single commentary from all merged files.
        
        Args:
            commentary_name: Name of commentary to extract (e.g., "Ba'er Hetev")
            output_dir: Output directory for new JSON files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"\n{'='*70}")
        logger.info(f"EXTRACTING COMMENTARY: {commentary_name}")
        logger.info(f"{'='*70}\n")

        success_count = 0
        
        for section in self.SECTIONS:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {section}")
            logger.info(f"{'='*60}")
            
            # Load merged file
            data = self.load_merged_file(section)
            
            if not data:
                logger.error(f"Failed to load {section}")
                continue
            
            # Get available commentaries
            available = self.get_available_commentaries(data)
            logger.info(f"Available commentaries: {len(available)}")
            
            # Find matching commentary
            matching_commentary = None
            for comm in available:
                if commentary_name in comm:
                    matching_commentary = comm
                    break
            
            if not matching_commentary:
                logger.warning(f"Commentary '{commentary_name}' not found in {section}")
                logger.info(f"Available commentaries:")
                for comm in available:
                    logger.info(f"  - {comm}")
                continue
            
            logger.info(f"Found: {matching_commentary}")
            
            # Extract this commentary
            filtered_data = self._filter_to_single_commentary(
                data,
                matching_commentary
            )
            
            # Save filtered file
            output_file = output_path / f"{section}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Saved: {output_file}")
            
            # Create summary
            summary_file = output_path / f"{section}_summary.txt"
            self._write_summary(filtered_data, summary_file, matching_commentary)
            logger.info(f"✓ Saved summary: {summary_file}")
            
            success_count += 1

        logger.info(f"\n{'='*70}")
        logger.info(f"EXTRACTION COMPLETE!")
        logger.info(f"Successfully processed: {success_count}/{len(self.SECTIONS)} sections")
        logger.info(f"Output directory: {output_path.absolute()}")
        logger.info(f"{'='*70}\n")

    def _filter_to_single_commentary(
        self,
        data: Dict,
        commentary_name: str
    ) -> Dict[str, Any]:
        """Filter merged data to keep only one commentary."""
        filtered = {
            'title': data['title'],
            'commentary': commentary_name,
            'metadata': {
                'source': data.get('metadata', {}).get('source', ''),
                'total_simanim': data.get('metadata', {}).get('total_simanim', 0),
                'commentary_included': commentary_name
            },
            'simanim': []
        }
        
        # Process each siman
        for siman_obj in data.get('simanim', []):
            filtered_siman = {
                'siman': siman_obj['siman'],
                'seifim': []
            }
            
            # Process each seif
            for seif_obj in siman_obj.get('seifim', []):
                filtered_seif = {
                    'seif': seif_obj['seif'],
                    'text': seif_obj['text']
                }
                
                # Add commentary if it exists for this seif
                commentaries = seif_obj.get('commentaries', {})
                if commentary_name in commentaries:
                    filtered_seif['commentary'] = commentaries[commentary_name]
                
                filtered_siman['seifim'].append(filtered_seif)
            
            filtered['simanim'].append(filtered_siman)
        
        return filtered

    def _write_summary(self, data: Dict, summary_file: Path, commentary_name: str):
        """Write summary file."""
        total_simanim = len(data.get('simanim', []))
        total_seifim = sum(len(s['seifim']) for s in data.get('simanim', []))
        
        seifim_with_commentary = sum(
            1 for siman in data.get('simanim', [])
            for seif in siman['seifim']
            if 'commentary' in seif
        )
        
        total_comments = sum(
            len(seif.get('commentary', {}).get('comments', []))
            for siman in data.get('simanim', [])
            for seif in siman['seifim']
            if 'commentary' in seif
        )
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Section: {data['title']}\n")
            f.write(f"Commentary: {commentary_name}\n")
            f.write(f"\n")
            f.write(f"Total Simanim: {total_simanim}\n")
            f.write(f"Total Se'ifim: {total_seifim}\n")
            f.write(f"Se'ifim with commentary: {seifim_with_commentary}\n")
            f.write(f"Total comments: {total_comments}\n")
            
            # Calculate coverage
            if total_seifim > 0:
                coverage = (seifim_with_commentary / total_seifim) * 100
                f.write(f"Coverage: {coverage:.1f}%\n")

    def list_commentaries_in_merged_files(self):
        """List all commentaries available in merged files."""
        print("\n" + "="*70)
        print("AVAILABLE COMMENTARIES IN MERGED FILES")
        print("="*70)
        
        all_commentaries = set()
        
        for section in self.SECTIONS:
            data = self.load_merged_file(section)
            if data:
                available = self.get_available_commentaries(data)
                print(f"\n{section}:")
                print(f"  Total commentaries: {len(available)}")
                for comm in available:
                    all_commentaries.add(comm)
                    # Extract base name for display
                    base_name = comm.split(" on ")[0]
                    print(f"  - {base_name}")
        
        print("\n" + "="*70)
        print("UNIQUE COMMENTARY NAMES (use these for extraction):")
        print("="*70)
        
        unique_bases = set()
        for comm in sorted(all_commentaries):
            base = comm.split(" on ")[0]
            unique_bases.add(base)
        
        for base in sorted(unique_bases):
            print(f"  - {base}")
        
        print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract single commentary from merged Shulchan Arukh files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract Ba'er Hetev from merged files
  python filter_commentary.py --commentary "Ba'er Hetev"
  
  # Extract Mishnah Berurah
  python filter_commentary.py --commentary "Mishnah Berurah"
  
  # List available commentaries
  python filter_commentary.py --list
  
  # Custom directories
  python filter_commentary.py --commentary "Ba'er Hetev" --merged-dir "./merged_output" --output-dir "./BaerHetev"
        """
    )
    parser.add_argument(
        '--commentary',
        help='Commentary name to extract (e.g., "Ba\'er Hetev", "Mishnah Berurah")'
    )
    parser.add_argument(
        '--merged-dir',
        default='./merged_output',
        help='Directory with merged JSON files (default: ./merged_output)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory (default: ./commentary_NAME)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available commentaries in merged files'
    )

    args = parser.parse_args()

    try:
        filter_obj = CommentaryFilter(merged_dir=args.merged_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Please ensure you have run merge_commentaries.py first")
        return

    if args.list:
        filter_obj.list_commentaries_in_merged_files()
        return

    if not args.commentary:
        logger.error("Please specify a commentary name with --commentary")
        logger.info("Use --list to see available commentaries")
        return

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        safe_name = args.commentary.replace("'", "").replace(" ", "_")
        output_dir = f"./commentary_{safe_name}"

    # Extract the commentary
    filter_obj.extract_single_commentary(
        commentary_name=args.commentary,
        output_dir=output_dir
    )


if __name__ == '__main__':
    main()
