# Tur Commentary Merger - Separate Files

**UPDATED VERSION** – Creates separate JSON files for each commentary using a sequence format.

## What This Does

This script merges Tur texts with their commentaries, creating **separate output files for each commentary** (not one big merged file). Each siman is represented as an ordered sequence of the base Tur text followed by the commentary entries, so consumers can present them in reading order.

- **Input**: Tur main texts + Commentary files
- **Output**: Separate JSON file for each combination (e.g., `Tur_Orach_Chaim_Bach.json`, `Tur_Orach_Chaim_Beit_Yosef.json`, etc.)

## Structure

### Tur Text Structure
Tur JSON files have this structure:
```json
{
  "text": {
    "Orach Chaim": {
      "1": ["text for siman 1..."],
      "2": ["text for siman 2..."],
      "Introduction": [],
      "": []
    }
  }
}
```

- Each siman is a dictionary key
- No seifim separation in main text (just continuous text per siman)
- Contains placeholders for commentaries: `<i data-commentator="Bach" data-order="1.1"></i>`

### Output Structure (Default: `sequence`)
Sequence-based structure keeps the reading order explicit:
```json
{
  "title": "Tur Orach Chaim",
  "commentary": "Bach",
  "commentary_display": "Bach",
  "total_simanim": 697,
  "output_format": "sequence",
  "simanim": [
    {
      "siman": 1,
      "entries": [
        {
          "type": "text",
          "content": "Main text for siman 1...",
          "source": {
            "work": "Tur",
            "section": "Orach Chaim",
            "siman": 1,
            "category": "primary"
          }
        },
        {
          "type": "commentary",
          "name": "Bach",
          "content": "Commentary text 1",
          "source": {
            "work": "Bach",
            "section": "Orach Chaim",
            "siman": 1,
            "category": "commentary",
            "comment_index": 1
          }
        }
      ]
    }
  ]
}
```

To reproduce the previous simple structure with `text` and `commentary` arrays, run the script with `--output-format simple`.

## Usage

### Merge All Sections with All Commentaries

```bash
python merge_tur_separate_commentaries.py
```

This creates 20 files (4 sections × 5 commentaries) using the default sequence format:
- `Tur_Orach_Chaim_Bach.json`
- `Tur_Orach_Chaim_Beit_Yosef.json`
- `Tur_Orach_Chaim_Darkhei_Moshe.json`
- ...and 17 more

### Merge Specific Section

```bash
python merge_tur_separate_commentaries.py --section "Orach Chaim"
```

Creates 5 files (one per commentary for Orach Chaim).

### Merge Specific Commentary

```bash
python merge_tur_separate_commentaries.py --commentary "Bach"
```

Creates 4 files (Bach for all 4 sections).

### Merge One Section + One Commentary

```bash
python merge_tur_separate_commentaries.py --section "Orach Chaim" --commentary "Bach"
```

Creates 1 file: `Tur_Orach_Chaim_Bach.json`.

### Custom Output Directory

```bash
python merge_tur_separate_commentaries.py --output-dir ./my_output
```

### Disable Text Cleaning

```bash
python merge_tur_separate_commentaries.py --no-clean
```

### Legacy Simple Output

```bash
python merge_tur_separate_commentaries.py --output-format simple
```

Outputs the previous structure with `text` and `commentary` arrays for each siman.

## Commentaries Supported

1. **Bach** - Bayit Chadash
2. **Beit_Yosef** - Beit Yosef
3. **Darkhei_Moshe** - Darkhei Moshe
4. **Drisha** - Drisha
5. **Prisha** - Prisha

## Sections Supported

1. **Orach Chaim**
2. **Yoreh Deah**
3. **Even HaEzer**
4. **Choshen Mishpat**

## Text Cleaning

By default, the script cleans:
- HTML tags (e.g., `<i>`, `<b>`)
- Excessive whitespace
- Leading/trailing spaces

Use `--no-clean` to keep original formatting.

## Output Files

Each output file contains:
- **title**: Section name
- **commentary** / **commentary_display**: Internal name and display label for the commentary
- **total_simanim**: Number of simanim
- **output_format**: Indicates whether the file was produced in `sequence` (default) or `simple` mode
- **simanim**: Array of simanim. In sequence mode each siman has an `entries` array ordered as base text followed by commentary notes, each with `source` metadata. In simple mode the siman contains `text` and `commentary` arrays as in previous versions.

## Example Output Files

After running the default command, you'll find in `Tur/Merged_Commentaries/`:

```
Tur_Orach_Chaim_Bach.json
Tur_Orach_Chaim_Beit_Yosef.json
Tur_Orach_Chaim_Darkhei_Moshe.json
Tur_Orach_Chaim_Drisha.json
Tur_Orach_Chaim_Prisha.json
Tur_Yoreh_Deah_Bach.json
...
```

## Differences from Old Script

**Old script** (`merge_tur_commentaries.py`):
- Tried to merge all commentaries into one file
- Complex seifim handling
- Didn't work correctly with Tur structure

**New script** (`merge_tur_separate_commentaries.py`):
- ✓ Creates separate files per commentary
- ✓ Simple siman-based structure
- ✓ Works with Tur's dict-based format
- ✓ No seifim complexity
- ✓ Clean, straightforward output

## Requirements

- Python 3.6+
- Tur JSON files (in `Tur/` directory)
- Commentary JSON files (in `Tur/Commentary/`)

## Troubleshooting

### "File is Git LFS pointer"
If you see this warning, the actual files haven't been downloaded from Git LFS. On your local machine with the actual files, this won't be an issue.

### "Section not found"
Check that the JSON structure matches the expected format with section names as keys.

### "Failed to load commentary"
Verify that commentary files exist in the expected paths under `Tur/Commentary/`.

## Example Commands

```bash
# All sections, all commentaries (creates 20 files)
python merge_tur_separate_commentaries.py

# Only Orach Chaim (creates 5 files)
python merge_tur_separate_commentaries.py --section "Orach Chaim"

# Only Bach commentary (creates 4 files)
python merge_tur_separate_commentaries.py --commentary "Bach"

# One specific combination (creates 1 file)
python merge_tur_separate_commentaries.py --section "Orach Chaim" --commentary "Bach"

# Custom output location
python merge_tur_separate_commentaries.py --output-dir ./output

# Keep original formatting (no cleaning)
python merge_tur_separate_commentaries.py --no-clean

# Legacy simple structure
python merge_tur_separate_commentaries.py --output-format simple
```
