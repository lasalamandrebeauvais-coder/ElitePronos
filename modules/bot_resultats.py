import requests
import sqlite3
import os

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Cle API Football-Data (la meme que bot_sourcing)
API_TOKEN = 'bf58da6a49824f2a8742957b89ca52ee'

def recuperer_resultats_finaux():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. On récupère les matchs stockés en base
    cursor.execute("SELECT id, equipe_home, equipe_away FROM matches")
    matchs_en_base = cursor.fetchall()

    headers = { 'X-Auth-Token': API_TOKEN }
    matchs_mis_a_jour = 0

    print("📡 Recherche des scores finaux sur l'API...")

    # On récupère tous les matchs TERMINÉS récemment
    url = "https://api.football-data.org/v4/matches?status=FINISHED"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            matchs_api = response.json().get('matches', [])
            
            for m_db in matchs_en_base:
                id_db, home_db, away_db = m_db
                
                # On cherche si ce match est dans les résultats de l'API
                for m_api in matchs_api:
                    home_api = m_api['homeTeam']['name']
                    away_api = m_api['awayTeam']['name']
                    
                    # Comparaison des noms d'équipes
                    if home_db == home_api and away_db == away_api:
                        score_h = m_api['score']['fullTime']['home']
                        score_a = m_api['score']['fullTime']['away']
                        
                        # Mise à jour de la base de données
                        cursor.execute('''
                            UPDATE matches 
                            SET score_final_home = ?, score_final_away = ? 
                            WHERE id = ?
                        ''', (score_h, score_a, id_db))
                        
                        print(f"✅ Score trouvé pour {home_db}-{away_db} : {score_h}-{score_a}")
                        matchs_mis_a_jour += 1
        else:
            print(f"❌ Erreur API : {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")

    conn.commit()
    conn.close()
    print(f"\n🏁 Mise à jour terminée : {matchs_mis_a_jour} matchs actualisés.")

if __name__ == "__main__":
    recuperer_resultats_finaux()
    