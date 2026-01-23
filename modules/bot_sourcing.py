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

# Contrainte: ecart maximum entre cotes domicile et exterieur
MAX_ECART_COTES = 2.5

# === GROSSES AFFICHES : Grands clubs europeens ===
GRANDS_CLUBS = {
    # Ligue 1
    'Paris Saint-Germain', 'Paris Saint-Germain FC', 'PSG',
    'Olympique de Marseille', 'Olympique Marseille', 'OM',
    'Olympique Lyonnais', 'Olympique Lyon', 'OL',
    'AS Monaco', 'Monaco FC',
    'LOSC Lille', 'Lille OSC',
    # Premier League
    'Manchester United', 'Manchester City', 'Liverpool FC', 'Arsenal FC',
    'Chelsea FC', 'Tottenham Hotspur',
    # La Liga
    'Real Madrid CF', 'Real Madrid', 'FC Barcelona', 'Barcelona',
    'Atletico Madrid', 'Atletico de Madrid',
    # Serie A
    'Juventus FC', 'Juventus', 'AC Milan', 'Inter Milan', 'FC Internazionale Milano',
    'AS Roma', 'SSC Napoli', 'Napoli',
    # Bundesliga
    'FC Bayern Munchen', 'Bayern Munich', 'Borussia Dortmund', 'BVB',
    'RB Leipzig', 'Bayer Leverkusen'
}

# === DERBYS : Rivalites regionales ===
DERBYS = [
    # France
    ('Paris Saint-Germain', 'Olympique de Marseille'),  # Le Classique
    ('Olympique Lyonnais', 'AS Saint-Etienne'),         # Derby du Rhone
    ('Olympique de Marseille', 'Olympique Lyonnais'),   # Olympico
    ('RC Lens', 'LOSC Lille'),                          # Derby du Nord
    ('OGC Nice', 'AS Monaco'),                          # Derby de la Cote d'Azur
    ('Girondins de Bordeaux', 'Toulouse FC'),           # Derby du Sud-Ouest
    # Angleterre
    ('Manchester United', 'Manchester City'),           # Manchester Derby
    ('Liverpool FC', 'Everton FC'),                     # Merseyside Derby
    ('Arsenal FC', 'Tottenham Hotspur'),                # North London Derby
    # Espagne
    ('Real Madrid CF', 'FC Barcelona'),                 # El Clasico
    ('Real Madrid CF', 'Atletico Madrid'),              # Derby de Madrid
    # Italie
    ('AC Milan', 'FC Internazionale Milano'),           # Derby della Madonnina
    ('AS Roma', 'SS Lazio'),                            # Derby della Capitale
    ('Juventus FC', 'Torino FC'),                       # Derby della Mole
    # Allemagne
    ('Borussia Dortmund', 'FC Schalke 04'),             # Revierderby
    ('FC Bayern Munchen', 'Borussia Dortmund'),         # Der Klassiker
]


def est_grosse_affiche(home, away):
    """Verifie si le match est une grosse affiche (2 grands clubs)"""
    home_grand = any(club.lower() in home.lower() for club in GRANDS_CLUBS)
    away_grand = any(club.lower() in away.lower() for club in GRANDS_CLUBS)
    return home_grand and away_grand


def est_derby(home, away):
    """Verifie si le match est un derby"""
    for team1, team2 in DERBYS:
        if (team1.lower() in home.lower() and team2.lower() in away.lower()) or \
           (team2.lower() in home.lower() and team1.lower() in away.lower()):
            return True
    return False


def generer_cotes_equilibrees():
    """
    Genere des cotes realistes avec un ecart max de 2.5 entre home et away
    Retourne: (cote_home, cote_draw, cote_away)
    """
    # Generer cote domicile
    cote_h = round(random.uniform(1.80, 3.50), 2)

    # Generer cote exterieur avec contrainte d'ecart max 2.5
    min_cote_a = max(1.80, cote_h - MAX_ECART_COTES)
    max_cote_a = min(4.50, cote_h + MAX_ECART_COTES)
    cote_a = round(random.uniform(min_cote_a, max_cote_a), 2)

    # Cote nul (generalement entre 3.00 et 4.00)
    cote_n = round(random.uniform(3.00, 4.00), 2)

    return cote_h, cote_n, cote_a


def valider_et_corriger_cotes():
    """
    Verifie tous les matchs actifs et corrige ceux avec ecart > MAX_ECART_COTES
    Retourne le nombre de matchs corriges
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Trouver les matchs avec ecart trop grand
    cursor.execute('''
        SELECT id, equipe_home, equipe_away, cote_home, cote_away
        FROM matches
        WHERE is_active = 1 AND ABS(cote_home - cote_away) > ?
    ''', (MAX_ECART_COTES,))

    matchs_invalides = cursor.fetchall()
    nb_corriges = 0

    for match in matchs_invalides:
        match_id, home, away, cote_h, cote_a = match

        # Generer de nouvelles cotes equilibrees
        nouvelle_cote_h, nouvelle_cote_n, nouvelle_cote_a = generer_cotes_equilibrees()

        cursor.execute('''
            UPDATE matches
            SET cote_home = ?, cote_draw = ?, cote_away = ?
            WHERE id = ?
        ''', (nouvelle_cote_h, nouvelle_cote_n, nouvelle_cote_a, match_id))

        print(f"[CORRIGE] {home} vs {away}: {cote_h}/{cote_a} -> {nouvelle_cote_h}/{nouvelle_cote_a}")
        nb_corriges += 1

    conn.commit()
    conn.close()

    return nb_corriges


def selectionner_4_matchs_valides():
    """
    S'assure qu'il y a exactement 4 matchs actifs avec ecart <= MAX_ECART_COTES
    Desactive les matchs en surplus ou avec ecart invalide
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # D'abord corriger les cotes invalides
    valider_et_corriger_cotes()

    # Recuperer tous les matchs actifs tries par ecart
    cursor.execute('''
        SELECT id, equipe_home, equipe_away, cote_home, cote_away,
               ABS(cote_home - cote_away) as ecart
        FROM matches
        WHERE is_active = 1
        ORDER BY ecart ASC
    ''')

    matchs = cursor.fetchall()

    # Filtrer les matchs valides (ecart <= 2.5)
    matchs_valides = [m for m in matchs if m[5] <= MAX_ECART_COTES]

    # Garder seulement les 4 premiers
    matchs_gardes = matchs_valides[:4]
    ids_gardes = [m[0] for m in matchs_gardes]

    # Desactiver tous les autres
    if ids_gardes:
        cursor.execute(f'''
            UPDATE matches SET is_active = 0
            WHERE is_active = 1 AND id NOT IN ({','.join(map(str, ids_gardes))})
        ''')
        nb_desactives = cursor.rowcount
    else:
        nb_desactives = 0

    conn.commit()
    conn.close()

    print(f"[INFO] {len(matchs_gardes)} matchs gardes, {nb_desactives} desactives")
    return len(matchs_gardes)


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
            # Calculer la priorite pour chaque match (derbys > affiches > autres)
            matchs_avec_priorite = []
            for m in matchs_journee:
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                score = 0
                if est_derby(home, away):
                    score += 100
                if est_grosse_affiche(home, away):
                    score += 50
                matchs_avec_priorite.append((m, score))

            # Trier par priorite puis selectionner 4 matchs
            matchs_avec_priorite.sort(key=lambda x: (-x[1], random.random()))
            matchs_tries = [m[0] for m in matchs_avec_priorite[:4]]

            for m in matchs_tries:
                # Generer des cotes equilibrees (ecart max 2.5 entre home et away)
                cote_h, cote_n, cote_a = generer_cotes_equilibrees()

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
    Regles:
    - Priorite Ligue 1 (4 matchs max)
    - Ecart max 2.5 entre cotes domicile/exterieur
    - Priorite aux grosses affiches et derbys
    - Si pas assez de L1: max 1 match europeen
    """
    saison_id = get_saison_actuelle()

    if semaine_id is None:
        semaine_id = datetime.now().isocalendar()[1]

    leagues = ['FL1', 'PL', 'PD', 'SA', 'BL1']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    headers = {'X-Auth-Token': API_TOKEN}
    matchs_ligue_1 = []
    matchs_europeens = []

    print(f"[INFO] Recherche des 4 matchs pour semaine {semaine_id}...")
    print(f"[INFO] Regles: Priorite L1, ecart cotes max {MAX_ECART_COTES}, grosses affiches/derbys")

    # --- ETAPE 1 : RECUPERATION DES MATCHS PROGRAMMES ---
    for league in leagues:
        url = f'https://api.football-data.org/v4/competitions/{league}/matches?status=SCHEDULED'
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                matchs_api = data.get('matches', [])
                for m in matchs_api:
                    home = m['homeTeam']['name']
                    away = m['awayTeam']['name']

                    # Calculer le score de priorite
                    score_priorite = 0
                    if est_derby(home, away):
                        score_priorite += 100  # Derbys en priorite absolue
                        print(f"[DERBY] {home} vs {away}")
                    if est_grosse_affiche(home, away):
                        score_priorite += 50   # Grosses affiches ensuite
                        print(f"[AFFICHE] {home} vs {away}")

                    infos = {
                        'league': league,
                        'home': home,
                        'away': away,
                        'date': m['utcDate'],
                        'priorite': score_priorite,
                        'is_derby': est_derby(home, away),
                        'is_affiche': est_grosse_affiche(home, away)
                    }

                    if league == 'FL1':
                        matchs_ligue_1.append(infos)
                    else:
                        matchs_europeens.append(infos)
        except Exception as e:
            print(f"[ERREUR] {league}: {e}")

    # --- ETAPE 2 : SECURITE ---
    if len(matchs_ligue_1) < 3:
        print("[WARN] Pas assez de matchs L1 programmes. Elargissement...")
        url_secu = f'https://api.football-data.org/v4/competitions/FL1/matches'
        res = requests.get(url_secu, headers=headers)
        if res.status_code == 200:
            matchs_secu = res.json().get('matches', [])
            for m in matchs_secu[:10]:
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                infos = {
                    'league': 'FL1',
                    'home': home,
                    'away': away,
                    'date': m['utcDate'],
                    'priorite': 100 if est_derby(home, away) else (50 if est_grosse_affiche(home, away) else 0),
                    'is_derby': est_derby(home, away),
                    'is_affiche': est_grosse_affiche(home, away)
                }
                # Eviter les doublons
                if not any(x['home'] == home and x['away'] == away for x in matchs_ligue_1):
                    matchs_ligue_1.append(infos)

    # --- ETAPE 3 : LOGIQUE DE SELECTION ---
    # Trier L1 par priorite (derbys > affiches > autres)
    matchs_ligue_1.sort(key=lambda x: (-x['priorite'], random.random()))

    # Prendre jusqu'a 4 matchs L1
    selection_finale = matchs_ligue_1[:4]
    print(f"[INFO] {len(selection_finale)} matchs L1 selectionnes")

    # Si moins de 4 L1: ajouter MAX 1 match europeen (priorite affiches/derbys)
    if len(selection_finale) < 4:
        besoin = min(1, 4 - len(selection_finale))  # MAX 1 match europeen
        matchs_europeens.sort(key=lambda x: (-x['priorite'], random.random()))
        matchs_euro_selection = matchs_europeens[:besoin]
        selection_finale.extend(matchs_euro_selection)
        if matchs_euro_selection:
            print(f"[INFO] +{len(matchs_euro_selection)} match(s) europeen(s) ajoute(s)")

    # --- ETAPE 4 : ENREGISTREMENT ---
    for m in selection_finale:
        # Generer des cotes equilibrees (ecart max 2.5 entre home et away)
        cote_h, cote_n, cote_a = generer_cotes_equilibrees()

        cursor.execute('''
            INSERT INTO matches (saison_id, semaine_id, championnat, equipe_home, equipe_away,
                                cote_home, cote_draw, cote_away, date_match, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (saison_id, semaine_id, m['league'], m['home'], m['away'],
              cote_h, cote_n, cote_a, m['date']))

        # Log du match
        tag = ""
        if m.get('is_derby'):
            tag = " [DERBY]"
        elif m.get('is_affiche'):
            tag = " [AFFICHE]"
        print(f"  -> {m['league']}: {m['home']} vs {m['away']}{tag}")

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
    