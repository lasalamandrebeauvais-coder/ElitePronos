"""
Script d'automatisation Elite Pronos
- Recupere les scores des matchs termines depuis l'API
- Met a jour Supabase
- Calcule les points automatiquement
- Execution via GitHub Actions (cron)
"""

import sys
import requests
import os
import random
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Configuration depuis les secrets GitHub Actions (pas de hardcode)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
FOOTBALL_API_TOKEN = os.getenv("FOOTBALL_API_TOKEN", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

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


# Mapping football-data.org → The Odds API
ODDS_API_MAPPING = {
    'FL1': 'soccer_france_ligue_one',
    'PL': 'soccer_epl',
    'PD': 'soccer_spain_la_liga',
    'SA': 'soccer_italy_serie_a',
    'BL1': 'soccer_germany_bundesliga',
}


def fetch_real_odds(championnats_codes=None):
    """Recupere les vraies cotes depuis The Odds API."""
    if not ODDS_API_KEY:
        print("[ODDS] Pas de cle API, fallback random")
        return {}

    if championnats_codes is None:
        championnats_codes = list(ODDS_API_MAPPING.keys())

    odds_dict = {}

    for code in championnats_codes:
        odds_key = ODDS_API_MAPPING.get(code)
        if not odds_key:
            continue
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{odds_key}/odds"
            params = {
                'apiKey': ODDS_API_KEY,
                'regions': 'eu',
                'markets': 'h2h',
                'oddsFormat': 'decimal',
            }
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                print(f"[ODDS] Erreur {resp.status_code} pour {code}")
                continue

            events = resp.json()
            print(f"[ODDS] {len(events)} matchs recuperes pour {code}")

            for event in events:
                home = event.get('home_team', '')
                away = event.get('away_team', '')
                all_home, all_draw, all_away = [], [], []
                for bookmaker in event.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market.get('key') != 'h2h':
                            continue
                        outcomes = {o['name']: o['price'] for o in market.get('outcomes', [])}
                        if home in outcomes:
                            all_home.append(outcomes[home])
                        if 'Draw' in outcomes:
                            all_draw.append(outcomes['Draw'])
                        if away in outcomes:
                            all_away.append(outcomes[away])

                if all_home and all_draw and all_away:
                    cote_h = round(sum(all_home) / len(all_home), 2)
                    cote_n = round(sum(all_draw) / len(all_draw), 2)
                    cote_a = round(sum(all_away) / len(all_away), 2)
                    odds_dict[(home.lower(), away.lower())] = (cote_h, cote_n, cote_a)

        except Exception as e:
            print(f"[ODDS] Exception pour {code}: {e}")
            continue

    print(f"[ODDS] Total: {len(odds_dict)} matchs avec cotes reelles")
    return odds_dict


def lookup_odds(odds_dict, equipe_home, equipe_away):
    """Cherche les cotes d'un match dans le dict (matching partiel)."""
    if not odds_dict:
        return None
    home_lower = equipe_home.lower()
    away_lower = equipe_away.lower()
    if (home_lower, away_lower) in odds_dict:
        return odds_dict[(home_lower, away_lower)]
    for (oh, oa), cotes in odds_dict.items():
        if (oh in home_lower or home_lower in oh) and \
           (oa in away_lower or away_lower in oa):
            return cotes
    return None


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

    # Recuperer les voleurs de la semaine precedente (exclus du GC)
    resp_vol = requests.get(
        f"{SUPABASE_URL}/rest/v1/jokers_historique?semaine_id=eq.{semaine_prec}&type_joker=eq.VOL&select=utilisateur_id",
        headers=SUPABASE_HEADERS
    )
    voleurs = set()
    if resp_vol.status_code == 200 and resp_vol.json():
        voleurs = {j['utilisateur_id'] for j in resp_vol.json()}

    # Recuperer toutes les predictions de ces matchs
    match_ids_str = ','.join(map(str, match_ids))
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=in.({match_ids_str})&select=user_id,match_id,score_prono_home,score_prono_away",
        headers=SUPABASE_HEADERS
    )
    if response.status_code != 200:
        return set()

    predictions = response.json()

    # Compter les 1N2 corrects par user (exclure voleurs)
    user_corrects = {}
    for pred in predictions:
        user_id = pred['user_id']
        match_id = pred['match_id']

        # Exclure les voleurs du GC
        if user_id in voleurs:
            continue

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

    # Retourner les users avec 4/4 corrects (non voleurs)
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
            points = round(mise * cote, 2)
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

    # Traiter les oublis AVANT le calcul des points
    try:
        from modules.database_manager import appliquer_vol_auto_oublis
        oublis_traites, msg_oublis = appliquer_vol_auto_oublis(semaine_id, saison_id)
        if oublis_traites:
            print(f"Auto-VOL (script): {msg_oublis}")
            for o in oublis_traites:
                print(f"  -> {o['pseudo']} : {o['action']}")
    except Exception as e:
        print(f"Erreur Auto-VOL (script): {e}")

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
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=in.({match_ids_str})&select=id,user_id,match_id,score_prono_home,score_prono_away,mise_points,mise_bonus_gc,points_gagnes",
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

            mise_bonus_gc = pred.get('mise_bonus_gc', 0) or 0

            # Si VOL actif et cible a un prono pour ce match, utiliser les pronos de la cible
            if cible_id and match_id in cible_preds:
                cible_pred = cible_preds[match_id]
                prono_h = cible_pred['score_prono_home']
                prono_a = cible_pred['score_prono_away']
                # VOL: uniquement budget 100 de la cible
                mise = cible_pred['mise_points'] or 25
                is_vol = True
            else:
                prono_h = pred['score_prono_home']
                prono_a = pred['score_prono_away']
                mise = pred['mise_points'] or 25
                is_vol = False

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
            pts_bonus_gc = 0

            if bon_resultat:
                points = round(mise * cote, 2)
                if prono_h == score_h and prono_a == score_a:
                    points += BONUS_EXACT
                    is_exact = True
                # Bonus GC (gains uniquement, pas de perte)
                if mise_bonus_gc > 0 and not is_vol:
                    pts_bonus_gc = round(mise_bonus_gc * cote, 2)
                    if is_exact:
                        pts_bonus_gc += BONUS_EXACT
            else:
                points = -mise
                # Bonus GC: PAS de perte si mauvais prono
                pts_bonus_gc = 0

            # Joker DOUBLE: x2 sur budget 100 uniquement (pas le bonus GC)
            if user_id in users_double:
                points = points * 2

            # Voleur n'a pas droit au bonus GC
            if is_vol:
                pts_bonus_gc = 0

            # Total = points budget 100 + bonus GC
            points_total = points + pts_bonus_gc

            # Mettre a jour seulement si le score a change
            old_points = pred.get('points_gagnes')
            if old_points != points_total:
                update_prediction_points(pred['id'], points_total, is_exact)
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

    # 1. Envoyer le debrief ironique (avant desactivation des matchs)
    try:
        envoyer_debrief_ironique_auto(semaine_id, saison_id)
    except Exception as e:
        print(f"  Erreur debrief ironique: {e}")

    # 2. Desactiver les matchs de la journee terminee
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
    # Recuperer les vraies cotes depuis The Odds API
    odds_codes = ['FL1'] + list(CHAMPIONNATS.keys())
    odds_dict = fetch_real_odds(odds_codes)

    count = 0
    for i, m in enumerate(all_matchs):
        # Vraies cotes depuis The Odds API (fallback random)
        real = lookup_odds(odds_dict, m['equipe_home'], m['equipe_away'])
        if real:
            cote_h, cote_n, cote_a = real
        else:
            cote_h = round(random.uniform(1.5, 3.5), 2)
            cote_n = round(random.uniform(3.0, 4.0), 2)
            cote_a = round(random.uniform(1.8, 4.0), 2)

        # Tous les matchs inactifs - l'admin valide manuellement
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
                'is_active': False
            }
        )
        print(f"  -> [{m['championnat']}] {m['equipe_home']} vs {m['equipe_away']}")
        count += 1

    print(f"{count} matchs importes pour J{semaine_id} (tous inactifs - validation admin requise)")


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
    "J'ai demande a ChatGPT ce qu'il pensait de ton absence. Il m'a repondu : 'Meme moi j'aurais pronostique.' Aie.",
    "Ton profil est tellement inactif que j'ai failli le classer comme compte fantome. Tu respires au moins ?",
    "Les matchs approchent, ton formulaire est vide, et moi je perds espoir en l'humanite. Merci {pseudo}.",
    "J'ai lance une recherche Google sur 'joueur qui ne fait jamais ses pronos'. Ta photo est apparue en premier resultat.",
    "Tu sais qu'il y a des gens qui paient pour avoir le droit de pronostiquer ? Toi tu l'as et tu t'en fiches. Ingrat.",
    "On raconte que {pseudo} aurait ete apercu(e) pour la derniere fois... tres loin d'Elite Pronos.",
    "Si tu mettais autant d'energie a faire tes pronos qu'a les eviter, tu serais premier du classement.",
    "La deadline arrive plus vite que toi le matin. Et c'est pas peu dire.",
    "Je me suis permis de consulter ton historique. Verdict : tu es un serial oublieur. Recidiviste du neant.",
    "Pendant que tu procrastines, les autres joueurs calculent leurs cotes, affinent leurs strategies, et toi... tu fais la sieste ?",
]

PHRASES_KINGO_CONSEQUENCES = [
    "Si tu ne fais rien, je te colle MES pronostics et je te vole un joker. Oui oui, automatiquement. Sans pitie.",
    "Rappel : pas de pronos = vol automatique d'un joker + tu herites de mes predictions. Et je suis un bot, pas Nostradamus.",
    "Tu veux vraiment que je choisisse pour toi ? Je suis programme pour etre mediocre, pas pour te faire gagner.",
    "Sans tes pronos, c'est VOL AUTO garanti : adieu un joker, bonjour mes predictions de robot.",
    "Le systeme va te voler un joker et copier mes pronos. C'est pas une menace, c'est une promesse algorithmique.",
    "Mes pronos sont generes par un algorithme qui a ete entraine sur... rien du tout. Bonne chance avec ca.",
    "Je vais te filer mes pronos et t'enlever un joker. C'est comme un cadeau d'anniversaire, mais en pire.",
    "Vol auto dans 4 heures : un joker en moins + mes pronos de bot desabuse. Tu veux vraiment vivre ca ?",
    "Imagine : tu ouvres tes resultats et tu vois MES pronos a la place des tiens. L'horreur absolue. Et c'est ce qui va arriver.",
    "Le reglement est formel : oubli = vol auto. Et mes pronos sont aussi fiables qu'un GPS en pleine foret.",
]

PHRASES_KINGO_MOTIVATION = [
    "Allez, il te reste encore un peu de temps. Montre-moi que t'es pas qu'un fantome dans le classement !",
    "4 petits pronos, c'est tout ce qu'on te demande. Meme ton chat pourrait le faire (bon, peut-etre pas).",
    "Saisis tes pronos maintenant et prouve que tu merites ta place parmi l'Elite !",
    "Il n'est pas trop tard pour sauver l'honneur. Clique, pronostique, et redeviens un champion.",
    "Ton classement te remercie d'avance. Enfin... si tu bouges.",
    "Tes adversaires n'attendent que ton absence pour prendre tes points. Tu vas les laisser faire ?",
    "Quelque part au fond de toi, il y a un pronostiqueur qui sommeille. REVEILLE-LE.",
    "T'as 4 heures pour passer de 'fantome du classement' a 'legende vivante'. Au boulot.",
    "Rappelle-toi pourquoi tu t'es inscrit : pour l'honneur, la gloire, et surtout pour ne pas te faire humilier par un bot.",
    "C'est maintenant ou jamais. Enfin surtout maintenant, parce que dans 4 heures c'est trop tard.",
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
                    <div style="font-size: 36px; color: #ff6b6b; font-weight: bold;">&#9200; H - 1</div>
                    <p style="margin: 10px 0 0 0; color: #ff6b6b; font-size: 16px; font-weight: bold;">
                        Plus qu'1 HEURE avant la deadline de la Journee {semaine_id} !
                    </p>
                </div>

                <div style="background: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <p style="color: #e74c3c; font-weight: bold; margin: 0 0 8px 0;">&#9888; Ce qui t'attend si tu ne bouges pas :</p>
                    <p style="color: #cccccc; margin: 0; line-height: 1.6;">{phrase_consequence}</p>
                </div>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/"
                       class="button" style="background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);">
                        Se connecter
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

    # 2. Calculer si on est dans la fenetre H-1 avant deadline
    # Deadline = date_match - 1h, donc H-1 avant deadline = date_match - 2h
    now = datetime.now()
    cible = date_match - timedelta(hours=2)  # 1h avant deadline
    diff_minutes = (now - cible).total_seconds() / 60

    # Fenetre : entre -15 et +15 minutes autour de la cible (30 min de marge pour le cron)
    if not (-15 <= diff_minutes <= 15):
        return

    print(f"=== RAPPEL RETARDATAIRES - H-1 avant deadline J{semaine_id} ===")

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


# ============================================
# SYNTHESE DES PARIS (auto apres deadline)
# ============================================

def _generer_commentaire_synthese(stats):
    """Genere un commentaire ironique de Kingo pour la synthese des paris"""
    commentaires = []
    deadline_passee = stats.get('matchs_termines', 0) > 0
    nb = stats.get('nb_joueurs', 0)

    if nb == 0:
        return "Personne n'a encore joue cette semaine. Vous attendez quoi ? Que les matchs se jouent sans vous ?"
    elif nb == 1:
        commentaires.append("Un seul brave a ose jouer pour l'instant. Les autres ont peur ou quoi ?")
    elif nb < 5:
        commentaires.append(f"Seulement {nb} joueurs ont fait leurs pronos. Les absents ont toujours tort !")
    else:
        commentaires.append(f"{nb} pronostiqueurs en lice cette semaine. Que le spectacle commence !")

    if stats.get('grosses_mises'):
        if deadline_passee:
            gros = stats['grosses_mises'][0]
            commentaires.append(f"{gros['pseudo']} a mise gros ({gros['mise']} pts) sur {gros['match']}. Confiance ou folie ?")
        else:
            phrases = [
                "Quelqu'un a sorti l'artillerie lourde cette semaine... Mais qui ?",
                "Une grosse mise a ete placee. Le suspense reste entier !",
                "Des paris audacieux ont ete enregistres. Je ne dirai rien de plus !",
            ]
            commentaires.append(random.choice(phrases))

    if stats.get('jokers'):
        nb_jokers = len(stats['jokers'])
        if deadline_passee:
            joker = stats['jokers'][0]
            if joker['type'] == 'DOUBLE':
                commentaires.append(f"{joker['pseudo']} a joue son joker Points Doubles. Ca passe ou ca casse !")
            else:
                commentaires.append(f"{joker['pseudo']} a utilise le vol de pronostics. Strategie ou desespoir ?")
        else:
            if nb_jokers == 1:
                commentaires.append("Un joker a ete active... Lequel et par qui ? Mystere !")
            else:
                commentaires.append(f"{nb_jokers} jokers actives cette semaine ! Ca va chauffer...")

    for m in stats.get('matchs', []):
        if m['pct_home'] >= 70:
            commentaires.append(f"{m['pct_home']}% voient {m['home']} gagner. Unanimite ou piege ?")
            break
        elif m['pct_away'] >= 70:
            commentaires.append(f"{m['pct_away']}% misent sur {m['away']}. Et si c'etait trop beau ?")
            break
        elif m['pct_nul'] >= 50:
            commentaires.append(f"{m['pct_nul']}% predisent un nul pour {m['home']} vs {m['away']}. Le foot est impredictible !")
            break

    return " ".join(commentaires)


def envoyer_debrief_ironique_auto(semaine_id, saison_id):
    """
    Envoie automatiquement le debrief ironique de fin de journee.
    A appeler au debut de cloturer_journee(), avant de desactiver les matchs.
    """
    print(f"=== DEBRIEF IRONIQUE AUTO - J{semaine_id} ===")

    # 1. Recuperer les matchs de la journee avec scores
    matchs_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,equipe_home,equipe_away,score_final_home,score_final_away,championnat",
        headers=SUPABASE_HEADERS
    )
    if matchs_resp.status_code != 200:
        print("  Impossible de recuperer les matchs")
        return
    matchs = matchs_resp.json()
    if not matchs:
        print("  Aucun match trouve")
        return

    # Filtrer ceux joues par Kingo (= matchs actifs de la journee)
    all_match_ids = [m['id'] for m in matchs]
    match_map = {m['id']: m for m in matchs}
    kingo_id = get_kingo_user_id()
    active_match_ids = all_match_ids
    if kingo_id:
        ids_str = ','.join(map(str, all_match_ids))
        kp = requests.get(
            f"{SUPABASE_URL}/rest/v1/predictions?user_id=eq.{kingo_id}&match_id=in.({ids_str})&select=match_id",
            headers=SUPABASE_HEADERS
        )
        if kp.status_code == 200 and kp.json():
            active_match_ids = [p['match_id'] for p in kp.json()]

    matchs_actifs = [m for m in matchs if m['id'] in active_match_ids]
    match_ids_str = ','.join(map(str, active_match_ids))

    # 2. Recuperer les utilisateurs actifs (sans Kingo)
    users_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/utilisateurs?statut=eq.Actif&pseudo=neq.Kingo&select=id,pseudo,email",
        headers=SUPABASE_HEADERS
    )
    users = users_resp.json() if users_resp.status_code == 200 else []
    user_map = {u['id']: u['pseudo'] for u in users}

    # 3. Recuperer les predictions avec points_gagnes
    preds_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=in.({match_ids_str})&select=user_id,match_id,score_prono_home,score_prono_away,points_gagnes",
        headers=SUPABASE_HEADERS
    )
    predictions = preds_resp.json() if preds_resp.status_code == 200 else []

    # 4. Calculer les stats par joueur
    stats_joueur = {}
    for u in users:
        stats_joueur[u['id']] = {'points': 0, 'bons_pronos': 0, 'scores_exacts': 0}

    for p in predictions:
        uid = p['user_id']
        m = match_map.get(p['match_id'])
        if not m or m.get('score_final_home') is None:
            continue
        if uid not in stats_joueur:
            stats_joueur[uid] = {'points': 0, 'bons_pronos': 0, 'scores_exacts': 0}

        stats_joueur[uid]['points'] += (p.get('points_gagnes') or 0)

        prono_res = '1' if p['score_prono_home'] > p['score_prono_away'] else ('2' if p['score_prono_home'] < p['score_prono_away'] else 'N')
        real_res = '1' if m['score_final_home'] > m['score_final_away'] else ('2' if m['score_final_home'] < m['score_final_away'] else 'N')
        if prono_res == real_res:
            stats_joueur[uid]['bons_pronos'] += 1
        if p['score_prono_home'] == m['score_final_home'] and p['score_prono_away'] == m['score_final_away']:
            stats_joueur[uid]['scores_exacts'] += 1

    # 5. Classement trie par points
    sorted_joueurs = sorted(stats_joueur.items(), key=lambda x: x[1]['points'], reverse=True)
    nb_matchs = len([m for m in matchs_actifs if m.get('score_final_home') is not None])

    classement = []
    for i, (uid, stats) in enumerate(sorted_joueurs, 1):
        pseudo = user_map.get(uid, 'Inconnu')
        grand_chelem = stats['bons_pronos'] >= 4 and nb_matchs >= 4
        classement.append({
            'rang': i,
            'pseudo': pseudo,
            'points': stats['points'],
            'bons_pronos': stats['bons_pronos'],
            'scores_exacts': stats['scores_exacts'],
            'grand_chelem': grand_chelem
        })

    # 6. Commentaire ironique de Kingo
    phrases_intro = [
        "Encore une semaine de drama footballistique !",
        "Les des sont tombes, et certains auraient prefere ne pas regarder...",
        "Resultats tombes. Les excuses peuvent commencer.",
        "La journee est terminee. Les blessures d'ego peuvent soigner.",
        "Voila ce que ca donne quand on croit connaitre le foot !"
    ]
    commentaire = random.choice(phrases_intro)
    if classement:
        winner = classement[0]
        loser = classement[-1]
        commentaire += f" Champion de la semaine : @{winner['pseudo']} avec {winner['points']} pts"
        if winner['grand_chelem']:
            commentaire += " — Grand Chelem !"
        commentaire += "."
        if len(classement) > 1:
            commentaire += f" Une pensee pour @{loser['pseudo']} ({loser['points']} pts)... courage, ca ira mieux la prochaine fois !"

    # 7. Generer le HTML du debrief
    now = datetime.now()
    annee = now.year if now.month >= 8 else now.year - 1
    saison_label = f"{annee}-{annee + 1}"

    lignes_classement = ""
    medailles = ['🥇', '🥈', '🥉']
    for joueur in classement:
        rang = joueur['rang']
        medaille = medailles[rang - 1] if rang <= 3 else f"#{rang}"
        gc_badge = ' <span style="color:#FFD700;">⭐ Grand Chelem</span>' if joueur['grand_chelem'] else ''
        se_txt = f" | {joueur['scores_exacts']} score(s) exact(s)" if joueur['scores_exacts'] else ""
        bg = "#002040" if rang % 2 == 0 else "#001a35"
        lignes_classement += f'''
        <tr style="background:{bg};">
            <td style="padding:10px 15px;color:#D4AF37;font-weight:bold;">{medaille}</td>
            <td style="padding:10px 15px;color:#ffffff;">@{joueur["pseudo"]}{gc_badge}</td>
            <td style="padding:10px 15px;color:#00FF88;font-weight:bold;text-align:center;">{joueur["points"]} pts</td>
            <td style="padding:10px 15px;color:#aaaaaa;text-align:center;">{joueur["bons_pronos"]}/{nb_matchs}{se_txt}</td>
        </tr>'''

    lignes_matchs = ""
    for m in matchs_actifs:
        if m.get('score_final_home') is not None:
            score = f"{m['score_final_home']}-{m['score_final_away']}"
            champ = m.get('championnat', '')
            lignes_matchs += f'''
            <tr>
                <td style="padding:8px 15px;color:#888888;font-size:11px;">{champ}</td>
                <td style="padding:8px 15px;color:#cccccc;">{m["equipe_home"]}</td>
                <td style="padding:8px 15px;color:#FFD700;font-weight:bold;text-align:center;">{score}</td>
                <td style="padding:8px 15px;color:#cccccc;">{m["equipe_away"]}</td>
            </tr>'''

    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="background:#001020;color:#ffffff;font-family:Arial,sans-serif;margin:0;padding:20px;">
<div style="max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#002040,#001530);border:2px solid #D4AF37;border-radius:15px;padding:30px;margin-bottom:20px;text-align:center;">
        <div style="font-size:48px;">⚽</div>
        <h1 style="color:#D4AF37;margin:10px 0;">Debrief Journee {semaine_id}</h1>
        <p style="color:#aaaaaa;">Saison {saison_label}</p>
    </div>

    <div style="background:rgba(155,89,182,0.1);border:1px solid #9b59b6;border-radius:10px;padding:20px;margin-bottom:20px;">
        <div style="display:flex;align-items:flex-start;">
            <div style="font-size:32px;margin-right:15px;">🤖</div>
            <div>
                <div style="color:#9b59b6;font-weight:bold;font-size:14px;margin-bottom:8px;">Kingo — Le Bot Elite</div>
                <p style="color:#cccccc;margin:0;line-height:1.6;font-style:italic;">{commentaire}</p>
            </div>
        </div>
    </div>

    <div style="background:#002040;border:1px solid #D4AF37;border-radius:10px;padding:20px;margin-bottom:20px;">
        <h2 style="color:#D4AF37;margin:0 0 15px;">🏆 Classement de la Semaine</h2>
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="background:linear-gradient(135deg,#D4AF37,#B8960C);">
                    <th style="padding:10px 15px;color:#001020;text-align:left;">#</th>
                    <th style="padding:10px 15px;color:#001020;text-align:left;">Joueur</th>
                    <th style="padding:10px 15px;color:#001020;text-align:center;">Points</th>
                    <th style="padding:10px 15px;color:#001020;text-align:center;">Pronos</th>
                </tr>
            </thead>
            <tbody>{lignes_classement}</tbody>
        </table>
    </div>

    <div style="background:#001530;border:1px solid #333;border-radius:10px;padding:20px;margin-bottom:20px;">
        <h3 style="color:#D4AF37;margin:0 0 15px;">📋 Resultats des Matchs</h3>
        <table style="width:100%;border-collapse:collapse;">
            <tbody>{lignes_matchs}</tbody>
        </table>
    </div>

    <div style="text-align:center;color:#555555;font-size:12px;margin-top:20px;">
        Elite Pronos — Powered by Kingo 🤖
    </div>
</div>
</body>
</html>'''

    # 8. Envoyer a tous les joueurs
    envois = 0
    for user in users:
        if not user.get('email'):
            continue
        ok = send_email_direct(
            user['email'],
            f"Elite Pronos - Debrief J{semaine_id} 🏆",
            html
        )
        if ok:
            envois += 1

    print(f"Debrief ironique envoye a {envois} joueur(s)")


def generer_html_synthese_paris(semaine_id, jokers_actifs, stats_matchs, commentaire_bot):
    """Genere le HTML complet de l'email de synthese des paris"""
    now = datetime.now()
    annee = now.year if now.month >= 8 else now.year - 1
    saison_label = f"{annee}-{annee + 1}"

    # === COMMENTAIRE DU BOT ===
    commentaire_html = ""
    if commentaire_bot:
        commentaire_html = f'''
        <div style="background: rgba(155, 89, 182, 0.1); border: 1px solid #9b59b6; border-radius: 10px; padding: 20px; margin: 20px 0;">
            <div style="display: flex; align-items: flex-start;">
                <div style="font-size: 32px; margin-right: 15px;">&#129302;</div>
                <div>
                    <div style="color: #9b59b6; font-weight: bold; font-size: 14px; margin-bottom: 8px;">Kingo - Le Bot Elite</div>
                    <p style="color: #cccccc; margin: 0; line-height: 1.6; font-style: italic;">{commentaire_bot}</p>
                </div>
            </div>
        </div>
        '''

    # === SECTION JOKERS ACTIFS ===
    jokers_html = ""
    if jokers_actifs:
        jokers_items = ""
        for joker in jokers_actifs:
            pseudo = joker.get('pseudo', '?')
            type_j = joker.get('type_joker', '')
            if type_j == 'double':
                jokers_items += f'''
                <div style="display: flex; align-items: center; padding: 10px; margin: 5px 0; background: rgba(255, 215, 0, 0.1); border-radius: 8px; border-left: 4px solid #FFD700;">
                    <span style="font-size: 24px; margin-right: 12px;">x2</span>
                    <div>
                        <div style="color: #FFD700; font-weight: bold;">@{pseudo}</div>
                        <div style="color: #AAAAAA; font-size: 12px;">Points Doubles actives</div>
                    </div>
                </div>
                '''
            elif type_j == 'vol':
                cible = joker.get('cible_pseudo', '')
                jokers_items += f'''
                <div style="display: flex; align-items: center; padding: 10px; margin: 5px 0; background: rgba(155, 89, 182, 0.1); border-radius: 8px; border-left: 4px solid #9b59b6;">
                    <span style="font-size: 24px; margin-right: 12px;">&#127917;</span>
                    <div>
                        <div style="color: #9b59b6; font-weight: bold;">@{pseudo}</div>
                        <div style="color: #AAAAAA; font-size: 12px;">Vole les pronos de <strong style="color: #fff;">@{cible}</strong></div>
                    </div>
                </div>
                '''
        jokers_html = f'''
        <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #FFD700; margin: 0 0 15px 0; font-size: 16px;">&#127183; Jokers Actives cette semaine</h3>
            {jokers_items}
        </div>
        '''
    else:
        jokers_html = '''
        <div style="background: #0a0a1a; border: 1px solid #333; border-radius: 10px; padding: 15px; margin: 20px 0; text-align: center;">
            <p style="color: #666; margin: 0;">Aucun joker active cette semaine</p>
        </div>
        '''

    # === SECTION STATISTIQUES PAR MATCH ===
    stats_html = ""
    if stats_matchs:
        stats_rows = ""
        for match_name, tendances in stats_matchs.items():
            pct_dom = tendances.get('dom', 0)
            pct_nul = tendances.get('nul', 0)
            pct_ext = tendances.get('ext', 0)
            stats_rows += f'''
            <div style="margin: 10px 0; padding: 12px; background: #1a1a2e; border-radius: 8px;">
                <div style="color: #ccc; font-size: 13px; margin-bottom: 8px;">{match_name}</div>
                <div style="display: flex; height: 24px; border-radius: 4px; overflow: hidden; background: #333;">
                    <div style="width: {pct_dom}%; background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); display: flex; align-items: center; justify-content: center;">
                        <span style="color: #fff; font-size: 11px; font-weight: bold;">{pct_dom}%</span>
                    </div>
                    <div style="width: {pct_nul}%; background: linear-gradient(135deg, #7f8c8d 0%, #95a5a6 100%); display: flex; align-items: center; justify-content: center;">
                        <span style="color: #fff; font-size: 11px; font-weight: bold;">{pct_nul}%</span>
                    </div>
                    <div style="width: {pct_ext}%; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); display: flex; align-items: center; justify-content: center;">
                        <span style="color: #fff; font-size: 11px; font-weight: bold;">{pct_ext}%</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 10px; color: #666;">
                    <span>&#127968; Dom</span>
                    <span>&#129309; Nul</span>
                    <span>&#9992; Ext</span>
                </div>
            </div>
            '''
        stats_html = f'''
        <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #FFD700; margin: 0 0 10px 0; font-size: 16px;">&#128202; Tendances des Pronos</h3>
            <p style="color: #AAAAAA; font-size: 12px; margin: 0 0 15px 0;">Repartition des pronostics par match</p>
            {stats_rows}
        </div>
        '''

    content = f'''
    <h2>Synthese des Paris - Semaine {semaine_id}</h2>
    <p>Les pronostics sont clos ! Voici le recapitulatif de la semaine.</p>
    {commentaire_html}
    {jokers_html}
    {stats_html}
    <div style="background: rgba(255, 215, 0, 0.1); border: 1px solid #FFD700; border-radius: 10px; padding: 20px; margin: 20px 0; text-align: center;">
        <p style="color: #FFD700; margin: 0;">Que le meilleur gagne !</p>
        <p style="color: #AAAAAA; font-size: 12px; margin: 5px 0 0 0;">
            Les resultats seront calcules automatiquement apres les matchs.
        </p>
    </div>

    <p style="text-align: center;">
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/"
           style="display: inline-block; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #0a0a1a !important; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-weight: bold; text-transform: uppercase; margin: 20px 0;">
            Se connecter
        </a>
    </p>
    '''

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
            .content h2 {{ color: #FFD700; margin-top: 0; }}
            .content p {{ line-height: 1.6; color: #cccccc; }}
            .footer {{ background: #0a0a1a; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Synthese des Paris</h1>
                <div class="subtitle">La ligue des experts du football</div>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>Cet email a ete envoye automatiquement par Elite Pronos.</p>
                <p>Saison {saison_label}</p>
            </div>
        </div>
    </body>
    </html>
    '''


def check_et_envoyer_synthese_paris(semaine_id, saison_id):
    """
    Verifie si on est ~15min apres la deadline et envoie la synthese.
    Deadline = premier match - 1h, donc on verifie si on est a ~45min du premier match.
    Fenetre de detection : entre 40 et 55 min avant le premier match.
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

    # 2. Calculer si on est ~15min apres la deadline
    # Deadline = date_match - 1h, donc 15min apres = date_match - 45min
    now = datetime.now()
    cible = date_match - timedelta(minutes=45)  # 15min apres deadline
    diff_minutes = (now - cible).total_seconds() / 60

    # Fenetre : entre -15 et +15 minutes autour de la cible
    if not (-15 <= diff_minutes <= 15):
        return

    print(f"=== SYNTHESE DES PARIS - Post-deadline J{semaine_id} ===")

    # 3. Recuperer les matchs de la semaine
    matchs_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,equipe_home,equipe_away,score_final_home",
        headers=SUPABASE_HEADERS
    )
    if matchs_resp.status_code != 200:
        return

    matchs = matchs_resp.json()
    if not matchs:
        return

    match_ids = [m['id'] for m in matchs]
    match_map = {m['id']: m for m in matchs}

    # Filtrer sur les matchs actifs (ceux de Kingo)
    kingo_id = get_kingo_user_id()
    if kingo_id:
        match_ids_str = ','.join(map(str, match_ids))
        kingo_preds_resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/predictions?user_id=eq.{kingo_id}&match_id=in.({match_ids_str})&select=match_id",
            headers=SUPABASE_HEADERS
        )
        if kingo_preds_resp.status_code == 200 and kingo_preds_resp.json():
            active_match_ids = [p['match_id'] for p in kingo_preds_resp.json()]
            matchs = [m for m in matchs if m['id'] in active_match_ids]
            match_ids = [m['id'] for m in matchs]
            match_map = {m['id']: m for m in matchs}

    if not match_ids:
        return

    # 4. Recuperer toutes les predictions
    match_ids_str = ','.join(map(str, match_ids))
    preds_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/predictions?match_id=in.({match_ids_str})&select=user_id,match_id,score_prono_home,score_prono_away,mise_points",
        headers=SUPABASE_HEADERS
    )
    predictions = preds_resp.json() if preds_resp.status_code == 200 else []

    # 5. Recuperer les utilisateurs
    users_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/utilisateurs?statut=eq.Actif&select=id,pseudo,email",
        headers=SUPABASE_HEADERS
    )
    users = users_resp.json() if users_resp.status_code == 200 else []
    user_map = {u['id']: u['pseudo'] for u in users}

    # 6. Recuperer les jokers actifs
    jokers_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/jokers_historique?semaine_id=eq.{semaine_id}&select=utilisateur_id,type_joker",
        headers=SUPABASE_HEADERS
    )
    jokers_data = jokers_resp.json() if jokers_resp.status_code == 200 else []

    jokers_actifs = []
    for jrow in jokers_data:
        pseudo = user_map.get(jrow['utilisateur_id'], 'Inconnu')
        jokers_actifs.append({
            'pseudo': pseudo,
            'type_joker': jrow['type_joker'].lower(),
            'cible_pseudo': ''
        })

    # 7. Calculer les tendances 1/N/2
    stats_brut = {}
    grosses_mises = []

    for p in predictions:
        match = match_map.get(p['match_id'])
        if not match:
            continue
        pseudo = user_map.get(p['user_id'], 'Inconnu')
        match_key = f"{match['equipe_home']} vs {match['equipe_away']}"
        prono_h = p['score_prono_home']
        prono_a = p['score_prono_away']
        mise = p.get('mise_points', 0) or 0

        if match_key not in stats_brut:
            stats_brut[match_key] = {'dom': 0, 'nul': 0, 'ext': 0, 'total': 0}

        stats_brut[match_key]['total'] += 1
        if prono_h > prono_a:
            stats_brut[match_key]['dom'] += 1
        elif prono_h == prono_a:
            stats_brut[match_key]['nul'] += 1
        else:
            stats_brut[match_key]['ext'] += 1

        if mise >= 40:
            grosses_mises.append({'pseudo': pseudo, 'mise': mise, 'match': match_key})

    # Convertir en pourcentages
    stats_matchs = {}
    stats_for_comment = []
    for match_key, counts in stats_brut.items():
        total = counts['total']
        if total > 0:
            pct_dom = round(counts['dom'] * 100 / total)
            pct_nul = round(counts['nul'] * 100 / total)
            pct_ext = round(counts['ext'] * 100 / total)
            diff = 100 - (pct_dom + pct_nul + pct_ext)
            if diff:
                pct_nul += diff
            stats_matchs[match_key] = {'dom': pct_dom, 'nul': pct_nul, 'ext': pct_ext}

            parts = match_key.split(' vs ')
            stats_for_comment.append({
                'home': parts[0] if len(parts) > 0 else '?',
                'away': parts[1] if len(parts) > 1 else '?',
                'pct_home': pct_dom,
                'pct_away': pct_ext,
                'pct_nul': pct_nul
            })

    # 8. Generer le commentaire de Kingo
    nb_joueurs = len(set(p['user_id'] for p in predictions))
    matchs_termines = sum(1 for m in matchs if m.get('score_final_home') is not None)
    grosses_mises.sort(key=lambda x: x['mise'], reverse=True)

    stats_comment = {
        'nb_joueurs': nb_joueurs,
        'nb_pronostics': len(predictions),
        'matchs_termines': matchs_termines,
        'total_matchs': len(matchs),
        'matchs': stats_for_comment,
        'jokers': [{'pseudo': j['pseudo'], 'type': j['type_joker'].upper()} for j in jokers_actifs],
        'grosses_mises': grosses_mises[:3]
    }

    commentaire_bot = _generer_commentaire_synthese(stats_comment)

    # 9. Generer le HTML
    html = generer_html_synthese_paris(semaine_id, jokers_actifs, stats_matchs, commentaire_bot)

    # 10. Envoyer a tous les utilisateurs avec email
    envois = 0
    for user in users:
        if not user.get('email'):
            continue
        success = send_email_direct(
            user['email'],
            f"Elite Pronos - Synthese des Paris (Semaine {semaine_id})",
            html
        )
        if success:
            envois += 1

    print(f"Synthese envoyee a {envois} joueur(s)")


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

    # === VERIFIER RAPPEL RETARDATAIRES (H-1 avant deadline) ===
    try:
        check_et_envoyer_rappel_retardataires(semaine_id, saison_id)
    except Exception as e:
        print(f"Erreur rappel retardataires: {e}")

    # === VERIFIER SYNTHESE DES PARIS (15min apres deadline) ===
    try:
        check_et_envoyer_synthese_paris(semaine_id, saison_id)
    except Exception as e:
        print(f"Erreur synthese paris: {e}")

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
    try:
        run_auto_update()
    except Exception as e:
        print(f"ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
