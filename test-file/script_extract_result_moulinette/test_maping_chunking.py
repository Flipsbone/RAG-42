import json

file_path = 'data/processed/chunks/chunk_mapping.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Analyzing {len(data)} items...\n")

    anomalies_found = False
    count = 0
    for index, item in enumerate(data):
        text = item.get('text', '')
        length = len(text)

        if length > 2000:
            print(f"⚠️ Alert (Index {index}): {length}"
                  f"characters (Limit exceeded) {item.get('file_path', '')}")
            count += 1
            anomalies_found = True

    if not anomalies_found:
        print("✅ Everything is in order: no element exceeds 2000 characters.")
    else:
        print("\nAnalysis complete: Some elements exceed the allowed limit.")
        print(f"Total anomalies found: {count}")

except FileNotFoundError:
    print("Error: The file could not be found.")
except json.JSONDecodeError:
    print("Error: The file is not a valid JSON.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
