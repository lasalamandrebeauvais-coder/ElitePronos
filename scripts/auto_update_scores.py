"""
Script d'automatisation Elite Pronos
- Recupere les scores des matchs termines depuis l'API
- Met a jour Supabase
- Calcule les points automatiquement
- Execution via GitHub Actions (cron)
"""

import requests
import os
from datetime import datetime

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
    """Recupere la journee courante depuis Supabase"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?saison_id=eq.{saison_id}&is_active=eq.true&select=semaine_id&order=semaine_id.desc&limit=1",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200 and response.json():
        return response.json()[0]['semaine_id']
    return None


def get_matchs_supabase(semaine_id, saison_id):
    """Recupere les matchs de la journee depuis Supabase"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,equipe_home,equipe_away,score_final_home,score_final_away,cote_home,cote_draw,cote_away",
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

    # Recuperer les matchs actifs termines de la semaine precedente
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_prec}&saison_id=eq.{saison_id}&score_final_home=not.is.null&is_active=eq.true&select=id,score_final_home,score_final_away",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200:
        return set()

    matchs_prec = response.json()
    if len(matchs_prec) < 4:
        return set()

    match_ids = [m['id'] for m in matchs_prec]
    matchs_dict = {m['id']: (m['score_final_home'], m['score_final_away']) for m in matchs_prec}

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

    # Recuperer les matchs termines avec cotes
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&score_final_home=not.is.null&is_active=eq.true&select=id,score_final_home,score_final_away,cote_home,cote_draw,cote_away",
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


def check_journee_terminee(semaine_id, saison_id):
    """Verifie si tous les matchs de la journee sont termines"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&is_active=eq.true&select=id,score_final_home",
        headers=SUPABASE_HEADERS
    )
    if response.status_code == 200:
        matchs = response.json()
        if not matchs:
            return False  # Pas de matchs actifs
        # Tous les matchs ont un score ?
        return all(m.get('score_final_home') is not None for m in matchs)
    return False


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
