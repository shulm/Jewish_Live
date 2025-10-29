# Tur Commentary Merger with Placeholder-Based Insertion

This script (`merge_tur_with_placeholders.py`) merges Tur texts with their commentaries by parsing placeholder tags in the main text and inserting commentary at those specific positions.

## Features

- **Placeholder-based insertion**: Parses `<i data-commentator="..." data-order="..."></i>` tags in the main text
- **Separate files per commentary**: Creates individual JSON files for each section-commentary combination
- **Proper text flow**: Inserts commentary at the exact positions indicated by placeholders
- **Source attribution**: Includes detailed metadata for both main text and commentary
- **Clean output**: Removes HTML tags and excessive whitespace while preserving content

## How It Works

### Placeholder Detection

The script looks for placeholder tags in the Tur main text like:
```html
<i data-commentator="Beit Yosef" data-order="1.1"></i>
```

When found, it:
1. Splits the text at the placeholder position
2. Inserts the corresponding commentary at that location
3. Continues with the remaining text

### Output Format

Each merged file contains:

```json
{
  "title": "Tur Orach Chaim",
  "commentary": "Bach",
  "commentary_display": "Bach",
  "total_simanim": 697,
  "source": {
    "main_text": {
      "work": "Tur",
      "section": "Orach Chaim",
      "file": "Orach Chaim.json"
    },
    "commentary": {
      "work": "Bach",
      "internal_name": "Bach",
      "section": "Orach Chaim",
      "file": "Tur Orach Chaim.json"
    }
  },
  "simanim": [
    {
      "siman": 1,
      "entries": [
        {
          "text": {
            "content": "Main Tur text before commentary...",
            "source": {
              "work": "Tur",
              "section": "Orach Chaim",
              "siman": 1,
              "category": "primary",
              "segment_index": 1
            }
          }
        },
        {
          "commentary": {
            "content": "Bach commentary text...",
            "source": {
              "work": "Bach",
              "section": "Orach Chaim",
              "siman": 1,
              "category": "commentary",
              "commentary_name": "Bach",
              "order": "1.1",
              "comment_index": 1
            }
          }
        },
        {
          "text": {
            "content": "Main Tur text after commentary...",
            "source": {
              "work": "Tur",
              "section": "Orach Chaim",
              "siman": 1,
              "category": "primary",
              "segment_index": 2
            }
          }
        }
      ]
    }
  ]
}
```

### Key Features of Output Format

1. **Entries array**: Each siman contains an `entries` array with text and commentary objects
2. **Text segments**: Split at placeholder positions for proper reading flow
3. **Commentary insertion**: Placed exactly where placeholders indicate
4. **Source metadata**: Detailed provenance for every segment
5. **Order tracking**: Preserves the `data-order` attribute from placeholders

## Prerequisites

### Git LFS Files

The Tur JSON files are stored in Git LFS. Before running the merger:

```bash
# Install Git LFS
sudo apt-get install git-lfs  # Ubuntu/Debian
brew install git-lfs          # macOS

# Initialize and pull LFS files
git lfs install
git lfs pull
```

### Directory Structure

```
Tur/
├── Orach Chaim.json
├── Yoreh Deah.json
├── Even HaEzer.json
├── Choshen Mishpat.json
└── Commentary/
    ├── Bach/Hebrew/
    │   ├── Tur Orach Chaim.json
    │   ├── Tur Yoreh Deah.json
    │   ├── Tur Even HaEzer.json
    │   └── Tur Choshen Mishpat.json
    ├── Beit Yosef/Hebrew/
    ├── Darkhei Moshe/Hebrew/
    ├── Drisha/Hebrew/
    └── Prisha/Hebrew/
```

## Usage

### Merge All Sections with All Commentaries

```bash
python3 merge_tur_with_placeholders.py
```

This creates 20 files (4 sections × 5 commentaries):
- `Tur_Orach_Chaim_Bach.json`
- `Tur_Orach_Chaim_Beit_Yosef.json`
- `Tur_Orach_Chaim_Darkhei_Moshe.json`
- `Tur_Orach_Chaim_Drisha.json`
- `Tur_Orach_Chaim_Prisha.json`
- ...and 15 more

### Merge Specific Section

```bash
python3 merge_tur_with_placeholders.py --section "Orach Chaim"
```

Creates 5 files (one per commentary).

### Merge Specific Commentary

```bash
python3 merge_tur_with_placeholders.py --commentary "Bach"
```

Creates 4 files (one per section).

### Merge One Section + One Commentary

```bash
python3 merge_tur_with_placeholders.py --section "Orach Chaim" --commentary "Bach"
```

Creates 1 file: `Tur_Orach_Chaim_Bach.json`.

### Custom Output Directory

```bash
python3 merge_tur_with_placeholders.py --output-dir ./custom_output
```

### Disable Text Cleaning

```bash
python3 merge_tur_with_placeholders.py --no-clean
```

Keeps original HTML tags and whitespace.

### Custom Base Path

```bash
python3 merge_tur_with_placeholders.py --base-path /path/to/Tur
```

## Commentaries Supported

1. **Bach** - Bayit Chadash
2. **Beit_Yosef** - Beit Yosef
3. **Darkhei_Moshe** - Darkhei Moshe
4. **Drisha** - Drisha
5. **Prisha** - Prisha

## Sections Supported

1. **Orach Chaim** - 697 simanim
2. **Yoreh Deah** - 403 simanim
3. **Even HaEzer** - 178 simanim
4. **Choshen Mishpat** - 427 simanim

## Text Cleaning

By default, the script:
- Removes HTML tags (including placeholders after processing)
- Removes excessive whitespace
- Strips leading/trailing spaces
- Preserves Hebrew text and formatting

Use `--no-clean` to disable cleaning.

## Comparison with Other Merge Scripts

### `merge_tur_commentaries.py`
- Tries to merge ALL commentaries into one file
- Uses seifim structure (not applicable to Tur)
- Doesn't use placeholders

### `merge_tur_separate_commentaries.py`
- Creates separate files per commentary ✓
- Simple sequence without placeholder parsing
- Adds all commentary after all text for each siman

### `merge_tur_with_placeholders.py` (This Script)
- ✓ Creates separate files per commentary
- ✓ Parses placeholders to determine insertion points
- ✓ Splits text at placeholder positions
- ✓ Maintains proper reading order
- ✓ Includes detailed source metadata
- ✓ Preserves order information from placeholders

## Example Commands

```bash
# Merge all sections with all commentaries
python3 merge_tur_with_placeholders.py

# Merge only Orach Chaim with all commentaries
python3 merge_tur_with_placeholders.py --section "Orach Chaim"

# Merge only Bach commentary for all sections
python3 merge_tur_with_placeholders.py --commentary "Bach"

# Merge specific combination
python3 merge_tur_with_placeholders.py --section "Yoreh Deah" --commentary "Beit_Yosef"

# Custom output directory
python3 merge_tur_with_placeholders.py --output-dir ./Tur/Merged_With_Placeholders

# Without text cleaning
python3 merge_tur_with_placeholders.py --no-clean

# Custom base path
python3 merge_tur_with_placeholders.py --base-path /data/Tur
```

## Testing

The script includes test data in `tests/data/tur_sample/`. To test:

```bash
cd tests/data/tur_sample
python3 ../../../merge_tur_with_placeholders.py \
  --section "Even HaEzer" \
  --commentary "Beit_Yosef" \
  --output-dir ./test_output
```

## Troubleshooting

### "File is Git LFS pointer"

The actual file content hasn't been downloaded from Git LFS:
```bash
git lfs pull
```

### "Section not found in main text"

Check that the main file contains the expected section in its `text` object.

### "Failed to load commentary"

Verify:
1. Commentary file exists in `Tur/Commentary/<commentary_name>/Hebrew/`
2. File naming matches the expected pattern
3. For "Choshen Mishpat", check both with and without comma before "Vilna"

### "No simanim found"

The JSON structure may be different than expected. Check:
- Main text should have `{"text": {"Section Name": {...}}}`
- Commentary should have similar structure with "Siman N" keys

## Output Files

Each output file is saved to `./Tur/Merged_Commentaries/` by default:
- UTF-8 encoding
- Pretty-printed JSON with 2-space indentation
- Preserves Hebrew characters
- Includes complete source attribution

## Performance

- Processing time: ~1-2 seconds per section-commentary combination
- Output file size: 10-25 MB per merged file (depending on section)
- Total for all 20 files: ~250-500 MB

## Notes

- Hebrew text and formatting are fully preserved
- Placeholder `data-order` values are tracked in the source metadata
- When no placeholders exist, commentary is added after all text for that siman
- Empty simanim are skipped
- The script is idempotent - safe to run multiple times
