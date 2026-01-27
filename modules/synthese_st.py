"""
Module Synthese pour Elite Pronos
Genere une synthese des paris de la semaine avec stats et ironie
Version Supabase avec debrief fin de journee
"""
import os
import random
from datetime import datetime

# Import Supabase
from modules.supabase_db import get_supabase


def get_stats_semaine(saison_id, semaine_id):
    """
    Recupere les statistiques des paris pour la semaine via Supabase
    Retourne: dict avec stats par match et stats globales
    """
    supabase = get_supabase()

    stats = {
        'matchs': [],
        'jokers': [],
        'grosses_mises': [],
        'nb_joueurs': 0,
        'nb_pronostics': 0,
        'matchs_termines': 0,
        'total_matchs': 0
    }

    # Recuperer les matchs de la semaine
    matchs = supabase.get_matches_journee(saison_id, semaine_id)
    stats['total_matchs'] = len(matchs)

    if not matchs:
        return stats

    # Compter les matchs termines
    stats['matchs_termines'] = sum(1 for m in matchs if m.get('score_final_home') is not None)

    # Recuperer toutes les predictions de la journee
    match_ids = [m['id'] for m in matchs]
    match_ids_str = ','.join(map(str, match_ids))

    predictions = supabase._request('GET',
        f'predictions?match_id=in.({match_ids_str})&select=*,utilisateurs(pseudo)'
    ) or []

    # Compter les joueurs uniques
    user_ids = set(p['user_id'] for p in predictions)
    stats['nb_joueurs'] = len(user_ids)
    stats['nb_pronostics'] = len(predictions)

    # Stats par match
    for match in matchs:
        match_id = match['id']
        home = match['equipe_home']
        away = match['equipe_away']
        score_home = match.get('score_final_home')
        score_away = match.get('score_final_away')

        # Filtrer les predictions pour ce match
        match_preds = [p for p in predictions if p['match_id'] == match_id]
        total = len(match_preds)

        if total > 0:
            votes_home = sum(1 for p in match_preds if p['score_prono_home'] > p['score_prono_away'])
            votes_away = sum(1 for p in match_preds if p['score_prono_home'] < p['score_prono_away'])
            votes_nul = sum(1 for p in match_preds if p['score_prono_home'] == p['score_prono_away'])
            mise_max = max(p.get('mise_points', 0) or 0 for p in match_preds)
            mise_moy = sum(p.get('mise_points', 0) or 0 for p in match_preds) / total

            pct_home = round(votes_home / total * 100)
            pct_away = round(votes_away / total * 100)
            pct_nul = round(votes_nul / total * 100)

            # Trouver qui a mis la mise max
            gros_parieurs = [(p['utilisateurs']['pseudo'], p['mise_points'])
                            for p in match_preds
                            if p.get('mise_points') == mise_max and p.get('utilisateurs')]
        else:
            pct_home = pct_away = pct_nul = 0
            mise_max = 0
            mise_moy = 0
            gros_parieurs = []

        stats['matchs'].append({
            'home': home,
            'away': away,
            'pct_home': pct_home,
            'pct_away': pct_away,
            'pct_nul': pct_nul,
            'mise_max': mise_max,
            'mise_moy': round(mise_moy, 1),
            'gros_parieurs': gros_parieurs,
            'score_home': score_home,
            'score_away': score_away,
            'termine': score_home is not None
        })

        # Ajouter aux grosses mises
        for pseudo, mise in gros_parieurs:
            if mise and mise >= 40:
                stats['grosses_mises'].append({
                    'pseudo': pseudo,
                    'mise': mise,
                    'match': f"{home} vs {away}"
                })

    # Recuperer les jokers utilises cette semaine
    jokers = supabase._request('GET',
        f'jokers_historique?semaine_id=eq.{semaine_id}&select=*,utilisateurs(pseudo)'
    ) or []

    for j in jokers:
        if j.get('utilisateurs'):
            stats['jokers'].append({
                'pseudo': j['utilisateurs']['pseudo'],
                'type': j.get('type_joker', 'DOUBLE')
            })

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
            break
        elif m['pct_away'] >= 70:
            phrases = [
                f"**{m['pct_away']}%** croient en {m['away']}. L'outsider devient favori !",
                f"{m['away']} a la cote ({m['pct_away']}%). Le favori va-t-il trembler ?",
            ]
            commentaires.append(random.choice(phrases))
            break
        elif m['pct_nul'] >= 40:
            commentaires.append(f"Match serre ? {m['pct_nul']}% parient sur le nul pour {m['home']} vs {m['away']}.")
            break

    # Si pas assez de commentaires, ajouter un generique
    if len(commentaires) < 2:
        generiques = [
            "Que le meilleur pronostiqueur gagne !",
            "Les cotes sont la, les pronos sont faits. Que le spectacle commence !",
            "La tension monte avant le coup d'envoi...",
        ]
        commentaires.append(random.choice(generiques))

    return " ".join(commentaires[:3])


def generer_debrief_fin_journee(stats, classement_journee):
    """
    Genere un debrief ironique quand tous les matchs sont termines
    classement_journee: liste de dict {'pseudo', 'points_journee'}
    """
    if stats['matchs_termines'] < stats['total_matchs']:
        return None  # Pas encore fini

    debrief = []

    # Trouver le meilleur de la journee
    if classement_journee:
        meilleur = classement_journee[0]
        pire = classement_journee[-1] if len(classement_journee) > 1 else None

        phrases_meilleur = [
            f"**{meilleur['pseudo']}** domine cette J avec **{meilleur['points_journee']} pts** ! Chapeau !",
            f"Le roi de la journee : **{meilleur['pseudo']}** ({meilleur['points_journee']} pts). Les autres prennent note.",
            f"**{meilleur['pseudo']}** ecrase tout avec {meilleur['points_journee']} pts cette semaine !",
        ]
        debrief.append(random.choice(phrases_meilleur))

        if pire and pire['points_journee'] < 0:
            phrases_pire = [
                f"Aie, **{pire['pseudo']}** finit dans le rouge ({pire['points_journee']} pts). Ca fait mal !",
                f"**{pire['pseudo']}** a souffert cette semaine ({pire['points_journee']} pts). La prochaine sera meilleure ?",
            ]
            debrief.append(random.choice(phrases_pire))

    # Compter les scores exacts
    nb_exacts = 0
    for m in stats['matchs']:
        if m.get('termine'):
            nb_exacts += sum(1 for p in m.get('gros_parieurs', []) if p)  # Simplification

    # Message de conclusion
    conclusions = [
        "Rendez-vous la semaine prochaine pour de nouvelles emotions !",
        "C'est termine pour cette journee. A la prochaine !",
        "Les jeux sont faits. On se retrouve a la prochaine journee !",
    ]
    debrief.append(random.choice(conclusions))

    return " ".join(debrief)


def generer_message_nouvelle_journee(journee_id, nb_matchs):
    """
    Genere un message d'intro pour une nouvelle journee
    """
    messages = [
        f"Nouvelle semaine, nouveaux defis ! J{journee_id} avec {nb_matchs} matchs au programme.",
        f"C'est parti pour la J{journee_id} ! {nb_matchs} rencontres vous attendent. Faites vos jeux !",
        f"La J{journee_id} demarre ! {nb_matchs} matchs a pronostiquer. Qui sera le meilleur ?",
        f"Bienvenue en J{journee_id} ! {nb_matchs} matchs, 100 points a repartir. A vous de jouer !",
    ]
    return random.choice(messages)


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
        elif m['pct_away'] > m['pct_home'] and m['pct_away'] > m['pct_nul']:
            favori = "2"
        else:
            favori = "N"

        # Afficher le score si termine
        score_display = ""
        if m.get('termine'):
            score_display = f"""
            <div style="text-align: center; margin-top: 5px; color: #00FF00; font-weight: bold;">
                Score: {m['score_home']} - {m['score_away']}
            </div>
            """

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
            {score_display}
        </div>
        """

    return html


def get_synthese_accueil(saison_id, semaine_id):
    """
    Retourne la synthese complete pour l'accueil
    dict avec 'commentaire', 'stats_html', 'debrief', 'message_nouvelle_journee'
    """
    stats = get_stats_semaine(saison_id, semaine_id)

    # Determiner le type de message
    if stats['nb_joueurs'] == 0 and stats['total_matchs'] > 0:
        # Nouvelle journee sans pronostics
        commentaire = generer_message_nouvelle_journee(semaine_id, stats['total_matchs'])
    elif stats['matchs_termines'] == stats['total_matchs'] and stats['total_matchs'] > 0:
        # Tous les matchs sont termines - debrief
        # Calculer le classement de la journee
        supabase = get_supabase()
        matchs = supabase.get_matches_journee(saison_id, semaine_id)
        match_ids = [m['id'] for m in matchs]
        match_ids_str = ','.join(map(str, match_ids))

        predictions = supabase._request('GET',
            f'predictions?match_id=in.({match_ids_str})&select=user_id,points_gagnes,utilisateurs(pseudo)'
        ) or []

        # Agreger par joueur
        joueurs_pts = {}
        for p in predictions:
            uid = p['user_id']
            pseudo = p['utilisateurs']['pseudo'] if p.get('utilisateurs') else 'Inconnu'
            if uid not in joueurs_pts:
                joueurs_pts[uid] = {'pseudo': pseudo, 'points_journee': 0}
            joueurs_pts[uid]['points_journee'] += p.get('points_gagnes') or 0

        classement = sorted(joueurs_pts.values(), key=lambda x: x['points_journee'], reverse=True)
        debrief = generer_debrief_fin_journee(stats, classement)
        commentaire = debrief if debrief else generer_commentaire_ironique(stats)
    else:
        commentaire = generer_commentaire_ironique(stats)

    stats_html = generer_synthese_html(stats, saison_id, semaine_id)

    return {
        'commentaire': commentaire,
        'stats_html': stats_html,
        'nb_joueurs': stats['nb_joueurs'],
        'matchs': stats['matchs'],
        'jokers': stats['jokers'],
        'grosses_mises': stats['grosses_mises'],
        'matchs_termines': stats['matchs_termines'],
        'total_matchs': stats['total_matchs']
    }


def get_debrief_rivaux(user_id, saison_id, semaine_id):
    """
    Genere un debrief specifique sur les rivaux du joueur
    """
    supabase = get_supabase()

    # Recuperer les rivaux
    rivaux_ids = supabase.get_rivaux_ids(user_id)
    if not rivaux_ids:
        return None

    # Recuperer les points de la journee pour les rivaux
    matchs = supabase.get_matches_journee(saison_id, semaine_id)
    if not matchs:
        return None

    match_ids = [m['id'] for m in matchs]
    match_ids_str = ','.join(map(str, match_ids))
    rivaux_ids_str = ','.join(map(str, rivaux_ids))

    predictions = supabase._request('GET',
        f'predictions?match_id=in.({match_ids_str})&user_id=in.({rivaux_ids_str})&select=user_id,points_gagnes,utilisateurs(pseudo)'
    ) or []

    # Agreger par rival
    rivaux_pts = {}
    for p in predictions:
        uid = p['user_id']
        pseudo = p['utilisateurs']['pseudo'] if p.get('utilisateurs') else 'Inconnu'
        if uid not in rivaux_pts:
            rivaux_pts[uid] = {'pseudo': pseudo, 'points_journee': 0}
        rivaux_pts[uid]['points_journee'] += p.get('points_gagnes') or 0

    if not rivaux_pts:
        return None

    # Trier par points
    classement_rivaux = sorted(rivaux_pts.values(), key=lambda x: x['points_journee'], reverse=True)

    # Generer le message
    meilleur = classement_rivaux[0]
    messages = [
        f"Parmi tes rivaux, **{meilleur['pseudo']}** mene avec {meilleur['points_journee']} pts cette semaine.",
        f"**{meilleur['pseudo']}** est en tete de tes rivaux ({meilleur['points_journee']} pts). Tu le laisses filer ?",
        f"Attention, **{meilleur['pseudo']}** fait {meilleur['points_journee']} pts ! Tes rivaux n'attendent pas.",
    ]

    return {
        'message': random.choice(messages),
        'classement': classement_rivaux
    }
