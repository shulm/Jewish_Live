# Tur Commentary Merger - Separate Files

**UPDATED VERSION** – Creates separate JSON files for each commentary, inserting commentary text directly where the Tur provides placeholders.

## What This Does

This script merges Tur texts with their commentaries, creating **separate output files for each commentary** (not one big merged file). Each siman is represented as an ordered sequence of the base Tur text followed by the commentary entries, so consumers can present them in reading order.

- **Input**: Tur main texts + Commentary files
- **Output**: Separate JSON file for each combination (e.g., `Tur_Orach_Chaim_Bach.json`, `Tur_Orach_Chaim_Beit_Yosef.json`, etc.)

## Structure

### Tur Text Structure
Tur JSON files typically look like this:
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
- Commentaries are referenced via placeholders such as `<i data-commentator="Bach" data-order="1.1"></i>`.

### Commentary Structure
Commentary JSON stores simanim as arrays or dicts with paragraph lists, for example:
```json
{
  "text": {
    "Orach Chaim": {
      "Siman 1": {
        "paragraphs": [
          "<p>First comment...</p>",
          "<p>Second comment...</p>"
        ]
      }
    }
  }
}
```

Comment entries are enumerated so they can be paired with placeholder `data-order` values inside the main text.

### Output Structure (Default: `embedded`)
The default `embedded` output stitches commentary segments into the reading
order of the Tur text. Every siman lists `entries` that contain the text
leading up to a placeholder and the matching commentary (if available).
```json
{
  "metadata": {
    "section": "Orach Chaim",
    "commentary_key": "Beit_Yosef",
    "commentary_display": "Beit Yosef",
    "output_format": "embedded",
    "sources": {
      "primary": {
        "work": "Tur Orach Chaim",
        "path": "Tur/Orach Chaim.json"
      },
      "commentary": {
        "work": "Beit Yosef",
        "key": "Beit_Yosef",
        "path": "Tur/Commentary/Beit Yosef/Hebrew/Tur Orach Chaim, Vilna, 1923.json"
      }
    }
  },
  "total_simanim": 697,
  "simanim": [
    {
      "siman": 1,
      "entries": [
        {
          "text": {
            "content": "Introductory Tur paragraph...",
            "source": {
              "type": "primary",
              "work": "Tur",
              "section": "Orach Chaim",
              "siman": 1,
              "segment_index": 1
            }
          },
          "commentary": {
            "content": "Matching commentary text...",
            "order": "1.1",
            "status": "matched",
            "commentator": "Beit Yosef",
            "source": {
              "type": "commentary",
              "work": "Beit Yosef",
              "section": "Orach Chaim",
              "siman": 1,
              "commentary_key": "Beit_Yosef",
              "comment_index": 1
            }
          }
        },
        {
          "text": {
            "content": "Continuation of the Tur after the placeholder...",
            "source": {
              "type": "primary",
              "work": "Tur",
              "section": "Orach Chaim",
              "siman": 1,
              "segment_index": 2
            }
          }
        }
      ]
    }
  ]
}
```

Each entry exposes provenance in its `source` block and records whether a
commentary snippet was matched, supplied as a fallback, or left unused.

### Alternate Output Modes
- `--output-format sequence` restores the linear list of `type`/`text` entries
  from the previous release.
- `--output-format simple` returns the legacy structure with `text` and
  `commentary` arrays per siman.

## Usage

### Merge All Sections with All Commentaries

```bash
python merge_tur_separate_commentaries.py
```

This creates 20 files (4 sections × 5 commentaries) using the default embedded format:
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

### Alternate Formats

- `--output-format sequence` &rarr; reproduces the previous sequence layout.
- `--output-format simple` &rarr; emits the classic `text`/`commentary` arrays per siman.

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
- **metadata**: Section, commentary identifiers, selected output format, and source attribution for the Tur text and commentary.
- **total_simanim**: Number of simanim merged.
- **simanim**: Array of simanim.
  - In `embedded` mode each siman exposes `entries` that align Tur text with commentaries at their placeholders.
  - In `sequence` mode each siman retains the legacy `sequence` array of ordered text/commentary segments.
  - In `simple` mode each siman contains `text` and `commentary` arrays like earlier versions of the script.

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
- ✓ Inserts commentary into the primary text flow using placeholders
- ✓ Offers `embedded`, `sequence`, and `simple` output modes
- ✓ Works with Tur's dict-based format without seifim complexity
- ✓ Exposes detailed provenance metadata for every segment

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
