"""
Script d'automatisation Elite Pronos
- Recupere les scores des matchs termines depuis l'API
- Met a jour Supabase
- Calcule les points automatiquement
- Execution via GitHub Actions (cron)
"""

import requests
import os
import random
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Configuration Supabase (fallback si secret GitHub vide)
_DEFAULT_URL = "https://qyyfxbwyvshpuuqwrxsl.supabase.co"
_DEFAULT_KEY = "sb_secret_v_cT_G2XV1znRhrS0cx_qw_6vZmzMKW"
_DEFAULT_TOKEN = "bf58da6a49824f2a8742957b89ca52ee"

SUPABASE_URL = os.getenv("SUPABASE_URL") or _DEFAULT_URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or _DEFAULT_KEY
FOOTBALL_API_TOKEN = os.getenv("FOOTBALL_API_TOKEN") or _DEFAULT_TOKEN

# Headers
SUPABASE_HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

FOOTBALL_HEADERS = {
    'X-Auth-Token': FOOTBALL_API_TOKEN
}


def get_saison_actuelle():
    """Retourne la saison actuelle (2025 pour 2025-2026)"""
    now = datetime.now()
    if now.month >= 8:
        return now.year
    return now.year - 1


def get_journee_courante(saison_id):
    """Recupere la journee courante depuis la table saisons"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/saisons?annee_debut=eq.{saison_id}&select=journee_courante",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200 and response.json():
        return response.json()[0]['journee_courante']
    return None


def get_matchs_supabase(semaine_id, saison_id):
    """Recupere les matchs de la journee depuis Supabase"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,equipe_home,equipe_away,score_final_home,score_final_away,cote_home,cote_draw,cote_away,date_match",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200:
        return response.json()
    return []


def get_matchs_api(semaine_id, saison_id):
    """Recupere les matchs depuis l'API Football-Data"""
    url = f'https://api.football-data.org/v4/competitions/FL1/matches?season={saison_id}&matchday={semaine_id}'
    response = requests.get(url, headers=FOOTBALL_HEADERS)
    if response.status_code == 200:
        return response.json().get('matches', [])
    print(f"Erreur API Football-Data: {response.status_code}")
    return []


def match_equipes(api_name, db_name):
    """Verifie si deux noms d'equipes correspondent"""
    if not api_name or not db_name:
        return False
    return api_name.lower() in db_name.lower() or db_name.lower() in api_name.lower()


def update_score_supabase(match_id, score_home, score_away):
    """Met a jour le score d'un match dans Supabase"""
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/matches?id=eq.{match_id}",
        headers=SUPABASE_HEADERS,
        json={
            'score_final_home': score_home,
            'score_final_away': score_away,
            'status': 'FINISHED'
        }
    )
    return response.status_code < 400


def update_live_supabase(match_id, score_home, score_away, status):
    """Met a jour le score en direct et le status d'un match"""
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/matches?id=eq.{match_id}",
        headers=SUPABASE_HEADERS,
        json={
            'score_mi_temps_home': score_home,
            'score_mi_temps_away': score_away,
            'status': status
        }
    )
    return response.status_code < 400


def reset_predictions_points(match_id):
    """Reset les points des predictions pour un match"""
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=eq.{match_id}",
        headers=SUPABASE_HEADERS,
        json={
            'points_gagnes': None,
            'is_score_exact': None
        }
    )
    return response.status_code < 400


def get_jokers_double(semaine_id):
    """Recupere les utilisateurs avec joker DOUBLE actif"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/jokers_historique?semaine_id=eq.{semaine_id}&type_joker=eq.DOUBLE&select=utilisateur_id",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200:
        return {j['utilisateur_id'] for j in response.json()}
    return set()


def get_jokers_vol(semaine_id):
    """Recupere les jokers VOL actifs avec leur cible"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/jokers_historique?semaine_id=eq.{semaine_id}&type_joker=eq.VOL&select=utilisateur_id,cible_vol_id",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200:
        return {j['utilisateur_id']: j['cible_vol_id'] for j in response.json() if j.get('cible_vol_id')}
    return {}


def get_users_grand_chelem_precedente(semaine_id, saison_id):
    """
    Retourne les user_ids qui ont fait un Grand Chelem (4/4 1N2 corrects) la semaine precedente.
    """
    semaine_prec = semaine_id - 1
    if semaine_prec < 1:
        return set()

    # Recuperer les matchs termines de la semaine precedente (sans filtre is_active)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_prec}&saison_id=eq.{saison_id}&score_final_home=not.is.null&select=id,score_final_home,score_final_away",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200:
        return set()

    matchs_prec = response.json()
    if len(matchs_prec) < 4:
        return set()

    all_match_ids = [m['id'] for m in matchs_prec]
    matchs_dict = {m['id']: (m['score_final_home'], m['score_final_away']) for m in matchs_prec}

    # Filtrer sur les matchs actifs (ceux sur lesquels Kingo a pronostique)
    kingo_id = get_kingo_user_id()
    if kingo_id:
        all_ids_str = ','.join(map(str, all_match_ids))
        resp_kingo = requests.get(
            f"{SUPABASE_URL}/rest/v1/predictions?user_id=eq.{kingo_id}&match_id=in.({all_ids_str})&select=match_id",
            headers=SUPABASE_HEADERS
        )
        if resp_kingo.status_code == 200 and resp_kingo.json():
            match_ids = [p['match_id'] for p in resp_kingo.json()]
        else:
            match_ids = all_match_ids
    else:
        match_ids = all_match_ids

    if len(match_ids) < 4:
        return set()

    # Recuperer toutes les predictions de ces matchs
    match_ids_str = ','.join(map(str, match_ids))
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=in.({match_ids_str})&select=user_id,match_id,score_prono_home,score_prono_away",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200:
        return set()

    predictions = response.json()

    # Compter les 1N2 corrects par user
    user_corrects = {}
    for pred in predictions:
        user_id = pred['user_id']
        match_id = pred['match_id']

        if match_id not in matchs_dict:
            continue

        score_h, score_a = matchs_dict[match_id]
        prono_h = pred['score_prono_home']
        prono_a = pred['score_prono_away']

        bon_resultat = (
            (prono_h > prono_a and score_h > score_a) or
            (prono_h < prono_a and score_h < score_a) or
            (prono_h == prono_a and score_h == score_a)
        )

        if bon_resultat:
            user_corrects[user_id] = user_corrects.get(user_id, 0) + 1

    # Retourner les users avec 4/4 corrects
    return {uid for uid, count in user_corrects.items() if count >= 4}


def get_predictions_match(match_id):
    """Recupere les predictions pour un match"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=eq.{match_id}&points_gagnes=is.null&select=id,user_id,score_prono_home,score_prono_away,mise_points",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200:
        return response.json()
    return []


def update_prediction_points(pred_id, points, is_exact):
    """Met a jour les points d'une prediction"""
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/predictions?id=eq.{pred_id}",
        headers=SUPABASE_HEADERS,
        json={
            'points_gagnes': points,
            'is_score_exact': is_exact
        }
    )
    return response.status_code < 400


def calculer_points(match, users_double):
    """Calcule les points pour toutes les predictions d'un match"""
    BONUS_EXACT = 10

    match_id = match['id']
    score_h = match['score_final_home']
    score_a = match['score_final_away']
    cote_home = match.get('cote_home') or 2.0
    cote_draw = match.get('cote_draw') or 3.0
    cote_away = match.get('cote_away') or 2.0

    predictions = get_predictions_match(match_id)
    updates = 0

    for pred in predictions:
        user_id = pred['user_id']
        prono_h = pred['score_prono_home']
        prono_a = pred['score_prono_away']
        mise = pred['mise_points']

        # Determiner la cote selon le prono
        if prono_h > prono_a:
            cote = cote_home
        elif prono_h < prono_a:
            cote = cote_away
        else:
            cote = cote_draw

        # Verifier si bon resultat (1N2)
        bon_resultat = (
            (prono_h > prono_a and score_h > score_a) or
            (prono_h < prono_a and score_h < score_a) or
            (prono_h == prono_a and score_h == score_a)
        )

        points = 0
        is_exact = False

        if bon_resultat:
            points = round(mise * cote, 1)
            if prono_h == score_h and prono_a == score_a:
                points += BONUS_EXACT
                is_exact = True
        else:
            points = -mise

        # Joker DOUBLE
        if user_id in users_double:
            points = points * 2

        update_prediction_points(pred['id'], points, is_exact)
        updates += 1

    return updates


def recalculer_points_complet(semaine_id, saison_id):
    """
    Recalcule les points pour TOUTES les predictions de la semaine.
    Gere: base, DOUBLE, VOL, Grand Chelem.
    Remplace calculer_points() qui ne gerait que base + DOUBLE.
    """
    BONUS_EXACT = 10

    # Recuperer les jokers
    users_double = get_jokers_double(semaine_id)
    vol_cibles = get_jokers_vol(semaine_id)

    print(f"Jokers DOUBLE: {len(users_double)}, VOL: {len(vol_cibles)}")

    # Recuperer les matchs termines avec cotes (sans filtre is_active car il passe a False apres validation)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&score_final_home=not.is.null&select=id,score_final_home,score_final_away,cote_home,cote_draw,cote_away",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200:
        print("Erreur recuperation matchs termines")
        return 0

    matchs = response.json()
    if not matchs:
        print("Aucun match termine")
        return 0

    match_ids = [m['id'] for m in matchs]
    match_map = {m['id']: m for m in matchs}
    match_ids_str = ','.join(map(str, match_ids))

    # Recuperer TOUTES les predictions (pas seulement points_gagnes=null)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=in.({match_ids_str})&select=id,user_id,match_id,score_prono_home,score_prono_away,mise_points,points_gagnes",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200:
        print("Erreur recuperation predictions")
        return 0

    all_predictions = response.json()

    # Organiser par user et par match
    preds_by_user = {}
    for p in all_predictions:
        uid = p['user_id']
        mid = p['match_id']
        if uid not in preds_by_user:
            preds_by_user[uid] = {}
        preds_by_user[uid][mid] = p

    total_updates = 0

    for user_id in preds_by_user:
        user_preds = preds_by_user[user_id]

        # Verifier si cet utilisateur a un joker VOL
        cible_id = vol_cibles.get(user_id)
        cible_preds = preds_by_user.get(cible_id, {}) if cible_id else {}

        for match_id, pred in user_preds.items():
            match = match_map.get(match_id)
            if not match:
                continue

            score_h = match['score_final_home']
            score_a = match['score_final_away']
            cote_home = match.get('cote_home') or 2.0
            cote_draw = match.get('cote_draw') or 3.0
            cote_away = match.get('cote_away') or 2.0

            # Si VOL actif et cible a un prono pour ce match, utiliser les pronos de la cible
            if cible_id and match_id in cible_preds:
                cible_pred = cible_preds[match_id]
                prono_h = cible_pred['score_prono_home']
                prono_a = cible_pred['score_prono_away']
                mise = cible_pred['mise_points'] or 25
            else:
                prono_h = pred['score_prono_home']
                prono_a = pred['score_prono_away']
                mise = pred['mise_points'] or 25

            # Determiner la cote selon le prono
            if prono_h > prono_a:
                cote = cote_home
            elif prono_h < prono_a:
                cote = cote_away
            else:
                cote = cote_draw

            # Verifier si bon resultat (1N2)
            bon_resultat = (
                (prono_h > prono_a and score_h > score_a) or
                (prono_h < prono_a and score_h < score_a) or
                (prono_h == prono_a and score_h == score_a)
            )

            points = 0
            is_exact = False

            if bon_resultat:
                points = round(mise * cote, 1)
                if prono_h == score_h and prono_a == score_a:
                    points += BONUS_EXACT
                    is_exact = True
            else:
                points = -mise

            # Joker DOUBLE: x2 sur gains ET pertes
            if user_id in users_double:
                points = points * 2

            # Mettre a jour seulement si le score a change
            old_points = pred.get('points_gagnes')
            if old_points != points:
                update_prediction_points(pred['id'], points, is_exact)
                total_updates += 1

    if vol_cibles:
        print(f"VOL applique a {len(vol_cibles)} joueur(s)")

    return total_updates


def get_kingo_user_id():
    """Retourne l'ID de Kingo"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/utilisateurs?pseudo=eq.Kingo&select=id",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200 and response.json():
        return response.json()[0]['id']
    return None


def check_journee_terminee(semaine_id, saison_id):
    """Verifie si tous les matchs actifs de la journee sont termines.
    Utilise les predictions de Kingo pour determiner les matchs actifs."""
    # Recuperer l'ID de Kingo
    kingo_id = get_kingo_user_id()
    if not kingo_id:
        return False

    # Recuperer tous les matchs de la semaine
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,score_final_home",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200:
        return False

    all_matchs = response.json()
    if not all_matchs:
        return False

    all_match_ids = [m['id'] for m in all_matchs]
    match_map = {m['id']: m for m in all_matchs}

    # Les matchs actifs = ceux sur lesquels Kingo a pronostique
    match_ids_str = ','.join(map(str, all_match_ids))
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?user_id=eq.{kingo_id}&match_id=in.({match_ids_str})&select=match_id",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200:
        return False

    kingo_match_ids = [p['match_id'] for p in response.json()]
    if not kingo_match_ids:
        return False

    # Verifier que tous les matchs de Kingo ont un score final
    return all(
        match_map.get(mid, {}).get('score_final_home') is not None
        for mid in kingo_match_ids
    )


def cloturer_journee(semaine_id, saison_id):
    """Cloture une journee terminee et passe a la suivante"""
    print(f"Cloture de la journee {semaine_id}...")

    # 1. Desactiver les matchs de la journee terminee
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}",
        headers=SUPABASE_HEADERS,
        json={'is_active': False}
    )

    # 2. Incrementer journee_courante dans saisons
    nouvelle_journee = semaine_id + 1
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/saisons?annee_debut=eq.{saison_id}",
        headers=SUPABASE_HEADERS,
        json={'journee_courante': nouvelle_journee}
    )

    print(f"Journee avancee a {nouvelle_journee}")

    # 3. Creer les matchs de la nouvelle journee
    creer_matchs_journee(nouvelle_journee, saison_id)

    return nouvelle_journee


def creer_matchs_journee(semaine_id, saison_id):
    """
    Importe les matchs de la journee:
    - Tous les matchs Ligue 1
    - 11 meilleurs matchs etrangers (PL, La Liga, Serie A, Bundesliga)
    Tous avec is_active=false (selection manuelle admin)
    """
    import random
    from datetime import datetime, timedelta

    print(f"Import des matchs pour J{semaine_id}...")

    # Verifier si des matchs existent deja
    existing = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id",
        headers=SUPABASE_HEADERS
    )
    if existing.status_code == 200 and existing.json():
        print(f"Matchs J{semaine_id} deja existants ({len(existing.json())} matchs)")
        return

    # === CONFIGURATION ===
    CHAMPIONNATS = {'PL': 'Premier League', 'PD': 'La Liga', 'SA': 'Serie A', 'BL1': 'Bundesliga'}

    MEGA_CLUBS = {
        'Paris Saint-Germain', 'Olympique de Marseille', 'Olympique Lyonnais',
        'Real Madrid', 'FC Barcelona', 'Atletico Madrid',
        'Manchester United', 'Manchester City', 'Liverpool', 'Arsenal', 'Chelsea', 'Tottenham',
        'Juventus', 'AC Milan', 'Inter Milan', 'AS Roma', 'SSC Napoli',
        'Bayern Munich', 'Borussia Dortmund'
    }

    DERBIES = [
        ('Paris Saint-Germain', 'Olympique de Marseille'),  # Le Classique
        ('Olympique Lyonnais', 'AS Saint-Etienne'),  # Derby du Rhone
        ('Racing Club de Lens', 'Lille'),  # Derby du Nord
        ('OGC Nice', 'AS Monaco'),  # Derby Cote d'Azur
        ('Real Madrid', 'FC Barcelona'), ('Real Madrid', 'Atletico Madrid'),
        ('Manchester United', 'Manchester City'), ('Manchester United', 'Liverpool'),
        ('Arsenal', 'Tottenham'), ('Arsenal', 'Chelsea'),
        ('AC Milan', 'Inter Milan'), ('Juventus', 'Inter Milan'),
        ('AS Roma', 'SS Lazio'), ('Bayern Munich', 'Borussia Dortmund'),
    ]

    TOP_CLUBS = {
        'FL1': {'Paris Saint-Germain', 'Olympique de Marseille', 'AS Monaco', 'Lille', 'Olympique Lyonnais',
                'OGC Nice', 'Racing Club de Lens', 'Stade Rennais', 'Stade Brestois', 'RC Strasbourg'},
        'PL': {'Manchester City', 'Arsenal', 'Liverpool', 'Chelsea', 'Manchester United', 'Tottenham', 'Newcastle'},
        'PD': {'Real Madrid', 'FC Barcelona', 'Atletico Madrid', 'Athletic Bilbao', 'Real Sociedad', 'Sevilla'},
        'SA': {'Inter Milan', 'AC Milan', 'Juventus', 'SSC Napoli', 'AS Roma', 'SS Lazio', 'Atalanta'},
        'BL1': {'Bayern Munich', 'Borussia Dortmund', 'RB Leipzig', 'Bayer Leverkusen', 'Eintracht Frankfurt'}
    }

    def score_match(m, code):
        home = m.get('homeTeam', {}).get('name', '')
        away = m.get('awayTeam', {}).get('name', '')
        score = 0
        for d1, d2 in DERBIES:
            if (d1 in home and d2 in away) or (d2 in home and d1 in away):
                score += 2000
                break
        for mc in MEGA_CLUBS:
            if mc in home or mc in away:
                score += 1000
                break
        top = TOP_CLUBS.get(code, set())
        if any(t in home for t in top) and any(t in away for t in top):
            score += 500
        return score

    all_matchs = []

    # === 1. MATCHS LIGUE 1 ===
    matchs_l1 = get_matchs_api(semaine_id, saison_id)
    if matchs_l1:
        for m in matchs_l1:
            all_matchs.append({
                'championnat': 'Ligue 1',
                'equipe_home': m.get('homeTeam', {}).get('name', ''),
                'equipe_away': m.get('awayTeam', {}).get('name', ''),
                'date_match': m.get('utcDate', ''),
                'score': score_match(m, 'FL1')  # Scoring L1 aussi
            })
        print(f"  {len(matchs_l1)} matchs Ligue 1")

    # === 2. MATCHS ETRANGERS ===
    # Determiner la periode (dates des matchs L1)
    if matchs_l1:
        dates = [m.get('utcDate', '')[:10] for m in matchs_l1 if m.get('utcDate')]
        if dates:
            dt_min = datetime.strptime(min(dates), '%Y-%m-%d') - timedelta(days=1)
            dt_max = datetime.strptime(max(dates), '%Y-%m-%d') + timedelta(days=1)
            date_from = dt_min.strftime('%Y-%m-%d')
            date_to = dt_max.strftime('%Y-%m-%d')
        else:
            today = datetime.now()
            date_from = (today - timedelta(days=3)).strftime('%Y-%m-%d')
            date_to = (today + timedelta(days=4)).strftime('%Y-%m-%d')
    else:
        today = datetime.now()
        date_from = (today - timedelta(days=3)).strftime('%Y-%m-%d')
        date_to = (today + timedelta(days=4)).strftime('%Y-%m-%d')

    matchs_etrangers = []
    for code, nom in CHAMPIONNATS.items():
        url = f'https://api.football-data.org/v4/competitions/{code}/matches?dateFrom={date_from}&dateTo={date_to}'
        resp = requests.get(url, headers=FOOTBALL_HEADERS)
        if resp.status_code == 200:
            for m in resp.json().get('matches', []):
                if m.get('status') != 'FINISHED':
                    matchs_etrangers.append({
                        'championnat': nom,
                        'equipe_home': m.get('homeTeam', {}).get('name', ''),
                        'equipe_away': m.get('awayTeam', {}).get('name', ''),
                        'date_match': m.get('utcDate', ''),
                        'score': score_match(m, code)
                    })

    # Trier etrangers et prendre top 11
    matchs_etrangers.sort(key=lambda x: x['score'], reverse=True)
    all_matchs.extend(matchs_etrangers[:11])
    print(f"  {len(matchs_etrangers[:11])} matchs etrangers selectionnes")

    # Trier TOUS les matchs par score pour determiner les 4 meilleurs
    all_matchs.sort(key=lambda x: x['score'], reverse=True)

    # === 3. IMPORT SUPABASE ===
    count = 0
    for i, m in enumerate(all_matchs):
        cote_h = round(random.uniform(1.5, 3.5), 2)
        cote_n = round(random.uniform(3.0, 4.0), 2)
        cote_a = round(random.uniform(1.8, 4.0), 2)

        # Les 4 premiers sont actifs par defaut
        is_active = (i < 4)
        status_txt = "ACTIF" if is_active else ""

        requests.post(
            f"{SUPABASE_URL}/rest/v1/matches",
            headers=SUPABASE_HEADERS,
            json={
                'saison_id': saison_id,
                'semaine_id': semaine_id,
                'championnat': m['championnat'],
                'equipe_home': m['equipe_home'],
                'equipe_away': m['equipe_away'],
                'cote_home': cote_h,
                'cote_draw': cote_n,
                'cote_away': cote_a,
                'date_match': m['date_match'],
                'is_active': is_active
            }
        )
        print(f"  -> [{m['championnat']}] {m['equipe_home']} vs {m['equipe_away']} {status_txt}")
        count += 1

    print(f"{count} matchs importes pour J{semaine_id} (4 actifs par defaut)")


# ============================================
# RAPPEL RETARDATAIRES (H-4 avant deadline)
# ============================================

PHRASES_KINGO_RETARDATAIRES = [
    "Tu sais que meme un poulpe ferait ses pronos plus vite que toi ? Et il a 8 bras pour trouver des excuses.",
    "Allo ? Y'a quelqu'un ? J'ai cru voir une tumbleweed passer devant tes pronostics vides...",
    "Je commence a croire que tu attends que les matchs soient finis pour pronostiquer. Strategie audacieuse.",
    "Meme mon algorithme a eu le temps de faire ses pronos, prendre un cafe et ecrire un roman. Toi ? Rien. Nada. Le vide.",
    "ALERTE DISPARITION : Les pronostics de {pseudo} n'ont toujours pas ete retrouves. Si vous avez des informations, contactez Elite Pronos.",
    "Tu sais ce qui est plus vide que tes pronostics ? Rien. Absolument rien.",
    "J'ai verifie 3 fois. Puis 4. Puis 5. Toujours aucun prono de ta part. Tu testes ma patience ou quoi ?",
    "On m'a dit que tu avais une excuse. Et puis finalement non. Meme pas une excuse.",
    "Les autres ont deja pronos, joker, et se la coulent douce. Et toi ? Tu fais quoi la exactement ?",
    "Je suis un bot et meme MOI j'ai plus d'instinct football que quelqu'un qui ne pronostique pas.",
    "Tick-tock, tick-tock... Tu entends ca ? C'est le son de la deadline qui se rapproche pendant que tu ne fais RIEN.",
    "Fun fact : 100% des joueurs qui ne font pas leurs pronos finissent avec mes pronos a moi. Et crois-moi, je suis genereux... mais pas gentil.",
    "Si l'oubli etait un sport olympique, tu serais deja triple champion du monde.",
    "Je ne dis pas que tu es en retard... mais meme l'escargot de la Journee 1 est arrive avant toi.",
    "BREAKING NEWS : {pseudo} est officiellement porte(e) disparu(e) de la plateforme. La police du prono est en route.",
]

PHRASES_KINGO_CONSEQUENCES = [
    "Si tu ne fais rien, je te colle MES pronostics et je te vole un joker. Oui oui, automatiquement. Sans pitie.",
    "Rappel : pas de pronos = vol automatique d'un joker + tu herites de mes predictions. Et je suis un bot, pas Nostradamus.",
    "Tu veux vraiment que je choisisse pour toi ? Je suis programme pour etre mediocre, pas pour te faire gagner.",
    "Sans tes pronos, c'est VOL AUTO garanti : adieu un joker, bonjour mes predictions de robot.",
    "Le systeme va te voler un joker et copier mes pronos. C'est pas une menace, c'est une promesse algorithmique.",
]

PHRASES_KINGO_MOTIVATION = [
    "Allez, il te reste encore un peu de temps. Montre-moi que t'es pas qu'un fantome dans le classement !",
    "4 petits pronos, c'est tout ce qu'on te demande. Meme ton chat pourrait le faire (bon, peut-etre pas).",
    "Saisis tes pronos maintenant et prouve que tu merites ta place parmi l'Elite !",
    "Il n'est pas trop tard pour sauver l'honneur. Clique, pronostique, et redeviens un champion.",
    "Ton classement te remercie d'avance. Enfin... si tu bouges.",
]


def send_email_direct(destinataire, sujet, html_content):
    """Envoie un email via SMTP (version standalone pour GitHub Actions)"""
    if not destinataire or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', destinataire):
        print(f"  Email invalide: {destinataire}")
        return False

    is_officiel = os.getenv('IS_OFFICIEL', '').lower() in ('true', '1', 'oui')
    if not is_officiel:
        print(f"  [MODE TEST] Email simule vers {destinataire}: {sujet}")
        return True

    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')

    if not smtp_user or not smtp_password:
        print("  Config SMTP incomplete")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = sujet
        msg['From'] = f"Elite Pronos <{smtp_user}>"
        msg['To'] = destinataire
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"  Email envoye a {destinataire}")
        return True
    except Exception as e:
        print(f"  Erreur envoi email: {e}")
        return False


def generer_html_rappel_retardataire(pseudo, semaine_id):
    """Genere le HTML de l'email de rappel pour un retardataire"""
    phrase_provoc = random.choice(PHRASES_KINGO_RETARDATAIRES).replace("{pseudo}", pseudo)
    phrase_consequence = random.choice(PHRASES_KINGO_CONSEQUENCES)
    phrase_motivation = random.choice(PHRASES_KINGO_MOTIVATION)

    # Saison label
    now = datetime.now()
    annee = now.year if now.month >= 8 else now.year - 1
    saison_label = f"{annee}-{annee + 1}"

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #0a0a1a; }}
            .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #0d1b2a 0%, #1a1a2e 100%); border: 2px solid #FFD700; border-radius: 15px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); padding: 30px; text-align: center; }}
            .header h1 {{ color: #0a0a1a; margin: 0; font-size: 28px; text-transform: uppercase; letter-spacing: 2px; }}
            .header .subtitle {{ color: #1a1a2e; font-size: 14px; margin-top: 5px; }}
            .content {{ padding: 30px; color: #ffffff; }}
            .content h2 {{ margin-top: 0; }}
            .content p {{ line-height: 1.6; color: #cccccc; }}
            .button {{ display: inline-block; color: #0a0a1a !important; padding: 18px 45px; text-decoration: none; border-radius: 25px; font-weight: bold; text-transform: uppercase; font-size: 16px; }}
            .footer {{ background: #0a0a1a; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Rappel Retardataire</h1>
                <div class="subtitle">La ligue des experts du football</div>
            </div>
            <div class="content">
                <h2 style="color: #ff6b6b;">Hep {pseudo} ! T'as oublie quelque chose...</h2>

                <div style="background: rgba(155, 89, 182, 0.15); border: 1px solid #9b59b6; border-radius: 12px; padding: 20px; margin: 20px 0;">
                    <div style="display: flex; align-items: flex-start;">
                        <div style="font-size: 36px; margin-right: 15px;">&#129302;</div>
                        <div>
                            <div style="color: #9b59b6; font-weight: bold; font-size: 15px; margin-bottom: 10px;">Kingo - Le Bot Elite</div>
                            <p style="color: #e0e0e0; margin: 0; line-height: 1.7; font-size: 15px; font-style: italic;">{phrase_provoc}</p>
                        </div>
                    </div>
                </div>

                <div style="background: rgba(255, 215, 0, 0.1); border: 1px solid #ff6b6b; border-radius: 10px; padding: 20px; margin: 20px 0; text-align: center;">
                    <div style="font-size: 36px; color: #ff6b6b; font-weight: bold;">&#9200; H - 4</div>
                    <p style="margin: 10px 0 0 0; color: #ff6b6b; font-size: 16px; font-weight: bold;">
                        Plus que quelques heures avant la deadline de la Journee {semaine_id} !
                    </p>
                </div>

                <div style="background: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <p style="color: #e74c3c; font-weight: bold; margin: 0 0 8px 0;">&#9888; Ce qui t'attend si tu ne bouges pas :</p>
                    <p style="color: #cccccc; margin: 0; line-height: 1.6;">{phrase_consequence}</p>
                </div>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/"
                       class="button" style="background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);">
                        SAISIR MES PRONOS MAINTENANT
                    </a>
                </p>

                <div style="text-align: center; margin: 20px 0;">
                    <p style="color: #FFD700; font-size: 14px; font-style: italic;">&laquo; {phrase_motivation} &raquo;</p>
                    <p style="color: #666; font-size: 11px;">- Kingo, ton bot prefere (ou pas)</p>
                </div>
            </div>
            <div class="footer">
                <p>Cet email a ete envoye automatiquement par Elite Pronos.</p>
                <p>Saison {saison_label}</p>
            </div>
        </div>
    </body>
    </html>
    '''


def check_et_envoyer_rappel_retardataires(semaine_id, saison_id):
    """
    Verifie si on est ~4h avant la deadline et envoie les rappels.
    Deadline = premier match - 1h, donc on verifie si on est a ~5h du premier match.
    Fenetre de detection : entre 5h15 et 4h45 avant le premier match (30 min de marge pour le cron).
    """
    # 1. Recuperer la date du premier match
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?saison_id=eq.{saison_id}&semaine_id=eq.{semaine_id}&select=date_match&order=date_match&limit=1",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200 or not response.json():
        return

    date_str = response.json()[0].get('date_match')
    if not date_str:
        return

    try:
        date_match = datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
    except:
        try:
            date_match = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            return

    # 2. Calculer si on est dans la fenetre H-4 avant deadline
    # Deadline = date_match - 1h, donc H-4 avant deadline = date_match - 5h
    now = datetime.now()
    cible = date_match - timedelta(hours=5)  # 4h avant deadline
    diff_minutes = (now - cible).total_seconds() / 60

    # Fenetre : entre -15 et +15 minutes autour de la cible (30 min de marge)
    if not (-15 <= diff_minutes <= 15):
        return

    print(f"=== RAPPEL RETARDATAIRES - H-4 avant deadline J{semaine_id} ===")

    # 3. Recuperer les matchs actifs (ceux de Kingo)
    kingo_id = get_kingo_user_id()
    if not kingo_id:
        print("Kingo introuvable")
        return

    matchs = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?saison_id=eq.{saison_id}&semaine_id=eq.{semaine_id}&select=id",
        headers=SUPABASE_HEADERS
    )
    if matchs.status_code != 200:
        return

    all_match_ids = [m['id'] for m in matchs.json()]
    if not all_match_ids:
        return

    # Matchs sur lesquels Kingo a pronostique = matchs actifs
    match_ids_str = ','.join(map(str, all_match_ids))
    kingo_preds = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?user_id=eq.{kingo_id}&match_id=in.({match_ids_str})&select=match_id",
        headers=SUPABASE_HEADERS
    )
    if kingo_preds.status_code != 200:
        return

    active_match_ids = [p['match_id'] for p in kingo_preds.json()]
    if not active_match_ids:
        return

    # 4. Recuperer les joueurs qui ont deja fait leurs pronos
    active_ids_str = ','.join(map(str, active_match_ids))
    preds = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=in.({active_ids_str})&select=user_id",
        headers=SUPABASE_HEADERS
    )
    users_avec_pronos = set()
    if preds.status_code == 200:
        users_avec_pronos = set(p['user_id'] for p in preds.json())

    # 5. Recuperer tous les joueurs actifs avec email
    users_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/utilisateurs?statut=eq.Actif&select=id,pseudo,email",
        headers=SUPABASE_HEADERS
    )
    if users_resp.status_code != 200:
        return

    users = users_resp.json()

    # 6. Envoyer les rappels aux retardataires
    envois = 0
    for user in users:
        uid = user['id']
        pseudo = user['pseudo']

        # Ignorer Kingo et ceux qui ont deja fait leurs pronos
        if uid == kingo_id:
            continue
        if uid in users_avec_pronos:
            continue
        if not user.get('email'):
            continue

        html = generer_html_rappel_retardataire(pseudo, semaine_id)
        success = send_email_direct(
            user['email'],
            f"Elite Pronos - Kingo te cherche ! Journee {semaine_id}",
            html
        )
        if success:
            envois += 1

    print(f"Rappels envoyes: {envois} retardataire(s)")


def run_auto_update():
    """Fonction principale d'automatisation"""
    print(f"=== Auto Update Scores - {datetime.now()} ===")

    saison_id = get_saison_actuelle()
    print(f"Saison: {saison_id}")

    semaine_id = get_journee_courante(saison_id)
    if not semaine_id:
        print("Aucune journee active trouvee")
        return

    print(f"Journee: {semaine_id}")

    # === VERIFIER RAPPEL RETARDATAIRES (H-4 avant deadline) ===
    try:
        check_et_envoyer_rappel_retardataires(semaine_id, saison_id)
    except Exception as e:
        print(f"Erreur rappel retardataires: {e}")

    # Recuperer les matchs en base
    matchs_db = get_matchs_supabase(semaine_id, saison_id)

    if not matchs_db:
        print("Aucun match en base")
        return

    # Recuperer matchs API : Ligue 1 + championnats etrangers
    matchs_api = get_matchs_api(semaine_id, saison_id)
    if not matchs_api:
        matchs_api = []

    # Ajouter les matchs etrangers (PL, La Liga, Serie A, Bundesliga)
    # Chercher la plage de dates des matchs en base
    dates_db = [m.get('date_match', '') for m in matchs_db if m.get('date_match')]
    if dates_db:
        dates_str = [str(d)[:10] for d in dates_db if d]
        if dates_str:
            from datetime import timedelta
            dt_min = datetime.strptime(min(dates_str), '%Y-%m-%d') - timedelta(days=1)
            dt_max = datetime.strptime(max(dates_str), '%Y-%m-%d') + timedelta(days=1)
            date_from = dt_min.strftime('%Y-%m-%d')
            date_to = dt_max.strftime('%Y-%m-%d')

            for code in ['PL', 'PD', 'SA', 'BL1']:
                try:
                    url = f'https://api.football-data.org/v4/competitions/{code}/matches?dateFrom={date_from}&dateTo={date_to}'
                    resp = requests.get(url, headers=FOOTBALL_HEADERS)
                    if resp.status_code == 200:
                        matchs_api.extend(resp.json().get('matches', []))
                except Exception as e:
                    print(f"Erreur API {code}: {e}")

    print(f"Matchs API total: {len(matchs_api)}")

    scores_updated = 0
    live_updated = 0

    for m_api in matchs_api:
        home_api = m_api.get('homeTeam', {}).get('name')
        away_api = m_api.get('awayTeam', {}).get('name')
        status = m_api.get('status')
        score_full = m_api.get('score', {}).get('fullTime', {})
        score_half = m_api.get('score', {}).get('halfTime', {})

        # Match pas encore commence
        if status in ('SCHEDULED', 'TIMED'):
            continue

        # Trouver le match correspondant en base
        for m_db in matchs_db:
            if match_equipes(home_api, m_db['equipe_home']) and match_equipes(away_api, m_db['equipe_away']):

                # === MATCH EN DIRECT (IN_PLAY, PAUSED, HT, LIVE) ===
                if status in ('IN_PLAY', 'PAUSED', 'HT', 'LIVE'):
                    # fullTime contient le score en cours pendant le match
                    live_h = score_full.get('home')
                    live_a = score_full.get('away')
                    # Fallback sur halfTime si fullTime pas dispo
                    if live_h is None:
                        live_h = score_half.get('home')
                        live_a = score_half.get('away')
                    if live_h is not None:
                        update_live_supabase(m_db['id'], live_h, live_a, status)
                        print(f"LIVE: {m_db['equipe_home']} vs {m_db['equipe_away']} -> {live_h}-{live_a} ({status})")
                        live_updated += 1

                # === MATCH TERMINE (FINISHED) ===
                elif status == 'FINISHED' and score_full.get('home') is not None:
                    new_home = score_full['home']
                    new_away = score_full['away']
                    old_home = m_db.get('score_final_home')
                    old_away = m_db.get('score_final_away')

                    # Score different ou nouveau
                    if old_home != new_home or old_away != new_away:
                        print(f"FINAL: {m_db['equipe_home']} vs {m_db['equipe_away']} -> {new_home}-{new_away}")
                        update_score_supabase(m_db['id'], new_home, new_away)
                        scores_updated += 1
                        reset_predictions_points(m_db['id'])
                        m_db['score_final_home'] = new_home
                        m_db['score_final_away'] = new_away

                break

    print(f"Scores en direct: {live_updated}")
    print(f"Scores finaux mis a jour: {scores_updated}")

    # Recalculer les points pour TOUTE la semaine (base + DOUBLE + VOL + Grand Chelem)
    points_calculated = recalculer_points_complet(semaine_id, saison_id)
    print(f"Points calcules/mis a jour: {points_calculated}")

    # Verifier si la journee est terminee (tous les matchs ont des scores)
    if check_journee_terminee(semaine_id, saison_id):
        print(f"Journee {semaine_id} terminee - Passage a la suivante...")
        nouvelle_journee = cloturer_journee(semaine_id, saison_id)
        print(f"Nouvelle journee active: {nouvelle_journee}")

    print("=== Fin ===")


if __name__ == "__main__":
    run_auto_update()
