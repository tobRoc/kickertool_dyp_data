import json
import requests
import os

def download_json(url):
    response = requests.get(url)
    response.raise_for_status() # Raise an exception for HTTP errors
    return response.json()

#https://live.kickertool.de/api/table_soccer/pages/dyp_nuernberg.json

# Pfad zur JSON-Datei
url = 'https://live.kickertool.de/api/table_soccer/pages/dyp_nuernberg.json'
data = download_json(url)

json_file_path = 'https://live.kickertool.de/api/table_soccer/pages/dyp_nuernberg.json'

# Verzeichnis zum Speichern der heruntergeladenen Dateien
download_dir = './tournaments/'

# Erstellen des Verzeichnisses, falls es nicht existiert
os.makedirs(download_dir, exist_ok=True)

# Basis-URL für den Download
base_url = "https://live.kickertool.de/api/table_soccer/tournaments/"

# Durchlaufen der Turniere und Herunterladen der Dateien
for tournament in data['tournaments']:
    tournament_id = tournament['_id']
    url = f"{base_url}{tournament_id}.json"
    response = requests.get(url)
    
    if response.status_code == 200:
        file_path = os.path.join(download_dir, f"{tournament_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"Downloaded: {file_path}")
    else:
        print(f"Failed to download: {url}")

print("Download abgeschlossen.")
