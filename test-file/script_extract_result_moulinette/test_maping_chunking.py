import json

file_path = 'data/processed/chunks/chunk_mapping.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Analyse en cours de {len(data)} éléments...\n")
    
    anomalies_trouvees = False
    count = 0
    # 2. Boucle de vérification
    for index, item in enumerate(data):
        # Récupération sécurisée du texte
        texte = item.get('text', '')
        longueur = len(texte)
        
        # 3. Filtrage : On ne garde que ce qui dépasse ou atteint 2000 caractères
        if longueur > 2000:
            print(f"⚠️ Alerte (Index {index}) : {longueur} caractères (Limite dépassée) {item.get('file_path', '')}")
            count += 1
            anomalies_trouvees = True
            
    # 4. Résumé final
    if not anomalies_trouvees:
        print("✅ Tout est en ordre : aucun élément ne dépasse 2000 caractères.")
    else:
        print("\nAnalyse terminée : Certains éléments dépassent la limite autorisée.")
        print(count)

except FileNotFoundError:
    print("Erreur : Le fichier est introuvable.")
except json.JSONDecodeError:
    print("Erreur : Le fichier n'est pas un JSON valide.")
except Exception as e:
    print(f"Une erreur inattendue est survenue : {e}")