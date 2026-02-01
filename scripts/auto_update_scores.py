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

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qyyfxbwyvshpuuqwrxsl.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_secret_v_cT_G2XV1znRhrS0cx_qw_6vZmzMKW")

# Configuration API Football-Data
FOOTBALL_API_TOKEN = os.getenv("FOOTBALL_API_TOKEN", "bf58da6a49824f2a8742957b89ca52ee")

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

    # Recuperer les matchs
    matchs_db = get_matchs_supabase(semaine_id, saison_id)
    matchs_api = get_matchs_api(semaine_id, saison_id)

    if not matchs_db:
        print("Aucun match en base")
        return

    if not matchs_api:
        print("Impossible de recuperer les matchs API")
        return

    # Recuperer les jokers DOUBLE
    users_double = get_jokers_double(semaine_id)
    print(f"Jokers DOUBLE actifs: {len(users_double)}")

    scores_updated = 0
    points_calculated = 0

    for m_api in matchs_api:
        home_api = m_api.get('homeTeam', {}).get('name')
        away_api = m_api.get('awayTeam', {}).get('name')
        score = m_api.get('score', {}).get('fullTime', {})
        status = m_api.get('status')

        # Match pas encore termine
        if score.get('home') is None:
            continue

        # Trouver le match correspondant en base
        for m_db in matchs_db:
            if match_equipes(home_api, m_db['equipe_home']) and match_equipes(away_api, m_db['equipe_away']):
                old_home = m_db.get('score_final_home')
                old_away = m_db.get('score_final_away')
                new_home = score['home']
                new_away = score['away']

                # Score different ou nouveau
                if old_home != new_home or old_away != new_away:
                    print(f"Mise a jour: {m_db['equipe_home']} vs {m_db['equipe_away']} -> {new_home}-{new_away}")

                    # Mettre a jour le score
                    update_score_supabase(m_db['id'], new_home, new_away)
                    scores_updated += 1

                    # Reset et recalculer les points
                    reset_predictions_points(m_db['id'])
                    m_db['score_final_home'] = new_home
                    m_db['score_final_away'] = new_away

                # Calculer les points si pas encore fait
                if m_db.get('score_final_home') is not None:
                    pts = calculer_points(m_db, users_double)
                    points_calculated += pts

                break

    print(f"Scores mis a jour: {scores_updated}")
    print(f"Points calcules: {points_calculated}")
    print("=== Fin ===")


if __name__ == "__main__":
    run_auto_update()
