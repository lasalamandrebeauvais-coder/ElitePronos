"""
Bot Resultats - Elite Pronos
Met a jour les scores des matchs en fonction du temps ecoule
- A partir de 50 min apres le debut : score mi-temps
- A partir de 120 min apres le debut : score final
- Calcule automatiquement les points gagnes pour chaque pronostic
"""
import requests
import sqlite3
import os
from datetime import datetime, timedelta, timezone

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Cle API Football-Data (depuis secrets)
def _get_api_token():
    try:
        import streamlit as st
        return st.secrets.get("FOOTBALL_API_TOKEN", os.getenv("FOOTBALL_API_TOKEN", ""))
    except Exception:
        return os.getenv("FOOTBALL_API_TOKEN", "")

API_TOKEN = _get_api_token()

# Configuration des bonus
BONUS_SCORE_EXACT = 10  # +10 pts si score exact


def calculer_temps_ecoule(date_match):
    """
    Calcule le temps ecoule depuis le debut du match en minutes
    Retourne: nombre de minutes (negatif si pas encore commence)
    """
    if not date_match:
        return None

    try:
        # Parser la date du match
        if isinstance(date_match, str):
            if 'T' in date_match:
                dt_match = datetime.fromisoformat(date_match.replace('Z', '+00:00'))
            else:
                dt_match = datetime.strptime(date_match, '%Y-%m-%d %H:%M:%S')
                dt_match = dt_match.replace(tzinfo=timezone.utc)
        else:
            dt_match = date_match
            if dt_match.tzinfo is None:
                dt_match = dt_match.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        diff = now - dt_match
        minutes_ecoulees = int(diff.total_seconds() / 60)

        return minutes_ecoulees

    except Exception as e:
        print(f"Erreur calcul temps: {e}")
        return None


def determiner_action(minutes_ecoulees, status_actuel, a_mi_temps, a_final):
    """
    Determine quelle action effectuer selon le temps ecoule
    Retourne: 'rien', 'live', 'mi_temps', 'final'
    """
    if minutes_ecoulees is None:
        return 'rien'

    # Match pas encore commence
    if minutes_ecoulees < 0:
        return 'rien'

    # Match deja marque comme FINISHED avec score final
    if status_actuel == 'FINISHED' and a_final:
        return 'rien'

    # A partir de 120 min : recuperer score final
    if minutes_ecoulees >= 120:
        if not a_final:  # Pas encore de score final
            return 'final'
        return 'rien'

    # Entre 50 et 120 min : recuperer score mi-temps
    if minutes_ecoulees >= 50:
        if not a_mi_temps:  # Pas encore de score mi-temps
            return 'mi_temps'
        return 'rien'

    # Entre 0 et 50 min : match en cours, recuperer score live
    if minutes_ecoulees >= 0:
        return 'live'

    return 'rien'


def calculer_points_match(prono_h, prono_a, score_h, score_a, mise, cote_h, cote_n, cote_a):
    """
    Calcule les points gagnes pour un pronostic

    Formule:
    - Pronostic correct (1N2): Mise × Cote correspondante
    - Score exact: + 10 pts bonus
    - Pronostic incorrect: -Mise (perte de la mise)

    Retourne: (points_gagnes, is_score_exact)
    """
    # Determiner le resultat reel (1, N, 2)
    if score_h > score_a:
        resultat_reel = '1'
        cote = cote_h
    elif score_h < score_a:
        resultat_reel = '2'
        cote = cote_a
    else:
        resultat_reel = 'N'
        cote = cote_n

    # Determiner le pronostic (1, N, 2)
    if prono_h > prono_a:
        resultat_prono = '1'
    elif prono_h < prono_a:
        resultat_prono = '2'
    else:
        resultat_prono = 'N'

    # Verifier si le 1N2 est correct
    is_1n2_correct = (resultat_prono == resultat_reel)

    # Verifier si le score exact
    is_score_exact = (prono_h == score_h and prono_a == score_a)

    if not is_1n2_correct:
        # Pronostic incorrect: perte de la mise
        return -mise, False

    # Pronostic correct: Mise × Cote
    points = mise * cote

    # Bonus score exact
    if is_score_exact:
        points += BONUS_SCORE_EXACT

    return round(points, 1), is_score_exact


def calculer_points_journee(cursor, match_id, score_h, score_a):
    """
    Calcule les points gagnes pour tous les pronostics d'un match
    """
    # Recuperer les cotes du match
    cursor.execute("""
        SELECT cote_home, cote_draw, cote_away
        FROM matches WHERE id = ?
    """, (match_id,))
    cotes = cursor.fetchone()

    if not cotes:
        print(f"  Erreur: cotes non trouvees pour match {match_id}")
        return 0

    cote_h, cote_n, cote_a = cotes

    # Valeurs par defaut si cotes manquantes
    if cote_h is None:
        cote_h = 2.0
    if cote_n is None:
        cote_n = 3.0
    if cote_a is None:
        cote_a = 2.0

    # Recuperer tous les pronostics pour ce match
    cursor.execute("""
        SELECT id, user_id, score_prono_home, score_prono_away, mise_points
        FROM predictions
        WHERE match_id = ?
    """, (match_id,))
    pronostics = cursor.fetchall()

    nb_calcules = 0
    for pred_id, user_id, prono_h, prono_a, mise in pronostics:
        # Calculer les points
        points, is_exact = calculer_points_match(
            prono_h, prono_a,
            score_h, score_a,
            mise,
            cote_h, cote_n, cote_a
        )

        # Mettre a jour la prediction
        cursor.execute("""
            UPDATE predictions
            SET points_gagnes = ?, is_score_exact = ?
            WHERE id = ?
        """, (points, 1 if is_exact else 0, pred_id))

        nb_calcules += 1

    return nb_calcules


def recuperer_et_mettre_a_jour_scores():
    """
    Fonction principale qui:
    1. Calcule le temps ecoule pour chaque match
    2. A +50min : recupere le score mi-temps
    3. A +120min : recupere le score final + calcule les points
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Recuperer la saison et journee courante
    cursor.execute("SELECT id FROM saisons WHERE is_active = 1")
    saison_row = cursor.fetchone()
    if not saison_row:
        print("Aucune saison active trouvee")
        conn.close()
        return
    saison_id = saison_row[0]

    cursor.execute("SELECT MAX(semaine_id) FROM matches WHERE saison_id = ? AND is_active = 1", (saison_id,))
    journee_row = cursor.fetchone()
    if not journee_row or not journee_row[0]:
        print("Aucune journee courante trouvee")
        conn.close()
        return
    journee_courante = journee_row[0]

    print(f"{'='*60}")
    print(f"BOT RESULTATS - Saison {saison_id} - Journee {journee_courante}")
    print(f"Heure actuelle (UTC): {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*60}\n")

    # Recuperer tous les matchs de la journee
    cursor.execute("""
        SELECT id, equipe_home, equipe_away, date_match, status,
               score_mi_temps_home, score_mi_temps_away,
               score_final_home, score_final_away
        FROM matches
        WHERE saison_id = ? AND semaine_id = ? AND is_active = 1
        ORDER BY date_match
    """, (saison_id, journee_courante))

    matchs = cursor.fetchall()

    if not matchs:
        print("Aucun match trouve pour cette journee")
        conn.close()
        return

    print(f"Matchs de la journee: {len(matchs)}\n")

    # Listes pour les actions
    matchs_live = []       # Matchs en cours (0-50 min)
    matchs_mi_temps = []   # Matchs dont on doit recuperer le score mi-temps
    matchs_final = []      # Matchs dont on doit recuperer le score final

    for match in matchs:
        match_id, home, away, date_match, status, mi_h, mi_a, final_h, final_a = match

        # Calculer le temps ecoule
        minutes = calculer_temps_ecoule(date_match)

        # Determiner l'action
        a_mi_temps = mi_h is not None
        a_final = final_h is not None
        action = determiner_action(minutes, status, a_mi_temps, a_final)

        # Affichage
        if minutes is not None and minutes >= 0:
            temps_str = f"+{minutes} min"
        elif minutes is not None:
            temps_str = f"dans {-minutes} min"
        else:
            temps_str = "?"

        score_mi = f"{mi_h}-{mi_a}" if a_mi_temps else "-"
        score_fin = f"{final_h}-{final_a}" if a_final else "-"

        print(f"{home} vs {away}")
        print(f"  Temps: {temps_str} | Mi-temps: {score_mi} | Final: {score_fin}")

        if action == 'live':
            print(f"  -> ACTION: Recuperer score LIVE")
            matchs_live.append((match_id, home, away))
        elif action == 'mi_temps':
            print(f"  -> ACTION: Recuperer score MI-TEMPS")
            matchs_mi_temps.append((match_id, home, away))
        elif action == 'final':
            print(f"  -> ACTION: Recuperer score FINAL")
            matchs_final.append((match_id, home, away))
        elif status == 'FINISHED':
            print(f"  -> Match termine")
        elif minutes is not None and minutes < 0:
            print(f"  -> Pas encore commence")
        else:
            print(f"  -> En attente")
        print()

    # Executer les mises a jour
    headers = {'X-Auth-Token': API_TOKEN}
    matchs_mis_a_jour = 0
    points_calcules = 0

    # Recuperer les matchs depuis l'API si necessaire
    if matchs_live or matchs_mi_temps or matchs_final:
        print(f"{'='*60}")
        print("RECUPERATION DES SCORES SUR L'API...")
        print(f"{'='*60}\n")

        all_api_matchs = []

        # Recuperer matchs en cours (pour live et mi-temps)
        if matchs_live or matchs_mi_temps:
            try:
                url = "https://api.football-data.org/v4/matches?status=LIVE,IN_PLAY,PAUSED"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    matchs_api = response.json().get('matches', [])
                    all_api_matchs.extend(matchs_api)
                    print(f"Matchs EN COURS sur l'API: {len(matchs_api)}")
            except Exception as e:
                print(f"Erreur API LIVE: {e}")

        # Recuperer matchs termines (pour final)
        if matchs_final:
            try:
                url = "https://api.football-data.org/v4/matches?status=FINISHED"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    matchs_api = response.json().get('matches', [])
                    all_api_matchs.extend(matchs_api)
                    print(f"Matchs TERMINES sur l'API: {len(matchs_api)}")
            except Exception as e:
                print(f"Erreur API FINISHED: {e}")

        print()

        # Traiter les matchs LIVE (score en cours)
        for match_id, home_db, away_db in matchs_live:
            print(f"Recherche LIVE: {home_db} vs {away_db}")

            found = False
            for m_api in all_api_matchs:
                home_api = m_api['homeTeam']['name']
                away_api = m_api['awayTeam']['name']

                if home_db == home_api and away_db == away_api:
                    score_data = m_api.get('score', {})
                    # Score actuel (fullTime contient le score en cours pendant le match)
                    full_time = score_data.get('fullTime', {})
                    current_h = full_time.get('home')
                    current_a = full_time.get('away')

                    if current_h is not None:
                        # Mettre a jour le statut et stocker le score en cours
                        # On utilise score_mi_temps pour afficher le score live
                        cursor.execute("""
                            UPDATE matches
                            SET status = ?,
                                score_mi_temps_home = ?,
                                score_mi_temps_away = ?
                            WHERE id = ?
                        """, (m_api['status'], current_h, current_a, match_id))
                        print(f"  -> LIVE: {current_h}-{current_a} (status: {m_api['status']})")
                        matchs_mis_a_jour += 1
                        found = True
                    break

            if not found:
                print(f"  -> Non trouve sur l'API")

        # Traiter les matchs mi-temps
        for match_id, home_db, away_db in matchs_mi_temps:
            print(f"Recherche MI-TEMPS: {home_db} vs {away_db}")

            found = False
            for m_api in all_api_matchs:
                home_api = m_api['homeTeam']['name']
                away_api = m_api['awayTeam']['name']

                if home_db == home_api and away_db == away_api:
                    score_data = m_api.get('score', {})
                    half_time = score_data.get('halfTime', {})
                    mi_h = half_time.get('home')
                    mi_a = half_time.get('away')

                    if mi_h is not None:
                        cursor.execute("""
                            UPDATE matches
                            SET score_mi_temps_home = ?,
                                score_mi_temps_away = ?,
                                status = ?
                            WHERE id = ?
                        """, (mi_h, mi_a, m_api['status'], match_id))
                        print(f"  -> MI-TEMPS: {mi_h}-{mi_a}")
                        matchs_mis_a_jour += 1
                        found = True
                    break

            if not found:
                print(f"  -> Non trouve sur l'API")

        # Traiter les matchs final
        for match_id, home_db, away_db in matchs_final:
            print(f"Recherche FINAL: {home_db} vs {away_db}")

            found = False
            for m_api in all_api_matchs:
                home_api = m_api['homeTeam']['name']
                away_api = m_api['awayTeam']['name']

                if home_db == home_api and away_db == away_api:
                    score_data = m_api.get('score', {})
                    full_time = score_data.get('fullTime', {})
                    final_h = full_time.get('home')
                    final_a = full_time.get('away')

                    # Aussi recuperer mi-temps si pas encore fait
                    half_time = score_data.get('halfTime', {})
                    mi_h = half_time.get('home')
                    mi_a = half_time.get('away')

                    if final_h is not None:
                        cursor.execute("""
                            UPDATE matches
                            SET score_final_home = ?,
                                score_final_away = ?,
                                score_mi_temps_home = COALESCE(score_mi_temps_home, ?),
                                score_mi_temps_away = COALESCE(score_mi_temps_away, ?),
                                status = 'FINISHED'
                            WHERE id = ?
                        """, (final_h, final_a, mi_h, mi_a, match_id))
                        print(f"  -> FINAL: {final_h}-{final_a}")
                        matchs_mis_a_jour += 1
                        found = True

                        # CALCULER LES POINTS GAGNES
                        print(f"  -> Calcul des points...")
                        nb = calculer_points_journee(cursor, match_id, final_h, final_a)
                        points_calcules += nb
                        print(f"  -> {nb} pronostic(s) calcule(s)")
                    break

            if not found:
                print(f"  -> Non trouve sur l'API")

        conn.commit()

    # Verifier s'il y a des matchs termines sans points calcules
    print(f"\n{'='*60}")
    print("VERIFICATION DES POINTS NON CALCULES...")
    print(f"{'='*60}\n")

    cursor.execute("""
        SELECT m.id, m.equipe_home, m.equipe_away, m.score_final_home, m.score_final_away
        FROM matches m
        WHERE m.saison_id = ? AND m.semaine_id = ? AND m.is_active = 1
        AND m.score_final_home IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM predictions p
            WHERE p.match_id = m.id AND (p.points_gagnes IS NULL OR p.points_gagnes = 0)
        )
    """, (saison_id, journee_courante))

    matchs_sans_points = cursor.fetchall()

    for match_id, home, away, score_h, score_a in matchs_sans_points:
        print(f"Calcul manquant: {home} vs {away} ({score_h}-{score_a})")
        nb = calculer_points_journee(cursor, match_id, score_h, score_a)
        points_calcules += nb
        print(f"  -> {nb} pronostic(s) calcule(s)")

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"BILAN:")
    print(f"  - {matchs_mis_a_jour} match(s) mis a jour")
    print(f"  - {points_calcules} pronostic(s) calcules")
    print(f"{'='*60}")


if __name__ == "__main__":
    recuperer_et_mettre_a_jour_scores()
