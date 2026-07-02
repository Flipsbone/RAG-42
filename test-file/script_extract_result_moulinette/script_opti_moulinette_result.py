import json
import os


def extraire_donnees():
    json_path = "data/output/search_results/dataset_docs_public.json"
    out_path = "result_moulinette.txt"

    if not os.path.exists(json_path):
        print(f"Erreur : Fichier source introuvable à {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    results = data.get("search_results", [])

    with open(out_path, "w", encoding="utf-8") as out_file:
        for item in results:
            question = item.get("question_str", "")

            for source in item.get("retrieved_sources", []):
                file_path = source.get("file_path")
                start = source.get("first_character_index")
                end = source.get("last_character_index")
                mon_text = source.get("text", "")

                if file_path and os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as src_file:
                        content = src_file.read()
                        le_text = content[start:end] if start is not None and end is not None else ""

                        resultat = (
                            f"Question {question}\n"
                            f"my_answered {mon_text}\n"
                            f"expected_ansered {le_text}\n"
                        )

                        out_file.write(resultat + "\n")
                        print(resultat)


if __name__ == "__main__":
    extraire_donnees()
