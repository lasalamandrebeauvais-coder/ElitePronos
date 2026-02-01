"""
Bot Sourcing pour Elite Pronos - Kingo
Selection intelligente des 4 matchs de la semaine
Regles:
1. Recuperer les matchs de la JOURNEE COURANTE depuis l'API
2. Prioriser: Derbys > Grosses affiches > 1 grand club > Autres
3. Generer des cotes equilibrees (ecart max 2.5)
4. Si pas assez de L1: max 1 match europeen
"""
import requests
import sqlite3
import random
import os
from datetime import datetime, timedelta

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Cle API Football-Data
API_TOKEN = 'bf58da6a49824f2a8742957b89ca52ee'

# Contrainte: ecart maximum entre cotes domicile et exterieur
MAX_ECART_COTES = 2.5

# === MEGA CLUBS : Toujours prioritaires quand ils jouent ===
MEGA_CLUBS = {
    'Paris Saint-Germain', 'Paris Saint-Germain FC', 'PSG',
    'Olympique de Marseille', 'Olympique Marseille', 'OM',
    'Olympique Lyonnais', 'Olympique Lyon', 'OL',
    'Real Madrid CF', 'FC Barcelona',
    'Manchester City FC', 'Liverpool FC',
    'FC Bayern München',
}

# === TOP 10 LIGUE 1 : Pour detecter les grosses affiches ===
# Mis a jour selon le classement 2024-2025
TOP_10_LIGUE_1 = {
    # 1. PSG
    'Paris Saint-Germain', 'Paris Saint-Germain FC', 'PSG',
    # 2. Marseille
    'Olympique de Marseille', 'Olympique Marseille', 'OM',
    # 3. Monaco
    'AS Monaco', 'AS Monaco FC', 'Monaco',
    # 4. Lille
    'LOSC Lille', 'Lille OSC', 'Lille',
    # 5. Lyon
    'Olympique Lyonnais', 'Olympique Lyon', 'OL',
    # 6. Nice
    'OGC Nice', 'Nice',
    # 7. Lens
    'RC Lens', 'Racing Club de Lens', 'Lens',
    # 8. Rennes
    'Stade Rennais', 'Stade Rennais FC 1901', 'Rennes',
    # 9. Brest
    'Stade Brestois 29', 'Stade Brestois', 'Brest',
    # 10. Strasbourg
    'RC Strasbourg Alsace', 'RC Strasbourg', 'Strasbourg',
}

# === GRANDS CLUBS : Pour detecter les grosses affiches (Top 10 L1 + Europe) ===
GRANDS_CLUBS = {
    # Top 10 Ligue 1 (inclus automatiquement)
    *TOP_10_LIGUE_1,
    # Premier League
    'Manchester United FC', 'Manchester City FC', 'Liverpool FC', 'Arsenal FC',
    'Chelsea FC', 'Tottenham Hotspur FC',
    # La Liga
    'Real Madrid CF', 'FC Barcelona', 'Atletico de Madrid',
    # Serie A
    'Juventus FC', 'AC Milan', 'FC Internazionale Milano', 'SSC Napoli', 'AS Roma',
    # Bundesliga
    'FC Bayern München', 'Borussia Dortmund', 'RB Leipzig', 'Bayer 04 Leverkusen'
}

# === DERBYS : Matchs a haute tension ===
DERBYS = [
    # France - Les classiques
    ('Paris Saint-Germain', 'Olympique de Marseille'),  # Le Classique
    ('Olympique Lyonnais', 'AS Saint-Etienne'),         # Derby du Rhone
    ('Olympique de Marseille', 'Olympique Lyonnais'),   # Olympico
    ('RC Lens', 'LOSC Lille'),                          # Derby du Nord
    ('Racing Club de Lens', 'Lille OSC'),               # Derby du Nord (API names)
    ('OGC Nice', 'AS Monaco'),                          # Derby de la Cote d'Azur
    # Angleterre
    ('Manchester United', 'Manchester City'),
    ('Liverpool FC', 'Everton FC'),
    ('Arsenal FC', 'Tottenham Hotspur'),
    # Espagne
    ('Real Madrid CF', 'FC Barcelona'),
    ('Real Madrid CF', 'Atletico de Madrid'),
    # Italie
    ('AC Milan', 'FC Internazionale Milano'),
    ('AS Roma', 'SS Lazio'),
    ('Juventus FC', 'Torino FC'),
    # Allemagne
    ('Borussia Dortmund', 'FC Schalke 04'),
    ('FC Bayern München', 'Borussia Dortmund'),
]


def est_mega_club(equipe):
    """Verifie si une equipe est un mega club (PSG, OM, OL, etc.)"""
    equipe_lower = equipe.lower()
    for club in MEGA_CLUBS:
        if club.lower() in equipe_lower or equipe_lower in club.lower():
            return True
    return False


def est_top10_ligue1(equipe):
    """Verifie si une equipe fait partie du Top 10 Ligue 1"""
    equipe_lower = equipe.lower()
    for club in TOP_10_LIGUE_1:
        if club.lower() in equipe_lower or equipe_lower in club.lower():
            return True
    return False


def est_grand_club(equipe):
    """Verifie si une equipe est un grand club (Top 10 L1 ou grand club europeen)"""
    equipe_lower = equipe.lower()
    for club in GRANDS_CLUBS:
        if club.lower() in equipe_lower or equipe_lower in club.lower():
            return True
    return False


def est_grosse_affiche(home, away):
    """Verifie si le match oppose 2 clubs du Top 10 Ligue 1"""
    return est_top10_ligue1(home) and est_top10_ligue1(away)


def est_derby(home, away):
    """Verifie si le match est un derby"""
    home_lower = home.lower()
    away_lower = away.lower()

    for team1, team2 in DERBYS:
        t1_lower = team1.lower()
        t2_lower = team2.lower()

        # Match dans les deux sens
        if (t1_lower in home_lower or home_lower in t1_lower) and \
           (t2_lower in away_lower or away_lower in t2_lower):
            return True
        if (t2_lower in home_lower or home_lower in t2_lower) and \
           (t1_lower in away_lower or away_lower in t1_lower):
            return True

    return False


def calculer_score_interet(home, away):
    """
    Calcule un score d'interet pour un match (plus c'est haut, plus c'est interessant)

    Priorites:
    - Derby: +1000
    - Mega club (PSG, OM, OL): +800
    - Grosse affiche (2 grands clubs): +500
    - 1 grand club: +200
    - Bonus aleatoire: 0-50
    """
    score = 0

    # Derby = priorite maximale
    if est_derby(home, away):
        score += 1000
        print(f"  [DERBY] {home} vs {away}")

    # Mega club = tres haute priorite (PSG, OM, OL, Real, Barca...)
    if est_mega_club(home) or est_mega_club(away):
        score += 800
        mega = home if est_mega_club(home) else away
        print(f"  [MEGA] {mega}")

    # Grosse affiche (2 grands clubs)
    elif est_grosse_affiche(home, away):
        score += 500
        print(f"  [AFFICHE] {home} vs {away}")

    # Match avec 1 grand club
    elif est_grand_club(home) or est_grand_club(away):
        score += 200
        top = home if est_grand_club(home) else away
        print(f"  [TOP] {top}")

    # Bonus aleatoire pour variete
    score += random.randint(0, 50)

    return score


def generer_cotes_equilibrees():
    """
    Genere des cotes realistes avec un ecart max de 2.5 entre home et away
    """
    cote_h = round(random.uniform(1.80, 3.50), 2)
    min_cote_a = max(1.80, cote_h - MAX_ECART_COTES)
    max_cote_a = min(4.50, cote_h + MAX_ECART_COTES)
    cote_a = round(random.uniform(min_cote_a, max_cote_a), 2)
    cote_n = round(random.uniform(3.00, 4.00), 2)
    return cote_h, cote_n, cote_a


def get_saison_actuelle():
    """Retourne l'ID de la saison actuelle"""
    # Importer depuis database_manager pour coherence
    try:
        from modules.database_manager import get_saison_actuelle as db_get_saison
        return db_get_saison()
    except:
        now = datetime.now()
        if now.month >= 8:
            return now.year
        return now.year - 1


def get_journee_courante_api():
    """
    Recupere la journee courante depuis l'API Football-Data
    = premiere journee avec des matchs SCHEDULED
    """
    headers = {'X-Auth-Token': API_TOKEN}
    url = 'https://api.football-data.org/v4/competitions/FL1/matches?status=SCHEDULED'

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matchs = data.get('matches', [])

            if matchs:
                # Trouver la plus petite journee avec des matchs programmes
                journees = set(m.get('matchday', 0) for m in matchs)
                return min(journees) if journees else 1
    except Exception as e:
        print(f"[ERREUR] API: {e}")

    return 1


def recuperer_matchs_journee(journee_id, saison_id=None):
    """
    Recupere les matchs d'une journee specifique depuis l'API
    Retourne une liste de matchs avec leur score d'interet
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    headers = {'X-Auth-Token': API_TOKEN}
    url = f'https://api.football-data.org/v4/competitions/FL1/matches?matchday={journee_id}&season={saison_id}'

    print(f"[API] Recuperation J{journee_id} saison {saison_id}...")

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"[ERREUR] API retourne {response.status_code}")
            return []

        data = response.json()
        matchs_api = data.get('matches', [])

        print(f"[API] {len(matchs_api)} matchs trouves pour J{journee_id}")

        matchs_avec_score = []
        for m in matchs_api:
            home = m['homeTeam']['name']
            away = m['awayTeam']['name']
            date = m.get('utcDate', '')
            status = m.get('status', 'SCHEDULED')

            # Ne prendre que les matchs programmes ou a venir
            if status not in ['SCHEDULED', 'TIMED']:
                continue

            score_interet = calculer_score_interet(home, away)

            matchs_avec_score.append({
                'home': home,
                'away': away,
                'date': date,
                'score_interet': score_interet,
                'league': 'FL1',
                'journee': journee_id
            })

        return matchs_avec_score

    except Exception as e:
        print(f"[ERREUR] Exception API: {e}")
        return []


def recuperer_matchs_europeens():
    """
    Recupere des matchs europeens interessants (backup si pas assez de L1)
    """
    headers = {'X-Auth-Token': API_TOKEN}
    leagues = ['PL', 'PD', 'SA', 'BL1']  # Premier League, La Liga, Serie A, Bundesliga
    matchs = []

    for league in leagues:
        url = f'https://api.football-data.org/v4/competitions/{league}/matches?status=SCHEDULED'

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                matchs_api = data.get('matches', [])[:5]  # Max 5 par ligue

                for m in matchs_api:
                    home = m['homeTeam']['name']
                    away = m['awayTeam']['name']
                    date = m.get('utcDate', '')

                    # Ne garder que les grosses affiches europeennes
                    if est_grosse_affiche(home, away) or est_derby(home, away):
                        score_interet = calculer_score_interet(home, away)
                        matchs.append({
                            'home': home,
                            'away': away,
                            'date': date,
                            'score_interet': score_interet,
                            'league': league,
                            'journee': 0
                        })
        except:
            continue

    return matchs


def selectionner_4_meilleurs_matchs(matchs_l1, matchs_euro=[]):
    """
    Selectionne les 4 matchs les plus interessants
    Priorite: L1, max 1 europeen si necessaire
    """
    # Trier L1 par score d'interet (decroissant)
    matchs_l1_tries = sorted(matchs_l1, key=lambda x: -x['score_interet'])

    selection = []

    # Prendre jusqu'a 4 matchs L1
    for m in matchs_l1_tries[:4]:
        selection.append(m)

    # Si moins de 4 L1, ajouter MAX 1 match europeen
    if len(selection) < 4 and matchs_euro:
        matchs_euro_tries = sorted(matchs_euro, key=lambda x: -x['score_interet'])
        # Ajouter max 1 europeen
        for m in matchs_euro_tries:
            if len(selection) >= 4:
                break
            if len([s for s in selection if s['league'] != 'FL1']) < 1:  # Max 1 europeen
                selection.append(m)

    return selection[:4]


def nettoyer_matchs_semaine(semaine_id, saison_id):
    """
    Supprime les anciens matchs de la semaine pour reimporter
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM matches
        WHERE semaine_id = ? AND saison_id = ?
    ''', (semaine_id, saison_id))

    nb_supprimes = cursor.rowcount
    conn.commit()
    conn.close()

    return nb_supprimes


def importer_matchs_selectionnes(matchs, semaine_id, saison_id):
    """
    Importe les matchs selectionnes dans la base de donnees
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    nb_importes = 0

    for m in matchs:
        # Generer des cotes equilibrees
        cote_h, cote_n, cote_a = generer_cotes_equilibrees()

        # Inserer le match
        cursor.execute('''
            INSERT INTO matches (saison_id, semaine_id, championnat, equipe_home, equipe_away,
                                cote_home, cote_draw, cote_away, date_match, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (saison_id, semaine_id, m['league'], m['home'], m['away'],
              cote_h, cote_n, cote_a, m['date']))

        nb_importes += 1

        # Log
        tag = ""
        if m['score_interet'] >= 1000:
            tag = " [DERBY]"
        elif m['score_interet'] >= 500:
            tag = " [AFFICHE]"
        elif m['score_interet'] >= 200:
            tag = " [TOP]"

        print(f"  -> {m['league']}: {m['home']} vs {m['away']}{tag}")
        print(f"     Cotes: {cote_h}/{cote_n}/{cote_a}")

    conn.commit()
    conn.close()

    return nb_importes


def sourcing_journee(journee_id=None, saison_id=None, force_reimport=False):
    """
    Fonction principale de sourcing pour une journee

    Etapes:
    1. Determiner la journee et saison
    2. Recuperer les matchs de cette journee depuis l'API
    3. Calculer le score d'interet de chaque match
    4. Selectionner les 4 meilleurs matchs
    5. Generer des cotes equilibrees
    6. Importer dans la base

    Args:
        journee_id: Numero de la journee (defaut: journee courante)
        saison_id: ID de la saison (defaut: saison actuelle)
        force_reimport: Si True, supprime et reimporte les matchs existants

    Returns:
        int: Nombre de matchs importes
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    if journee_id is None:
        journee_id = get_journee_courante_api()

    print(f"\n{'='*50}")
    print(f"KINGO BOT - SOURCING JOURNEE {journee_id}")
    print(f"Saison: {saison_id}-{saison_id+1}")
    print(f"{'='*50}")

    # Verifier si des matchs existent deja
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM matches
        WHERE semaine_id = ? AND saison_id = ? AND is_active = 1
    ''', (journee_id, saison_id))
    nb_existants = cursor.fetchone()[0]
    conn.close()

    if nb_existants > 0 and not force_reimport:
        print(f"[INFO] {nb_existants} matchs existent deja pour J{journee_id}")
        print("[INFO] Utilisez force_reimport=True pour reimporter")
        return 0

    if force_reimport and nb_existants > 0:
        nb_supprimes = nettoyer_matchs_semaine(journee_id, saison_id)
        print(f"[INFO] {nb_supprimes} anciens matchs supprimes")

    # Etape 1: Recuperer les matchs L1 de la journee
    print(f"\n[ETAPE 1] Recuperation matchs L1 J{journee_id}...")
    matchs_l1 = recuperer_matchs_journee(journee_id, saison_id)

    if not matchs_l1:
        print("[ERREUR] Aucun match L1 trouve pour cette journee")
        return 0

    # Etape 2: Recuperer matchs europeens (backup)
    print(f"\n[ETAPE 2] Recherche matchs europeens interessants...")
    matchs_euro = recuperer_matchs_europeens()
    print(f"[INFO] {len(matchs_euro)} matchs europeens interessants trouves")

    # Etape 3: Selection des 4 meilleurs
    print(f"\n[ETAPE 3] Selection des 4 meilleurs matchs...")
    selection = selectionner_4_meilleurs_matchs(matchs_l1, matchs_euro)

    if len(selection) < 4:
        print(f"[WARN] Seulement {len(selection)} matchs selectionnes")

    # Etape 4: Import dans la base
    print(f"\n[ETAPE 4] Import des matchs selectionnes...")
    nb_importes = importer_matchs_selectionnes(selection, journee_id, saison_id)

    print(f"\n{'='*50}")
    print(f"[OK] {nb_importes} matchs importes pour J{journee_id}")
    print(f"{'='*50}\n")

    return nb_importes


def sourcing_semaine_courante():
    """Alias pour compatibilite avec l'ancien code"""
    return sourcing_journee()


def sourcing_football_data():
    """Alias pour compatibilite avec l'ancien code"""
    return sourcing_journee()


def verifier_matchs_actifs():
    """
    Affiche les matchs actuellement actifs dans la base
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT saison_id, semaine_id, equipe_home, equipe_away,
               cote_home, cote_away, date_match
        FROM matches
        WHERE is_active = 1
        ORDER BY saison_id, semaine_id, date_match
    ''')

    matchs = cursor.fetchall()
    conn.close()

    print(f"\n=== {len(matchs)} MATCHS ACTIFS ===")
    for m in matchs:
        ecart = abs(m[4] - m[5])
        print(f"S{m[0]}-J{m[1]} | {m[2]} vs {m[3]} | Cotes: {m[4]}/{m[5]} (ecart: {ecart:.2f})")

    return matchs


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--force':
            print("=== REIMPORT FORCE ===")
            sourcing_journee(force_reimport=True)
        elif sys.argv[1] == '--check':
            verifier_matchs_actifs()
        elif sys.argv[1].isdigit():
            journee = int(sys.argv[1])
            print(f"=== SOURCING JOURNEE {journee} ===")
            sourcing_journee(journee_id=journee, force_reimport=True)
    else:
        print("=== KINGO BOT - SOURCING AUTOMATIQUE ===")
        sourcing_journee()
        print("\nOptions:")
        print("  --force : Reimporter meme si des matchs existent")
        print("  --check : Verifier les matchs actifs")
        print("  <numero> : Sourcer une journee specifique (ex: python bot_sourcing.py 19)")
