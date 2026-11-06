import os
import json
import boto3
import requests
from datetime import datetime

# --- CONFIGURATION ---
BUCKET_NAME = "data-portfolio-velib-jerom" #Nom de ton bucket S3 (base de données dans le cloud AWS)

# URLs des APIs publiques (Vélib Paris et Open-Meteo pour Paris)
VELIB_API_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/exports/json"
METEO_API_URL = "https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&current_weather=true"

# 2. Initialiser le client AWS S3
access_key = os.environ.get("AWS_ACCESS_KEY_ID")
secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
bucket_name = "data-portfolio-velib-jerom"

s3 = boto3.client(
    "s3",
    region_name="eu-north-1",
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)

def fetch_data(url):
    """Récupère les données depuis une API au format JSON en simulant un navigateur"""
    # Déguiser le script Python en navigateur web classique
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # timeout=15 force le script à abandonner si le serveur ne répond pas après 15 secondes
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status() 
    return response.json() # Retourne les données JSON sous forme de dictionnaire Python


def upload_to_s3(data, folder_name, file_prefix):
    """Sauvegarde les données en JSON et les envoie sur S3 dans un dossier partitionné par date"""
    # Créer un chemin partitionné par date : bronze/nom_dossier/année-mois-jour/fichier.json
    now = datetime.now()
    date_partition = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H-%M-%S")
    
    # Chemin exact dans le bucket (c'est ici qu'AWS crée le dossier "bronze" tout seul !)
    s3_key = f"bronze/{folder_name}/{date_partition}/{file_prefix}_{timestamp}.json"
    
    # Convertir le dictionnaire Python en texte JSON
    json_data = json.dumps(data)
    
    # Envoyer sur AWS S3
    print(f"Upload en cours vers s3://{BUCKET_NAME}/{s3_key} ...")
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json_data
    )
    print("Upload réussi !")

def main():
    print("Début de l'ingestion des données...")
    
    try:
        # 3. Récupérer et envoyer les données Vélib
        print("\nExtraction des données Vélib...")
        velib_data = fetch_data(VELIB_API_URL)
        upload_to_s3(velib_data, folder_name="velib", file_prefix="status")
        
        # 4. Récupérer et envoyer les données Météo (Paris)
        print("\nExtraction des données Météo...")
        meteo_data = fetch_data(METEO_API_URL)
        upload_to_s3(meteo_data, folder_name="meteo", file_prefix="weather")
        
        print("\n Ingestion terminée avec succès !")
        
    except Exception as e:
        print(f"\n Une erreur est survenue : {e}")

if __name__ == "__main__":
    main()