"""
Module Synthese pour Elite Pronos
Genere une synthese des paris de la semaine avec stats et ironie
"""
import sqlite3
import os
import random
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')


def get_stats_semaine(saison_id, semaine_id):
    """
    Recupere les statistiques des paris pour la semaine
    Retourne: dict avec stats par match et stats globales
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stats = {
        'matchs': [],
        'jokers': [],
        'grosses_mises': [],
        'nb_joueurs': 0,
        'nb_pronostics': 0
    }

    # Recuperer les matchs de la semaine
    cursor.execute("""
        SELECT id, equipe_home, equipe_away
        FROM matches
        WHERE saison_id = ? AND semaine_id = ? AND is_active = 1
    """, (saison_id, semaine_id))
    matchs = cursor.fetchall()

    # Compter le nombre total de joueurs ayant pronostique
    cursor.execute("""
        SELECT COUNT(DISTINCT p.user_id)
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        WHERE m.saison_id = ? AND m.semaine_id = ?
    """, (saison_id, semaine_id))
    stats['nb_joueurs'] = cursor.fetchone()[0]

    # Stats par match
    for match_id, home, away in matchs:
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN score_prono_home > score_prono_away THEN 1 ELSE 0 END) as votes_home,
                SUM(CASE WHEN score_prono_home < score_prono_away THEN 1 ELSE 0 END) as votes_away,
                SUM(CASE WHEN score_prono_home = score_prono_away THEN 1 ELSE 0 END) as votes_nul,
                MAX(mise_points) as mise_max,
                AVG(mise_points) as mise_moy
            FROM predictions
            WHERE match_id = ?
        """, (match_id,))

        row = cursor.fetchone()
        total = row[0] or 0
        votes_home = row[1] or 0
        votes_away = row[2] or 0
        votes_nul = row[3] or 0
        mise_max = row[4] or 0
        mise_moy = row[5] or 0

        # Calculer les pourcentages
        if total > 0:
            pct_home = round(votes_home / total * 100)
            pct_away = round(votes_away / total * 100)
            pct_nul = round(votes_nul / total * 100)
        else:
            pct_home = pct_away = pct_nul = 0

        # Trouver qui a mis la mise max
        cursor.execute("""
            SELECT u.pseudo, p.mise_points
            FROM predictions p
            JOIN utilisateurs u ON p.user_id = u.id
            WHERE p.match_id = ? AND p.mise_points = ?
        """, (match_id, mise_max))
        gros_parieurs = cursor.fetchall()

        stats['matchs'].append({
            'home': home,
            'away': away,
            'pct_home': pct_home,
            'pct_away': pct_away,
            'pct_nul': pct_nul,
            'mise_max': mise_max,
            'mise_moy': round(mise_moy, 1),
            'gros_parieurs': gros_parieurs
        })

        # Ajouter aux grosses mises
        for pseudo, mise in gros_parieurs:
            if mise >= 40:  # Grosse mise = 40 pts ou plus
                stats['grosses_mises'].append({
                    'pseudo': pseudo,
                    'mise': mise,
                    'match': f"{home} vs {away}"
                })

    # Recuperer les jokers utilises cette semaine
    cursor.execute("""
        SELECT u.pseudo, j.type_joker
        FROM jokers_historique j
        JOIN utilisateurs u ON j.utilisateur_id = u.id
        WHERE j.semaine_id = ?
    """, (semaine_id,))

    for pseudo, type_joker in cursor.fetchall():
        stats['jokers'].append({
            'pseudo': pseudo,
            'type': type_joker
        })

    conn.close()
    return stats


def generer_commentaire_ironique(stats):
    """
    Genere un commentaire ironique base sur les stats
    """
    commentaires = []

    # Commentaire sur le nombre de joueurs
    nb = stats['nb_joueurs']
    if nb == 0:
        return "Personne n'a encore joue cette semaine. Vous attendez quoi ? Que les matchs se jouent sans vous ?"
    elif nb == 1:
        commentaires.append(f"Un seul brave a ose jouer pour l'instant. Les autres ont peur ou quoi ?")
    elif nb < 5:
        commentaires.append(f"Seulement {nb} joueurs ont fait leurs pronos. Les absents ont toujours tort !")

    # Commentaire sur les grosses mises
    if stats['grosses_mises']:
        gros = stats['grosses_mises'][0]
        phrases_mises = [
            f"**{gros['pseudo']}** mise gros ({gros['mise']} pts) sur {gros['match']}. Confiance ou folie ?",
            f"Attention, **{gros['pseudo']}** sort l'artillerie lourde avec {gros['mise']} pts !",
            f"**{gros['pseudo']}** n'a pas froid aux yeux : {gros['mise']} pts d'un coup !",
        ]
        commentaires.append(random.choice(phrases_mises))

    # Commentaire sur les jokers
    if stats['jokers']:
        joker = stats['jokers'][0]
        if joker['type'] == 'DOUBLE':
            phrases_joker = [
                f"**{joker['pseudo']}** joue son joker Points Doubles. Ca passe ou ca casse !",
                f"Joker Points Doubles pour **{joker['pseudo']}** ! La pression monte...",
            ]
        else:
            phrases_joker = [
                f"**{joker['pseudo']}** utilise le vol de pronostics. Strategie ou desespoir ?",
                f"Attention, **{joker['pseudo']}** a sorti le joker Vol ! Qui est la cible ?",
            ]
        commentaires.append(random.choice(phrases_joker))

    # Commentaire sur les votes
    for m in stats['matchs']:
        if m['pct_home'] >= 70:
            phrases = [
                f"**{m['pct_home']}%** voient {m['home']} gagner. Unanimite ou piege ?",
                f"Tout le monde ({m['pct_home']}%) mise sur {m['home']}. Attention au retournement !",
            ]
            commentaires.append(random.choice(phrases))
        elif m['pct_away'] >= 70:
            phrases = [
                f"**{m['pct_away']}%** croient en {m['away']}. L'outsider devient favori !",
                f"{m['away']} a la cote ({m['pct_away']}%). Le favori va-t-il trembler ?",
            ]
            commentaires.append(random.choice(phrases))
        elif m['pct_nul'] >= 40:
            commentaires.append(f"Match serre ? {m['pct_nul']}% parient sur le nul pour {m['home']} vs {m['away']}.")

    # Si pas assez de commentaires, ajouter un generique
    if len(commentaires) < 2:
        generiques = [
            "Que le meilleur pronostiqueur gagne !",
            "Les cotes sont la, les pronos sont faits. Que le spectacle commence !",
            "La tension monte avant le coup d'envoi...",
        ]
        commentaires.append(random.choice(generiques))

    return " ".join(commentaires[:3])  # Max 3 commentaires


def generer_synthese_html(stats, saison_id, semaine_id):
    """
    Genere le HTML de la synthese complete
    """
    if stats['nb_joueurs'] == 0:
        return """
        <div style="text-align: center; color: #AAAAAA; padding: 10px;">
            Aucun pronostic enregistre pour cette journee.
        </div>
        """

    html = ""

    # Stats par match
    for m in stats['matchs']:
        # Determiner le favori
        if m['pct_home'] > m['pct_away'] and m['pct_home'] > m['pct_nul']:
            favori = "1"
            favori_pct = m['pct_home']
        elif m['pct_away'] > m['pct_home'] and m['pct_away'] > m['pct_nul']:
            favori = "2"
            favori_pct = m['pct_away']
        else:
            favori = "N"
            favori_pct = m['pct_nul']

        html += f"""
        <div style="
            background: #002040;
            border-radius: 8px;
            padding: 10px;
            margin: 8px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #FFFFFF; font-size: 0.9em;">{m['home']}</span>
                <span style="color: #D4AF37; font-weight: bold;">vs</span>
                <span style="color: #FFFFFF; font-size: 0.9em;">{m['away']}</span>
            </div>
            <div style="display: flex; justify-content: space-around; font-size: 0.85em;">
                <span style="color: {'#00FF00' if favori == '1' else '#AAAAAA'};">1: {m['pct_home']}%</span>
                <span style="color: {'#00FF00' if favori == 'N' else '#AAAAAA'};">N: {m['pct_nul']}%</span>
                <span style="color: {'#00FF00' if favori == '2' else '#AAAAAA'};">2: {m['pct_away']}%</span>
            </div>
        </div>
        """

    # Jokers utilises
    if stats['jokers']:
        html += '<div style="color: #FFD700; font-size: 0.85em; margin-top: 10px;">'
        for j in stats['jokers']:
            icon = "⚡" if j['type'] == "DOUBLE" else "🎯"
            html += f"{icon} {j['pseudo']} "
        html += '</div>'

    return html


def get_synthese_accueil(saison_id, semaine_id):
    """
    Retourne la synthese complete pour l'accueil
    dict avec 'commentaire' et 'stats_html'
    """
    stats = get_stats_semaine(saison_id, semaine_id)
    commentaire = generer_commentaire_ironique(stats)
    stats_html = generer_synthese_html(stats, saison_id, semaine_id)

    return {
        'commentaire': commentaire,
        'stats_html': stats_html,
        'nb_joueurs': stats['nb_joueurs'],
        'matchs': stats['matchs'],
        'jokers': stats['jokers'],
        'grosses_mises': stats['grosses_mises']
    }
