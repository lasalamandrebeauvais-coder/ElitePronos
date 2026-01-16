"""
Moteur de Calcul des Gains pour Elite Pronos
Gère les gains de base, jokers, chaînes de vol et Grand Chelem
"""
import sqlite3
import os
from datetime import datetime
from modules.database_manager import (
    get_connection,
    get_joker_actif_semaine,
    get_pronostics_effectifs,
    tous_matchs_termines,
    get_utilisateurs_sans_pronostics,
    activer_vol_automatique,
    resoudre_chaine_vol
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# ============================================
# CONFIGURATION DES BONUS
# ============================================
# Formule: Points = (Mise × Cote) + Bonus

BONUS_SCORE_EXACT = 10   # +10 pts fixes si score exact
BONUS_GRAND_CHELEM = 40  # +40 pts appliques sur la semaine SUIVANTE


def determiner_resultat_match(score_home, score_away):
    """Détermine le résultat d'un match (1, N, 2)"""
    if score_home > score_away:
        return '1'
    elif score_home < score_away:
        return '2'
    return 'N'


def a_fait_grand_chelem_semaine_precedente(utilisateur_id, semaine_id):
    """
    Vérifie si l'utilisateur a fait un Grand Chelem la semaine précédente.
    Retourne True si 4/4 résultats 1N2 corrects.
    """
    semaine_precedente = semaine_id - 1
    if semaine_precedente < 1:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    # Compter les pronostics 1N2 corrects de la semaine précédente
    cursor.execute('''
        SELECT COUNT(*)
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        WHERE p.user_id = ?
          AND m.semaine_id = ?
          AND m.score_final_home IS NOT NULL
          AND (
              (p.score_prono_home > p.score_prono_away AND m.score_final_home > m.score_final_away) OR
              (p.score_prono_home < p.score_prono_away AND m.score_final_home < m.score_final_away) OR
              (p.score_prono_home = p.score_prono_away AND m.score_final_home = m.score_final_away)
          )
    ''', (utilisateur_id, semaine_precedente))

    nb_corrects = cursor.fetchone()[0]

    # Compter le nombre total de matchs de cette semaine
    cursor.execute('''
        SELECT COUNT(*) FROM matches WHERE semaine_id = ? AND score_final_home IS NOT NULL
    ''', (semaine_precedente,))

    nb_matchs = cursor.fetchone()[0]
    conn.close()

    # Grand Chelem = 4/4 corrects
    return nb_corrects >= 4 and nb_matchs >= 4


def calculer_gain_match(prono_home, prono_away, score_home, score_away, mise, cote_home, cote_draw, cote_away):
    """
    Calcule le gain pour un match donné.

    FORMULE: Points = (Mise × Cote) + Bonus
    - Bonus score exact: +10 pts fixes

    Retourne:
        - gain: points gagnés (0 si prono incorrect)
        - is_1n2_correct: bool si le sens du résultat est correct
        - is_score_exact: bool si le score exact est correct
    """
    # Résultat réel
    resultat_reel = determiner_resultat_match(score_home, score_away)

    # Pronostic du joueur
    resultat_prono = determiner_resultat_match(prono_home, prono_away)

    # Vérifier si le 1N2 est correct
    is_1n2_correct = (resultat_prono == resultat_reel)

    # Vérifier si le score exact est correct
    is_score_exact = (prono_home == score_home and prono_away == score_away)

    if not is_1n2_correct:
        # Pronostic incorrect - pas de gain
        return 0, False, False

    # Sélectionner la cote correspondante
    if resultat_reel == '1':
        cote = cote_home
    elif resultat_reel == '2':
        cote = cote_away
    else:
        cote = cote_draw

    # Gain de base: Mise × Cote
    gain = mise * cote

    # Bonus score exact: +10 pts FIXES
    if is_score_exact:
        gain += BONUS_SCORE_EXACT

    return round(gain, 2), is_1n2_correct, is_score_exact


def calculer_gains_semaine(utilisateur_id, semaine_id):
    """
    Calcule les gains d'un utilisateur pour une semaine.

    Prend en compte:
    - Les chaînes de vol (pronostics effectifs)
    - Le joker Points Doubles (x2 personnel)
    - Le Grand Chelem (bonus 50 pts si 4/4)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Récupérer le joker actif pour cet utilisateur
    joker = get_joker_actif_semaine(utilisateur_id, semaine_id)

    # Récupérer les pronostics effectifs (résout les chaînes de vol)
    pronos_data = get_pronostics_effectifs(utilisateur_id, semaine_id)
    pronostics = pronos_data['pronostics']
    est_vol = pronos_data['est_vol']

    if not pronostics:
        conn.close()
        return {
            'total_gains': 0,
            'nb_1n2_corrects': 0,
            'nb_scores_exacts': 0,
            'grand_chelem': False,
            'joker_utilise': joker['type'] if joker else None,
            'est_vol': est_vol,
            'details': []
        }

    # Récupérer les matchs de la semaine avec leurs scores finaux
    cursor.execute('''
        SELECT id, cote_home, cote_draw, cote_away, score_final_home, score_final_away
        FROM matches
        WHERE semaine_id = ?
          AND score_final_home IS NOT NULL
          AND score_final_away IS NOT NULL
    ''', (semaine_id,))

    matchs_dict = {m[0]: m[1:] for m in cursor.fetchall()}
    conn.close()

    total_gains = 0
    nb_1n2_corrects = 0
    nb_scores_exacts = 0
    details = []

    for prono in pronostics:
        match_id, prono_home, prono_away, mise = prono

        if match_id not in matchs_dict:
            continue

        cote_home, cote_draw, cote_away, score_home, score_away = matchs_dict[match_id]

        gain, is_1n2, is_exact = calculer_gain_match(
            prono_home, prono_away,
            score_home, score_away,
            mise,
            cote_home, cote_draw, cote_away
        )

        total_gains += gain
        if is_1n2:
            nb_1n2_corrects += 1
        if is_exact:
            nb_scores_exacts += 1

        details.append({
            'match_id': match_id,
            'prono': f"{prono_home}-{prono_away}",
            'score_reel': f"{score_home}-{score_away}",
            'mise': mise,
            'gain': gain,
            'is_1n2_correct': is_1n2,
            'is_score_exact': is_exact
        })

    # Grand Chelem: 4 pronostics 1N2 corrects cette semaine
    # Le bonus sera applique la semaine SUIVANTE
    grand_chelem = (nb_1n2_corrects == 4 and len(pronostics) >= 4)

    # Verifier si l'utilisateur a fait un Grand Chelem la semaine PRECEDENTE
    # Si oui, appliquer le bonus +40 pts CETTE semaine
    bonus_grand_chelem_precedent = 0
    if a_fait_grand_chelem_semaine_precedente(utilisateur_id, semaine_id):
        bonus_grand_chelem_precedent = BONUS_GRAND_CHELEM
        total_gains += BONUS_GRAND_CHELEM

    # Appliquer le joker Points Doubles (x2)
    # IMPORTANT: Le multiplicateur est strictement personnel
    # Il ne se transmet PAS lors d'un vol
    multiplicateur = 1
    if joker and joker['type'] == 'DOUBLE' and not est_vol:
        multiplicateur = 2
        total_gains *= 2

    return {
        'total_gains': round(total_gains, 2),
        'nb_1n2_corrects': nb_1n2_corrects,
        'nb_scores_exacts': nb_scores_exacts,
        'grand_chelem': grand_chelem,
        'bonus_grand_chelem_applique': bonus_grand_chelem_precedent,
        'joker_utilise': joker['type'] if joker else None,
        'multiplicateur': multiplicateur,
        'est_vol': est_vol,
        'source_pronos_id': pronos_data['source_id'],
        'details': details
    }


def traiter_oublis_semaine(semaine_id):
    """
    Traite les utilisateurs qui ont oublié de faire leurs pronostics.
    Active automatiquement le joker Points Volés avec le dernier du classement comme cible.
    """
    oublieurs = get_utilisateurs_sans_pronostics(semaine_id)

    resultats = []
    for user_id, pseudo in oublieurs:
        success, message = activer_vol_automatique(user_id, semaine_id)
        resultats.append({
            'user_id': user_id,
            'pseudo': pseudo,
            'success': success,
            'message': message
        })

    return resultats


def calculer_tous_gains_semaine(semaine_id):
    """
    Calcule les gains de tous les utilisateurs pour une semaine.

    IMPORTANT: Ne déclenche le calcul que si les 4 matchs sont terminés (Status FT)
    """
    # Vérifier que tous les matchs sont terminés
    if not tous_matchs_termines(semaine_id):
        return None, "Tous les matchs ne sont pas encore terminés"

    # D'abord, traiter les oublis
    oublis = traiter_oublis_semaine(semaine_id)

    # Récupérer tous les utilisateurs actifs
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, pseudo FROM utilisateurs WHERE statut = 'Actif'
    ''')
    utilisateurs = cursor.fetchall()
    conn.close()

    resultats = []
    for user_id, pseudo in utilisateurs:
        gains = calculer_gains_semaine(user_id, semaine_id)
        gains['user_id'] = user_id
        gains['pseudo'] = pseudo
        resultats.append(gains)

    # Trier par gains décroissants
    resultats.sort(key=lambda x: x['total_gains'], reverse=True)

    return {
        'semaine_id': semaine_id,
        'oublis_traites': oublis,
        'resultats': resultats
    }, "Calcul terminé"


def sauvegarder_resultats_semaine(semaine_id, resultats):
    """
    Sauvegarde les résultats de la semaine dans la base de données.
    Met à jour les points_gagnes dans predictions et le classement.
    """
    conn = get_connection()
    cursor = conn.cursor()

    for resultat in resultats['resultats']:
        user_id = resultat['user_id']

        # Mettre à jour les points gagnés pour chaque prédiction
        for detail in resultat['details']:
            cursor.execute('''
                UPDATE predictions
                SET points_gagnes = ?,
                    is_score_exact = ?
                WHERE user_id = ? AND match_id = ?
            ''', (detail['gain'], detail['is_score_exact'], user_id, detail['match_id']))

    conn.commit()
    conn.close()

    return True


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def afficher_rapport_semaine(semaine_id):
    """Génère un rapport lisible des gains de la semaine"""
    resultats, message = calculer_tous_gains_semaine(semaine_id)

    if resultats is None:
        return message

    rapport = []
    rapport.append(f"=== RAPPORT SEMAINE {semaine_id} ===\n")

    if resultats['oublis_traites']:
        rapport.append("--- OUBLIS TRAITÉS ---")
        for oubli in resultats['oublis_traites']:
            rapport.append(f"  {oubli['pseudo']}: {oubli['message']}")
        rapport.append("")

    rapport.append("--- CLASSEMENT ---")
    for i, r in enumerate(resultats['resultats'], 1):
        joker_info = ""
        if r['joker_utilise']:
            joker_info = f" [{r['joker_utilise']}]"
        if r['est_vol']:
            joker_info += " (pronostics volés)"
        if r['grand_chelem']:
            joker_info += " [GRAND CHELEM]"

        rapport.append(
            f"  #{i} {r['pseudo']}: {r['total_gains']} pts "
            f"({r['nb_1n2_corrects']}/4 1N2, {r['nb_scores_exacts']} exacts){joker_info}"
        )

    return "\n".join(rapport)
