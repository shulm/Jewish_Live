# Shulchan Arukh Commentary Merger

This tool merges Shulchan Arukh texts with their commentaries, creating a unified JSON structure where commentaries are stored as separate fields. This allows you to easily include or exclude specific commentaries in the future.

## Features

- **Flexible Commentary Selection**: Choose which commentaries to include or exclude
- **Two Output Formats**: Structured (nested objects) or Flat (array-based)
- **All Sections Supported**: Orach Chayim, Yoreh De'ah, Choshen Mishpat, Even HaEzer
- **60+ Commentaries**: Automatically discovers and merges all available commentaries
- **Git LFS Compatible**: Works with JSON files stored in Git LFS

## Prerequisites

Before running the script, ensure you have the actual JSON files (not LFS pointers):

```bash
# Pull the actual files from Git LFS
git lfs pull
```

## Installation

No additional dependencies required - uses Python standard library only!

## Basic Usage

### Merge All Sections

```bash
python merge_commentaries.py --section all
```

### Merge Specific Section

```bash
# Merge only Orach Chayim
python merge_commentaries.py --section "Orach Chayim"

# Merge only Yoreh De'ah
python merge_commentaries.py --section "Yoreh De'ah"
```

### Choose Specific Commentaries

```bash
# Include only Mishnah Berurah and Magen Avraham
python merge_commentaries.py \
  --section "Orach Chayim" \
  --commentaries "Mishnah Berurah on Shulchan Arukh, Orach Chayim" \
               "Magen Avraham on Shulchan Arukh, Orach Chayim"
```

### Choose Output Format

```bash
# Structured format (default) - nested objects
python merge_commentaries.py --format structured

# Flat format - keeps array structure
python merge_commentaries.py --format flat
```

### Custom Output Directory

```bash
python merge_commentaries.py --output-dir ./my_output
```

## Output Formats

### Structured Format (Recommended)

This format creates a hierarchical structure with explicit Siman and Se'if objects:

```json
{
  "title": "Shulchan Arukh, Orach Chayim",
  "metadata": {
    "source": "Shulchan Arukh, Orach Chayim",
    "total_simanim": 697,
    "commentaries_included": [
      "Mishnah Berurah on Shulchan Arukh, Orach Chayim",
      "Magen Avraham on Shulchan Arukh, Orach Chayim"
    ]
  },
  "simanim": [
    {
      "siman": 1,
      "seifim": [
        {
          "seif": 1,
          "text": "Main text of Siman 1, Se'if 1",
          "commentaries": {
            "Mishnah Berurah on Shulchan Arukh, Orach Chayim": {
              "author": "Mishnah Berurah",
              "comments": [
                "First comment on this se'if",
                "Second comment on this se'if"
              ]
            },
            "Magen Avraham on Shulchan Arukh, Orach Chayim": {
              "author": "Magen Avraham",
              "comments": [
                "Commentary from Magen Avraham"
              ]
            }
          }
        },
        {
          "seif": 2,
          "text": "Main text of Siman 1, Se'if 2",
          "commentaries": {}
        }
      ]
    }
  ]
}
```

**Benefits:**
- Easy to navigate by Siman and Se'if numbers
- Clear structure for APIs and applications
- Explicit numbering makes references easier

### Flat Format

This format keeps the original array structure but adds commentary fields:

```json
{
  "title": "Shulchan Arukh, Orach Chayim",
  "schema": { ... },
  "commentaries_included": ["Mishnah Berurah on Shulchan Arukh, Orach Chayim"],
  "text": [
    [
      {
        "text": "Main text of Siman 1, Se'if 1",
        "commentaries": {
          "Mishnah Berurah on Shulchan Arukh, Orach Chayim": {
            "author": "Mishnah Berurah",
            "comments": ["Commentary text"]
          }
        }
      }
    ]
  ]
}
```

**Benefits:**
- Compatible with original Sefaria format
- Preserves original schema and metadata
- Array indices match Siman/Se'if numbers (0-based)

## Using the Configuration File

Edit `commentary_config.json` to set which commentaries to include:

```json
{
  "commentary_selection": {
    "Orach Chayim": {
      "Mishnah Berurah on Shulchan Arukh, Orach Chayim": true,
      "Magen Avraham on Shulchan Arukh, Orach Chayim": false,
      ...
    }
  }
}
```

Set `false` for commentaries you want to exclude.

## Output Files

For each section, the script creates:

1. **`{Section}_merged.json`** - The merged JSON file with commentaries
2. **`{Section}_summary.txt`** - A summary of what was merged

Example:
```
merged_output/
├── Orach_Chayim_merged.json
├── Orach_Chayim_summary.txt
├── Yoreh_Deah_merged.json
├── Yoreh_Deah_summary.txt
├── Choshen_Mishpat_merged.json
├── Choshen_Mishpat_summary.txt
├── Even_HaEzer_merged.json
└── Even_HaEzer_summary.txt
```

## Available Commentaries by Section

### Orach Chayim (20 commentaries)
- Mishnah Berurah, Magen Avraham, Ba'er Hetev, Beur HaGra, Turei Zahav, and 15 more

### Yoreh De'ah (10+ commentaries)
- Siftei Kohen, Pitchei Teshuva, Ba'er Hetev, Beur HaGra, and more

### Choshen Mishpat (11+ commentaries)
- Siftei Kohen, Ketzot HaChoshen, Netivot HaMishpat, Me'irat Einayim, and more

### Even HaEzer (8+ commentaries)
- Beit Meir, Ba'er Hetev, Pitchei Teshuva, Beur HaGra, and more

## Programming Examples

### Python: Load and Filter Commentaries

```python
import json

# Load merged file
with open('merged_output/Orach_Chayim_merged.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get a specific Siman and Se'if
siman_1 = data['simanim'][0]  # Siman 1 (0-based)
seif_1 = siman_1['seifim'][0]  # Se'if 1

# Get only Mishnah Berurah commentary
mb_commentary = seif_1['commentaries'].get('Mishnah Berurah on Shulchan Arukh, Orach Chayim', {})
print(mb_commentary.get('comments', []))

# Remove a commentary from all seifim
for siman in data['simanim']:
    for seif in siman['seifim']:
        if 'Magen Avraham on Shulchan Arukh, Orach Chayim' in seif['commentaries']:
            del seif['commentaries']['Magen Avraham on Shulchan Arukh, Orach Chayim']
```

### JavaScript: Display with Commentary Selection

```javascript
const data = require('./merged_output/Orach_Chayim_merged.json');

// Get available commentaries
const availableCommentaries = data.metadata.commentaries_included;

// Display text with selected commentaries
function displaySeif(siman, seif, selectedCommentaries) {
  const simanObj = data.simanim[siman - 1];
  const seifObj = simanObj.seifim[seif - 1];

  console.log(`Main Text: ${seifObj.text}`);

  selectedCommentaries.forEach(commName => {
    const comm = seifObj.commentaries[commName];
    if (comm) {
      console.log(`\n${commName}:`);
      comm.comments.forEach((comment, i) => {
        console.log(`  ${i + 1}. ${comment}`);
      });
    }
  });
}

// Show Siman 1, Se'if 1 with only Mishnah Berurah
displaySeif(1, 1, ['Mishnah Berurah on Shulchan Arukh, Orach Chayim']);
```

## Troubleshooting

### "File is Git LFS pointer" Error

```bash
# Pull actual files from Git LFS
git lfs pull
```

### "Commentary directory not found" Warning

Make sure you're running from the correct directory or specify `--base-path`:

```bash
python merge_commentaries.py --base-path "/path/to/Shulchan Arukh"
```

### Empty Commentaries

Some commentaries may not cover all Simanim or Se'ifim. Empty commentaries are automatically excluded from the output.

## Advanced Usage

### Create Custom Merge Script

```python
from merge_commentaries import ShulchanArukhMerger

merger = ShulchanArukhMerger()

# Merge with specific commentaries
merged = merger.merge_section(
    "Shulchan Arukh, Orach Chayim",
    commentaries_to_include=[
        "Mishnah Berurah on Shulchan Arukh, Orach Chayim",
        "Magen Avraham on Shulchan Arukh, Orach Chayim"
    ],
    output_format="structured"
)

# Do custom processing
# ...
```

## File Structure

```
Jewish_Live/
├── merge_commentaries.py          # Main script
├── commentary_config.json         # Configuration file
├── MERGE_README.md               # This file
├── Shulchan Arukh/
│   ├── Shulchan Arukh, Orach Chayim/
│   │   └── Hebrew/merged.json
│   ├── Shulchan Arukh, Yoreh De'ah/
│   │   └── Hebrew/merged.json
│   ├── Shulchan Arukh, Choshen Mishpat/
│   │   └── Hebrew/merged.json
│   ├── Shulchan Arukh, Even HaEzer/
│   │   └── Hebrew/merged.json
│   └── Commentary/
│       ├── [Author]/
│       │   └── [Commentary Title]/
│       │       └── Hebrew/merged.json
│       └── ...
└── merged_output/                 # Output directory (created by script)
```

## License

This tool is for educational and religious study purposes.

## Support

For issues or questions, please refer to the main project documentation.
