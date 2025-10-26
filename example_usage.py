#!/usr/bin/env python3
"""
Example usage of merged Shulchan Arukh data with commentaries.

This script demonstrates how to:
1. Load merged JSON files
2. Access specific Siman and Se'if
3. Filter commentaries
4. Display text with selected commentaries
"""

import json
from pathlib import Path
from typing import List, Optional


def load_merged_file(section: str, base_dir: str = "./merged_output") -> dict:
    """Load a merged JSON file for a specific section."""
    section_name = section.replace(" ", "_").replace("'", "")
    file_path = Path(base_dir) / f"{section_name}_merged.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Merged file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_seif(data: dict, siman: int, seif: int) -> Optional[dict]:
    """Get a specific Se'if from the merged data (structured format)."""
    if siman < 1 or siman > len(data.get('simanim', [])):
        return None

    siman_obj = data['simanim'][siman - 1]
    seifim = siman_obj.get('seifim', [])

    if seif < 1 or seif > len(seifim):
        return None

    return seifim[seif - 1]


def display_seif_with_commentaries(
    data: dict,
    siman: int,
    seif: int,
    commentaries: Optional[List[str]] = None,
    show_all: bool = False
):
    """
    Display a Se'if with its commentaries.

    Args:
        data: Merged data dictionary
        siman: Siman number (1-based)
        seif: Se'if number (1-based)
        commentaries: List of commentary names to show (None = all)
        show_all: If True, show all commentaries regardless of commentaries param
    """
    seif_obj = get_seif(data, siman, seif)

    if not seif_obj:
        print(f"Siman {siman}, Se'if {seif} not found")
        return

    # Print header
    print("=" * 80)
    print(f"Siman {siman}, Se'if {seif}")
    print("=" * 80)

    # Print main text
    print(f"\n[Main Text]")
    print(seif_obj['text'])
    print()

    # Print commentaries
    available_commentaries = seif_obj.get('commentaries', {})

    if not available_commentaries:
        print("[No commentaries available for this Se'if]")
        return

    # Determine which commentaries to display
    if show_all or commentaries is None:
        display_commentaries = available_commentaries.keys()
    else:
        display_commentaries = [c for c in commentaries if c in available_commentaries]

    if not display_commentaries:
        print(f"[None of the requested commentaries are available for this Se'if]")
        return

    # Display each commentary
    for comm_name in display_commentaries:
        comm_obj = available_commentaries[comm_name]
        author = comm_obj.get('author', 'Unknown')
        comments = comm_obj.get('comments', [])

        print(f"\n[{comm_name}]")
        print(f"Author: {author}")
        print("-" * 80)

        for i, comment in enumerate(comments, 1):
            print(f"{i}. {comment}")
            print()


def list_available_commentaries(data: dict) -> List[str]:
    """Get list of all commentaries included in the merged data."""
    metadata = data.get('metadata', {})
    return metadata.get('commentaries_included', [])


def find_seifim_with_commentary(data: dict, commentary_name: str) -> List[tuple]:
    """
    Find all Siman/Se'if combinations that have a specific commentary.

    Returns:
        List of (siman, seif) tuples
    """
    results = []

    for siman_obj in data.get('simanim', []):
        siman_num = siman_obj['siman']
        for seif_obj in siman_obj['seifim']:
            seif_num = seif_obj['seif']
            if commentary_name in seif_obj.get('commentaries', {}):
                results.append((siman_num, seif_num))

    return results


def create_commentary_subset(
    data: dict,
    include_commentaries: List[str],
    output_file: str
):
    """
    Create a new merged file with only specified commentaries.

    Args:
        data: Original merged data
        include_commentaries: List of commentary names to keep
        output_file: Path to save the new file
    """
    # Deep copy to avoid modifying original
    import copy
    new_data = copy.deepcopy(data)

    # Update metadata
    if 'metadata' in new_data:
        new_data['metadata']['commentaries_included'] = include_commentaries

    # Filter commentaries from each seif
    for siman_obj in new_data.get('simanim', []):
        for seif_obj in siman_obj['seifim']:
            commentaries = seif_obj.get('commentaries', {})
            # Keep only specified commentaries
            filtered_commentaries = {
                k: v for k, v in commentaries.items()
                if k in include_commentaries
            }
            seif_obj['commentaries'] = filtered_commentaries

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"Created commentary subset: {output_file}")


def get_statistics(data: dict):
    """Print statistics about the merged data."""
    simanim = data.get('simanim', [])
    total_simanim = len(simanim)
    total_seifim = sum(len(s['seifim']) for s in simanim)

    commentaries = list_available_commentaries(data)

    # Count seifim with commentaries
    seifim_with_commentaries = 0
    total_commentary_instances = 0

    for siman_obj in simanim:
        for seif_obj in siman_obj['seifim']:
            comm_count = len(seif_obj.get('commentaries', {}))
            if comm_count > 0:
                seifim_with_commentaries += 1
                total_commentary_instances += comm_count

    print(f"\n{'='*60}")
    print(f"Statistics for: {data.get('title', 'Unknown')}")
    print(f"{'='*60}")
    print(f"Total Simanim: {total_simanim}")
    print(f"Total Se'ifim: {total_seifim}")
    print(f"Se'ifim with commentaries: {seifim_with_commentaries}")
    print(f"Total commentary instances: {total_commentary_instances}")
    print(f"\nAvailable commentaries ({len(commentaries)}):")
    for comm in commentaries:
        print(f"  - {comm}")
    print(f"{'='*60}\n")


def main():
    """Example usage demonstrations."""
    import sys

    # Example 1: Load and display basic info
    print("Example 1: Loading merged data and displaying statistics")
    print("-" * 80)

    try:
        # Try to load Orach Chayim
        data = load_merged_file("Orach_Chayim")
        get_statistics(data)

        # Example 2: Display a specific Se'if with all commentaries
        print("\n\nExample 2: Display Siman 1, Se'if 1 with all commentaries")
        print("-" * 80)
        display_seif_with_commentaries(data, siman=1, seif=1, show_all=True)

        # Example 3: Display with specific commentaries only
        print("\n\nExample 3: Display with specific commentaries only")
        print("-" * 80)
        specific_commentaries = [
            "Mishnah Berurah on Shulchan Arukh, Orach Chayim",
            "Magen Avraham on Shulchan Arukh, Orach Chayim"
        ]
        display_seif_with_commentaries(
            data, siman=1, seif=1,
            commentaries=specific_commentaries
        )

        # Example 4: Find where a specific commentary appears
        print("\n\nExample 4: Find Siman/Se'if with specific commentary")
        print("-" * 80)
        commentary_to_find = "Mishnah Berurah on Shulchan Arukh, Orach Chayim"
        locations = find_seifim_with_commentary(data, commentary_to_find)
        print(f"Found '{commentary_to_find}' in {len(locations)} locations")
        print(f"First 10 locations: {locations[:10]}")

        # Example 5: Create a subset with only essential commentaries
        print("\n\nExample 5: Creating commentary subset")
        print("-" * 80)
        essential_commentaries = [
            "Mishnah Berurah on Shulchan Arukh, Orach Chayim",
            "Beur HaGra on Shulchan Arukh, Orach Chayim"
        ]
        create_commentary_subset(
            data,
            essential_commentaries,
            "merged_output/Orach_Chayim_essential.json"
        )

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease run merge_commentaries.py first to create merged files:")
        print("  python merge_commentaries.py --section all")
        sys.exit(1)


if __name__ == '__main__':
    main()
