# Tur Commentary Merger

This script merges Tur texts with their commentaries, similar to the Shulchan Arukh merger. It also cleans text from non-formatting symbols.

## Features

- Merges 4 main Tur sections with their commentaries:
  - Orach Chaim
  - Yoreh Deah
  - Even HaEzer
  - Choshen Mishpat

- Supports 5 commentaries:
  - Bach
  - Beit Yosef
  - Darkhei Moshe
  - Drisha
  - Prisha

- Text cleaning: Removes HTML tags, excessive whitespace, and non-formatting symbols
- Two output formats: structured (nested objects) or flat (array-based)

## Prerequisites

The Tur JSON files are stored in Git LFS. Before running the merger, you need to fetch the actual files:

```bash
# Install Git LFS (if not already installed)
# On Ubuntu/Debian:
sudo apt-get install git-lfs

# On macOS:
brew install git-lfs

# Initialize Git LFS
git lfs install

# Pull the actual files from LFS
git lfs pull
```

## Directory Structure

```
Tur/
├── Orach Chaim.json        # Contains all 4 sections
├── Yoreh Deah.json         # Contains all 4 sections
├── Even HaEzer.json        # Contains all 4 sections
├── Choshen Mishpat.json    # Contains all 4 sections
└── Commentary/
    ├── Bach/Hebrew/
    ├── Beit Yosef/Hebrew/
    ├── Darkhei Moshe/Hebrew/
    ├── Drisha/Hebrew/
    └── Prisha/Hebrew/
```

**Note:** Each Tur JSON file contains ALL four sections in a nested dictionary format:
```json
{
  "text": {
    "Orach Chaim": [[...], [...]],
    "Yoreh Deah": [[...], [...]],
    "Even HaEzer": [[...], [...]],
    "Choshen Mishpat": [[...], [...]]
  }
}
```

The script automatically extracts the correct section from each file.

## Usage

### Merge All Sections

```bash
python3 merge_tur_commentaries.py
```

This will merge all 4 sections with all available commentaries and save them to `./Tur/Merged_Output/`

### Merge Specific Section

```bash
python3 merge_tur_commentaries.py --section "Orach Chaim"
```

### Specify Output Directory

```bash
python3 merge_tur_commentaries.py --output-dir ./custom_output
```

### Include Specific Commentaries Only

```bash
python3 merge_tur_commentaries.py --commentaries "Bach" "Beit Yosef"
```

### Disable Text Cleaning

```bash
python3 merge_tur_commentaries.py --no-clean
```

### Choose Output Format

```bash
# Structured format (default) - nested objects
python3 merge_tur_commentaries.py --format structured

# Flat format - array-based
python3 merge_tur_commentaries.py --format flat
```

### Use Custom Base Path

```bash
python3 merge_tur_commentaries.py --base-path /path/to/Tur
```

## Output Format

### Structured Format (Default)

```json
{
  "title": "Tur, Orach Chaim",
  "metadata": {
    "source": "Tur, Orach Chaim",
    "schema": {},
    "total_simanim": 697,
    "commentaries_included": ["Bach", "Beit Yosef", ...]
  },
  "simanim": [
    {
      "siman": 1,
      "seifim": [
        {
          "seif": 1,
          "text": "Main text here...",
          "commentaries": {
            "Bach": {
              "comments": ["Comment 1", "Comment 2"]
            },
            "Beit Yosef": {
              "comments": ["Comment 1"]
            }
          }
        }
      ]
    }
  ]
}
```

### Flat Format

```json
{
  "title": "Tur, Orach Chaim",
  "text": [
    [
      {
        "text": "Main text here...",
        "commentaries": {
          "Bach": {"comments": ["Comment 1"]},
          "Beit Yosef": {"comments": ["Comment 1"]}
        }
      }
    ]
  ],
  "commentaries_included": ["Bach", "Beit Yosef"]
}
```

## Text Cleaning

The script cleans text by:

1. Removing HTML tags
2. Removing excessive whitespace (converting multiple spaces/newlines to single space)
3. Removing control characters
4. Removing content in curly braces `{}`
5. Stripping leading/trailing whitespace

**Important:** Text cleaning is applied AFTER structure normalization to preserve the JSON array structure. This ensures that:
- All seifim (subsections) are preserved
- Text is not truncated
- The nested structure remains intact

Square brackets `[]` are preserved as they may contain important references or be part of the Hebrew text.

## Output Files

For each section, the script creates:

1. **Merged JSON file**: `Tur_<section>_merged.json`
2. **Summary text file**: `Tur_<section>_summary.txt`

Example summary:
```
Section: Tur, Orach Chaim
Total Simanim: 697
Commentaries Included (5):
  - Bach
  - Beit Yosef
  - Darkhei Moshe
  - Drisha
  - Prisha
```

## Troubleshooting

### "File is Git LFS pointer"

If you see this warning, run:
```bash
git lfs pull
```

### "Commentary directory not found"

Ensure the `Tur/Commentary` directory exists and contains the commentary subdirectories.

### "No simanim found in main text"

This usually indicates a JSON structure issue. Check that the main Tur JSON files have a `text` field.

## Example Commands

```bash
# Merge all sections with text cleaning (default)
python3 merge_tur_commentaries.py

# Merge only Orach Chaim with specific commentaries
python3 merge_tur_commentaries.py --section "Orach Chaim" --commentaries "Bach" "Beit Yosef"

# Merge all sections without text cleaning, flat format
python3 merge_tur_commentaries.py --no-clean --format flat

# Merge with custom output directory
python3 merge_tur_commentaries.py --output-dir ./my_merged_tur
```

## Comparison with Shulchan Arukh Merger

The Tur merger is based on the Shulchan Arukh merger but adapted for:

1. Different file structure (Tur files are in the root Tur directory, not in subdirectories)
2. Different commentary file naming patterns
3. Added text cleaning functionality
4. 5 commentaries instead of the Shulchan Arukh's commentaries

## Notes

- The script preserves Hebrew text and basic formatting
- Output files use UTF-8 encoding
- JSON output is formatted with 2-space indentation for readability
- The script logs progress and errors to help with debugging
