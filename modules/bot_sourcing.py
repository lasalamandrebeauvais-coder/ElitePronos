"""
Bot Sourcing pour Elite Pronos
Import automatique du calendrier Ligue 1 (J1 a J38)
Support pluriannuel avec detection automatique de la saison
"""
import requests
import sqlite3
import random
import os
from datetime import datetime

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Cle API Football-Data
API_TOKEN = 'bf58da6a49824f2a8742957b89ca52ee'


def get_saison_actuelle():
    """Retourne l'ID de la saison actuelle (ex: 2024 pour 2024-2025)"""
    now = datetime.now()
    if now.month >= 8:
        return now.year
    return now.year - 1


def importer_calendrier_complet_l1(saison_id=None):
    """
    Importe l'integralite du calendrier Ligue 1 (J1 a J38)
    A utiliser en phase de preparation (juillet)
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    headers = {'X-Auth-Token': API_TOKEN}

    print(f"[INFO] Import calendrier Ligue 1 saison {saison_id}-{saison_id+1}")
    print("[INFO] Recuperation des matchs...")

    # Recuperer tous les matchs de la saison Ligue 1
    url = f'https://api.football-data.org/v4/competitions/FL1/matches?season={saison_id}'

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[ERREUR] API retourne {response.status_code}")
            return False, f"Erreur API: {response.status_code}"

        data = response.json()
        matchs = data.get('matches', [])

        print(f"[INFO] {len(matchs)} matchs trouves")

        # Grouper par journee (matchday)
        journees = {}
        for m in matchs:
            journee = m.get('matchday', 1)
            if journee not in journees:
                journees[journee] = []
            journees[journee].append(m)

        # Inserer les matchs
        nb_inseres = 0
        for journee, matchs_journee in journees.items():
            # Selectionner 4 matchs par journee (priorite equilibre des cotes)
            matchs_tries = sorted(matchs_journee, key=lambda x: random.random())[:4]

            for m in matchs_tries:
                # Generer des cotes realistes si non disponibles
                cote_h = round(random.uniform(1.80, 3.50), 2)
                cote_n = round(random.uniform(3.00, 4.00), 2)
                cote_a = round(random.uniform(2.00, 4.50), 2)

                # Verifier si le match existe deja
                cursor.execute('''
                    SELECT id FROM matches
                    WHERE saison_id = ? AND semaine_id = ? AND equipe_home = ? AND equipe_away = ?
                ''', (saison_id, journee, m['homeTeam']['name'], m['awayTeam']['name']))

                if cursor.fetchone() is None:
                    cursor.execute('''
                        INSERT INTO matches (saison_id, semaine_id, championnat, equipe_home, equipe_away,
                                            cote_home, cote_draw, cote_away, date_match, is_active)
                        VALUES (?, ?, 'FL1', ?, ?, ?, ?, ?, ?, 1)
                    ''', (saison_id, journee, m['homeTeam']['name'], m['awayTeam']['name'],
                          cote_h, cote_n, cote_a, m['utcDate']))
                    nb_inseres += 1

        conn.commit()
        conn.close()

        print(f"[OK] {nb_inseres} matchs inseres pour la saison {saison_id}")
        return True, f"{nb_inseres} matchs importes"

    except Exception as e:
        conn.close()
        print(f"[ERREUR] {str(e)}")
        return False, str(e)


def sourcing_semaine_courante(semaine_id=None):
    """
    Sourcing des 4 matchs pour la semaine courante
    Priorite Ligue 1, complete par autres championnats si besoin
    """
    saison_id = get_saison_actuelle()

    if semaine_id is None:
        # Calculer la semaine basee sur la date
        semaine_id = datetime.now().isocalendar()[1]

    leagues = ['FL1', 'PL', 'PD', 'SA', 'BL1']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    headers = {'X-Auth-Token': API_TOKEN}
    matchs_ligue_1 = []
    matchs_autres = []

    print(f"[INFO] Recherche des 4 matchs pour semaine {semaine_id}...")

    # --- ETAPE 1 : RECUPERATION DES MATCHS PROGRAMMES ---
    for league in leagues:
        url = f'https://api.football-data.org/v4/competitions/{league}/matches?status=SCHEDULED'
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                matchs_api = data.get('matches', [])
                for m in matchs_api:
                    infos = {
                        'league': league,
                        'home': m['homeTeam']['name'],
                        'away': m['awayTeam']['name'],
                        'date': m['utcDate'],
                        'equilibre': random.uniform(0, 1)
                    }
                    if league == 'FL1':
                        matchs_ligue_1.append(infos)
                    else:
                        matchs_autres.append(infos)
        except Exception as e:
            print(f"[ERREUR] {league}: {e}")

    # --- ETAPE 2 : SECURITE ---
    if (len(matchs_ligue_1) + len(matchs_autres)) < 4:
        print("[WARN] Pas assez de matchs programmes. Elargissement...")
        url_secu = f'https://api.football-data.org/v4/competitions/FL1/matches'
        res = requests.get(url_secu, headers=headers)
        if res.status_code == 200:
            matchs_secu = res.json().get('matches', [])
            for m in matchs_secu[:10]:
                infos = {
                    'league': 'FL1',
                    'home': m['homeTeam']['name'],
                    'away': m['awayTeam']['name'],
                    'date': m['utcDate'],
                    'equilibre': random.uniform(0, 1)
                }
                if infos not in matchs_ligue_1:
                    matchs_ligue_1.append(infos)

    # --- LOGIQUE DE SELECTION ---
    random.shuffle(matchs_ligue_1)
    random.shuffle(matchs_autres)

    selection_finale = matchs_ligue_1[:4]

    if len(selection_finale) < 4:
        besoin = 4 - len(selection_finale)
        matchs_autres.sort(key=lambda x: x['equilibre'])
        selection_finale.extend(matchs_autres[:besoin])

    # --- ENREGISTREMENT ---
    for m in selection_finale:
        cote_h = round(random.uniform(2.10, 2.60), 2)
        cote_a = round(random.uniform(2.40, 3.10), 2)
        cote_n = round(random.uniform(3.00, 3.40), 2)

        cursor.execute('''
            INSERT INTO matches (saison_id, semaine_id, championnat, equipe_home, equipe_away,
                                cote_home, cote_draw, cote_away, date_match, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (saison_id, semaine_id, m['league'], m['home'], m['away'],
              cote_h, cote_n, cote_a, m['date']))

    conn.commit()
    conn.close()
    print(f"[OK] {len(selection_finale)} matchs enregistres pour semaine {semaine_id}")
    return len(selection_finale)


def sourcing_football_data():
    """Fonction legacy pour compatibilite"""
    return sourcing_semaine_courante()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        print("=== IMPORT CALENDRIER COMPLET ===")
        importer_calendrier_complet_l1()
    else:
        print("=== SOURCING SEMAINE COURANTE ===")
        sourcing_football_data()
        print("\nUtilisez --full pour importer le calendrier complet L1")
    