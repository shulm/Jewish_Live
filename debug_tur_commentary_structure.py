#!/usr/bin/env python3
"""
Debug script to examine Tur and commentary structure
Run this and send me the output!
"""
import json
from pathlib import Path

def examine_structure(file_path, name):
    print("\n" + "="*80)
    print(f"EXAMINING: {name}")
    print(f"File: {file_path}")
    print("="*80)

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\nTop-level keys: {list(data.keys())}")

    if 'text' in data:
        print(f"Type of data['text']: {type(data['text'])}")
        print(f"Keys in data['text']: {list(data['text'].keys())}")

        # Check Orach Chaim section
        if 'Orach Chaim' in data['text']:
            oc = data['text']['Orach Chaim']
            print(f"\nType of Orach Chaim: {type(oc)}")
            print(f"Keys in Orach Chaim: {list(oc.keys())[:10]}")

            # Check empty string key
            if '' in oc:
                arr = oc['']
                print(f"\nFound '' (empty string) key!")
                print(f"Type: {type(arr)}")
                print(f"Length (number of simanim): {len(arr)}")

                if len(arr) > 0:
                    print(f"\n--- SIMAN 1 ---")
                    siman1 = arr[0]
                    print(f"Type: {type(siman1)}")

                    if isinstance(siman1, list):
                        print(f"Length: {len(siman1)}")
                        print(f"Items in siman 1:")
                        for i, item in enumerate(siman1[:5]):  # First 5 items
                            print(f"  [{i}] type={type(item)}")
                            if isinstance(item, str):
                                print(f"      len={len(item)}, first 150 chars: {item[:150]}")
                            elif isinstance(item, list):
                                print(f"      list with {len(item)} items")
                                if len(item) > 0:
                                    print(f"      first item type: {type(item[0])}")
                                    if isinstance(item[0], str):
                                        print(f"      first item (150 chars): {item[0][:150]}")
                    elif isinstance(siman1, str):
                        print(f"String with length: {len(siman1)}")
                        print(f"First 200 chars: {siman1[:200]}")

                if len(arr) > 1:
                    print(f"\n--- SIMAN 2 ---")
                    siman2 = arr[1]
                    print(f"Type: {type(siman2)}")
                    if isinstance(siman2, list):
                        print(f"Length: {len(siman2)}")
                        if len(siman2) > 0:
                            print(f"First item type: {type(siman2[0])}")

# Examine main Tur file
tur_file = Path('Tur/Orach Chaim.json')
if tur_file.exists():
    examine_structure(tur_file, "TUR MAIN TEXT - Orach Chaim")
else:
    print(f"File not found: {tur_file}")

# Examine Bach commentary
bach_file = Path('Tur/Commentary/Bach/Hebrew/Tur Orach Chaim.json')
if bach_file.exists():
    examine_structure(bach_file, "BACH COMMENTARY - Orach Chaim")
else:
    print(f"File not found: {bach_file}")

# Examine Beit Yosef commentary
beit_yosef_file = Path('Tur/Commentary/Beit Yosef/Hebrew/Tur Orach Chaim, Vilna, 1923.json')
if beit_yosef_file.exists():
    examine_structure(beit_yosef_file, "BEIT YOSEF COMMENTARY - Orach Chaim")
else:
    print(f"File not found: {beit_yosef_file}")

print("\n" + "="*80)
print("DONE - Please send me this entire output!")
print("="*80)