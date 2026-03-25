"""
Module Synthese pour Elite Pronos
Genere une synthese des paris de la semaine avec stats et ironie
Version Supabase avec debrief fin de journee
"""
import random
import streamlit as st

# Import Supabase
from modules.supabase_db import get_supabase


@st.cache_data(ttl=30)
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
        f'jokers_historique?semaine_id=eq.{semaine_id}&select=*,utilisateurs!utilisateur_id(pseudo)'
    ) or []

    seen = set()
    for j in jokers:
        uid = j.get('utilisateur_id')
        if j.get('utilisateurs') and uid not in seen:
            seen.add(uid)
            stats['jokers'].append({
                'pseudo': j['utilisateurs']['pseudo'],
                'type': j.get('type_joker', 'DOUBLE')
            })

    return stats


def generer_commentaire_ironique(stats):
    """
    Genere un commentaire specifique base sur les stats reelles.
    AVANT DEADLINE: Kingo reste evasif (pas de noms, pas de details sur les joueurs)
    APRES DEADLINE: Kingo peut reveler les infos joueurs
    Les % de votes sont toujours OK (anonymes).
    """
    commentaires = []

    # Deadline passee = au moins 1 match termine
    deadline_passee = stats.get('matchs_termines', 0) > 0

    # Commentaire sur le nombre de joueurs
    nb = stats['nb_joueurs']
    if nb == 0:
        return "Personne n'a encore joue cette semaine. Vous attendez quoi ? Que les matchs se jouent sans vous ?"
    elif nb == 1:
        commentaires.append("Un seul brave a ose jouer pour l'instant. Les autres ont peur ou quoi ?")
    elif nb < 5:
        commentaires.append(f"Seulement {nb} joueurs ont fait leurs pronos. Les absents ont toujours tort !")

    # Trouver le match le plus polarise (votes les plus extremes)
    match_unanime = None
    max_pct = 0
    match_serre = None
    min_ecart = 100

    for m in stats['matchs']:
        pcts = [m['pct_home'], m['pct_away'], m['pct_nul']]
        top_pct = max(pcts)
        ecart = top_pct - sorted(pcts)[-2] if len(pcts) > 1 else 100

        if top_pct > max_pct:
            max_pct = top_pct
            match_unanime = m
        if ecart < min_ecart:
            min_ecart = ecart
            match_serre = m

    # Commentaire sur les votes - specifique aux vrais matchs
    if match_unanime and max_pct >= 65:
        m = match_unanime
        if m['pct_home'] >= 65:
            commentaires.append(
                f"**{m['pct_home']}%** misent sur {m['home']} contre {m['away']}. "
                f"Unanimite ou piege ?"
            )
        elif m['pct_away'] >= 65:
            commentaires.append(
                f"**{m['pct_away']}%** croient en {m['away']} face a {m['home']}. "
                f"Le favori va-t-il trembler ?"
            )
        elif m['pct_nul'] >= 40:
            commentaires.append(
                f"**{m['pct_nul']}%** parient sur le nul pour {m['home']}-{m['away']}. "
                f"Match ferme en vue ?"
            )
    elif match_serre and min_ecart <= 15:
        m = match_serre
        commentaires.append(
            f"{m['home']}-{m['away']} divise les pronostiqueurs : "
            f"{m['pct_home']}% / {m['pct_nul']}% / {m['pct_away']}%. Qui a raison ?"
        )

    # Commentaire sur les grosses mises
    if stats['grosses_mises']:
        if deadline_passee:
            gros = stats['grosses_mises'][0]
            commentaires.append(
                f"**{gros['pseudo']}** a mise gros ({gros['mise']} pts) "
                f"sur {gros['match']}. Confiance ou folie ?"
            )
        else:
            nb_gros = len(stats['grosses_mises'])
            if nb_gros == 1:
                commentaires.append(
                    "Quelqu'un a sorti l'artillerie lourde cette semaine... Mais qui ?"
                )
            else:
                commentaires.append(
                    f"{nb_gros} joueurs ont place des mises a 40+ pts. Ca va chauffer !"
                )

    # Commentaire sur les jokers
    if stats['jokers']:
        joker = stats['jokers'][0]
        if deadline_passee:
            type_label = "Points Doubles" if joker['type'] == 'DOUBLE' else "Vol de pronostics"
            commentaires.append(
                f"**{joker['pseudo']}** a joue son joker {type_label}. "
                f"Ca passe ou ca casse !"
            )
        else:
            nb_jokers = len(stats['jokers'])
            if nb_jokers == 1:
                commentaires.append(
                    "Un joker a ete active cette semaine... Lequel et par qui ? Mystere !"
                )
            else:
                commentaires.append(
                    f"{nb_jokers} jokers actives cette semaine ! Les strategies se devoilent..."
                )

    # Si pas assez de commentaires, mentionner un match a venir
    if len(commentaires) < 2:
        matchs_a_venir = [m for m in stats['matchs'] if not m.get('termine')]
        if matchs_a_venir:
            m = matchs_a_venir[0]
            commentaires.append(
                f"A suivre : {m['home']} vs {m['away']}. Faites vos jeux !"
            )
        elif deadline_passee:
            commentaires.append("Les resultats tombent, qui avait raison ?")
        else:
            commentaires.append("Que le meilleur pronostiqueur gagne !")

    return " ".join(commentaires[:3])


def generer_debrief_fin_journee(stats, classement_journee, jokers_enrichis=None):
    """
    Genere un debrief specifique quand tous les matchs sont termines.
    Ligne 1: fait marquant match (surprise, festival de buts)
    Ligne 2: fait marquant joueur (grand chelem, score exact, champion, joker, dernier)
    """
    if stats['matchs_termines'] < stats['total_matchs']:
        return None  # Pas encore fini

    debrief = []
    jokers_enrichis = jokers_enrichis or []

    # === LIGNE 1 : Fait marquant match ===
    # Trouver le match le plus surprenant
    match_surprise = None
    min_pct_correct = 100
    match_buts = None
    max_buts = 0

    for m in stats['matchs']:
        if not m.get('termine'):
            continue
        sh, sa = m['score_home'], m['score_away']
        total_buts = (sh or 0) + (sa or 0)

        # Determiner le resultat reel et le % qui l'avait predit
        if sh > sa:
            pct_correct = m['pct_home']
        elif sa > sh:
            pct_correct = m['pct_away']
        else:
            pct_correct = m['pct_nul']

        if pct_correct < min_pct_correct:
            min_pct_correct = pct_correct
            match_surprise = m

        if total_buts > max_buts:
            max_buts = total_buts
            match_buts = m

    if match_surprise and min_pct_correct <= 30:
        sh, sa = match_surprise['score_home'], match_surprise['score_away']
        if sh > sa:
            gagnant = match_surprise['home']
        elif sa > sh:
            gagnant = match_surprise['away']
        else:
            gagnant = "le nul"
        debrief.append(
            f"Surprise : {gagnant} l'emporte ({sh}-{sa}), "
            f"seulement {min_pct_correct}% y croyaient !"
        )
    elif match_buts and max_buts >= 5:
        m = match_buts
        debrief.append(
            f"Festival de buts sur {m['home']}-{m['away']} "
            f"({m['score_home']}-{m['score_away']}) !"
        )
    elif match_surprise:
        m = match_surprise
        debrief.append(
            f"{m['home']} {m['score_home']}-{m['score_away']} {m['away']}, "
            f"match serre comme les pronos."
        )

    # === LIGNE 2 : Fait marquant joueur (par priorite) ===
    if classement_journee:
        meilleur = classement_journee[0]
        pire = classement_journee[-1] if len(classement_journee) > 1 else None

        # 1. Grand Chelem
        grand_chelem = next((j for j in classement_journee if j.get('grand_chelem')), None)
        if grand_chelem:
            nb = stats['total_matchs']
            debrief.append(
                f"**{grand_chelem['pseudo']}** signe un Grand Chelem "
                f"({nb}/{nb}), tous les pronos bons !"
            )
        # 2. Score exact
        elif any(j.get('scores_exacts', 0) > 0 for j in classement_journee):
            joueur_exact = next(j for j in classement_journee if j.get('scores_exacts', 0) > 0)
            match_name = joueur_exact.get('score_exact_matchs', [''])[0]
            if joueur_exact['scores_exacts'] > 1:
                debrief.append(
                    f"**{joueur_exact['pseudo']}** a tape {joueur_exact['scores_exacts']} "
                    f"scores exacts ! Visionnaire."
                )
            else:
                debrief.append(
                    f"**{joueur_exact['pseudo']}** a tape le score exact "
                    f"sur {match_name} !"
                )
        # 3. Joker double reussi
        elif any(j.get('reussi') and j.get('type') == 'DOUBLE' for j in jokers_enrichis):
            joker_ok = next(j for j in jokers_enrichis if j.get('reussi') and j.get('type') == 'DOUBLE')
            debrief.append(
                f"**{joker_ok['pseudo']}** a double la mise et ca a paye "
                f"({joker_ok['points']} pts) !"
            )
        # 4. Champion de la journee
        elif meilleur:
            debrief.append(
                f"**{meilleur['pseudo']}** domine avec "
                f"**{meilleur['points_journee']} pts** cette journee !"
            )

        # Bonus : dernier dans le rouge
        if pire and pire['points_journee'] < 0 and len(debrief) < 3:
            debrief.append(
                f"**{pire['pseudo']}** ferme la marche a {pire['points_journee']} pts."
            )

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
            score_display = f'<div style="text-align:center;margin-top:5px;color:#00FF00;font-weight:bold;">Score: {m["score_home"]} - {m["score_away"]}</div>'

        color_1 = '#00FF00' if favori == '1' else '#AAAAAA'
        color_n = '#00FF00' if favori == 'N' else '#AAAAAA'
        color_2 = '#00FF00' if favori == '2' else '#AAAAAA'

        html += f'<div style="background:#002040;border-radius:8px;padding:10px;margin:8px 0;">'
        html += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
        html += f'<span style="color:#FFFFFF;font-size:0.9em;">{m["home"]}</span>'
        html += f'<span style="color:#D4AF37;font-weight:bold;">vs</span>'
        html += f'<span style="color:#FFFFFF;font-size:0.9em;">{m["away"]}</span></div>'
        html += f'<div style="display:flex;justify-content:space-around;font-size:0.85em;">'
        html += f'<span style="color:{color_1};">1: {m["pct_home"]}%</span>'
        html += f'<span style="color:{color_n};">N: {m["pct_nul"]}%</span>'
        html += f'<span style="color:{color_2};">2: {m["pct_away"]}%</span></div>'
        html += score_display
        html += '</div>'

    return html


@st.cache_data(ttl=30)
def get_synthese_accueil(saison_id, semaine_id):
    """
    Retourne la synthese complete pour l'accueil (cache 30s)
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
            f'predictions?match_id=in.({match_ids_str})&select=user_id,points_gagnes,is_score_exact,match_id,utilisateurs(pseudo)'
        ) or []

        total_matchs = len(matchs)

        # Agreger par joueur avec stats detaillees
        joueurs_pts = {}
        for p in predictions:
            uid = p['user_id']
            pseudo = p['utilisateurs']['pseudo'] if p.get('utilisateurs') else 'Inconnu'
            if uid not in joueurs_pts:
                joueurs_pts[uid] = {
                    'pseudo': pseudo,
                    'points_journee': 0,
                    'scores_exacts': 0,
                    'bons_pronos': 0,
                    'score_exact_matchs': []
                }
            pts = p.get('points_gagnes') or 0
            joueurs_pts[uid]['points_journee'] += pts
            if p.get('is_score_exact'):
                joueurs_pts[uid]['scores_exacts'] += 1
                # Trouver le match correspondant pour le nom
                mid = p.get('match_id')
                for m in matchs:
                    if m['id'] == mid:
                        joueurs_pts[uid]['score_exact_matchs'].append(
                            f"{m['equipe_home']} vs {m['equipe_away']}"
                        )
                        break
            if pts > 0:
                joueurs_pts[uid]['bons_pronos'] += 1

        # Arrondir les points et detecter grand chelem
        for v in joueurs_pts.values():
            v['points_journee'] = round(v['points_journee'], 2)
            v['grand_chelem'] = v['bons_pronos'] == total_matchs and total_matchs > 0

        # Croiser jokers avec resultats
        jokers_enrichis = []
        for j in stats['jokers']:
            pseudo = j['pseudo']
            # Trouver les points du joueur
            joueur_data = next((v for v in joueurs_pts.values() if v['pseudo'] == pseudo), None)
            pts = joueur_data['points_journee'] if joueur_data else 0
            jokers_enrichis.append({
                **j,
                'points': pts,
                'reussi': pts > 0
            })

        classement = sorted(joueurs_pts.values(), key=lambda x: x['points_journee'], reverse=True)
        debrief = generer_debrief_fin_journee(stats, classement, jokers_enrichis)
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


@st.cache_data(ttl=300)
def get_debrief_rivaux(user_id, saison_id, semaine_id):
    """
    Genere un debrief sur les rivaux base sur les resultats DEFINITIFS de la semaine precedente.
    Focus sur le JEU : bons pronos, scores exacts, mises, anecdotes — pas juste les points.
    """
    if semaine_id < 1:
        return None

    supabase = get_supabase()

    # Abreviations equipes
    _ABBR = {
        'paris saint-germain fc': 'PSG', 'paris saint-germain': 'PSG', 'paris sg': 'PSG',
        'olympique de marseille': 'OM', 'olympique lyonnais': 'OL',
        'rc lens': 'Lens', 'losc lille': 'Lille', 'losc': 'Lille',
        'as monaco fc': 'Monaco', 'as monaco': 'Monaco',
        'stade rennais fc 1901': 'Rennes', 'stade rennais fc': 'Rennes', 'stade rennais': 'Rennes',
        'stade brestois 29': 'Brest', 'toulouse fc': 'TFC', 'ogc nice': 'Nice',
        'montpellier hsc': 'MHSC', 'angers sco': 'Angers', 'fc nantes': 'Nantes',
        'aj auxerre': 'Auxerre', 'rc strasbourg alsace': 'Strasbourg',
        'as saint-etienne': 'ASSE', 'stade de reims': 'Reims', 'le havre ac': 'Le Havre',
        'manchester united fc': 'Man Utd', 'manchester city fc': 'Man City',
        'fc barcelona': 'Barca', 'real madrid cf': 'Real', 'arsenal fc': 'Arsenal',
        'liverpool fc': 'Liverpool', 'chelsea fc': 'Chelsea', 'tottenham hotspur fc': 'Spurs',
        'fc bayern münchen': 'Bayern', 'borussia dortmund': 'Dortmund',
        'juventus fc': 'Juve', 'ac milan': 'Milan', 'inter milan': 'Inter',
        'ssc napoli': 'Napoli', 'atletico madrid': 'Atletico',
    }
    def _abbr(nom):
        return _ABBR.get(nom.lower(), nom.split()[0].capitalize())

    # Rivaux
    rivaux_ids = supabase.get_rivaux_ids(user_id)
    if not rivaux_ids:
        return None

    # Matchs de la semaine (tous, pour avoir les scores)
    matchs = supabase._request('GET',
        f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{semaine_id}&is_active=eq.true&select=id,equipe_home,equipe_away,score_final_home,score_final_away&order=id'
    ) or []
    matchs_termines = [m for m in matchs if m.get('score_final_home') is not None]
    if not matchs_termines:
        return None

    match_ids = [m['id'] for m in matchs_termines]
    match_ids_str = ','.join(map(str, match_ids))
    rivaux_ids_str = ','.join(map(str, rivaux_ids))
    match_dict = {m['id']: m for m in matchs_termines}
    nb_matchs = len(match_ids)

    # Predictions des rivaux avec detail complet
    predictions_rivaux = supabase._request('GET',
        f'predictions?match_id=in.({match_ids_str})&user_id=in.({rivaux_ids_str})&select=user_id,match_id,score_prono_home,score_prono_away,mise_points,points_gagnes,is_score_exact,utilisateurs(pseudo)'
    ) or []

    # Predictions de l'utilisateur (pour se comparer)
    user_preds = supabase._request('GET',
        f'predictions?match_id=in.({match_ids_str})&user_id=eq.{user_id}&select=match_id,score_prono_home,score_prono_away,mise_points,points_gagnes,is_score_exact'
    ) or []
    user_pts = round(sum(p.get('points_gagnes') or 0 for p in user_preds), 2)
    user_bons = sum(1 for p in user_preds if (p.get('points_gagnes') or 0) > 0)
    user_exacts = sum(1 for p in user_preds if p.get('is_score_exact'))

    # Jokers utilises par les rivaux cette semaine
    jokers_rivaux = supabase._request('GET',
        f'jokers_historique?utilisateur_id=in.({rivaux_ids_str})&semaine_id=eq.{semaine_id}&select=utilisateur_id,type_joker'
    ) or []
    jokers_map = {j['utilisateur_id']: j['type_joker'] for j in jokers_rivaux}

    # Agreger par rival
    rivaux_data = {}
    for p in predictions_rivaux:
        uid = p['user_id']
        pseudo = (p.get('utilisateurs') or {}).get('pseudo', 'Inconnu')
        if uid not in rivaux_data:
            rivaux_data[uid] = {
                'uid': uid, 'pseudo': pseudo,
                'pts': 0, 'nb_bons': 0, 'nb_exacts': 0,
                'grosse_mise': 0, 'grosse_mise_match': None,
                'exact_match': None,
                'pronos_bizarres': [],
            }
        mid = p['match_id']
        match = match_dict.get(mid, {})
        pts = p.get('points_gagnes') or 0
        mise = p.get('mise_points') or 0
        ph = p.get('score_prono_home')
        pa = p.get('score_prono_away')
        sh = match.get('score_final_home')
        sa = match.get('score_final_away')
        home_abbr = _abbr(match.get('equipe_home', ''))
        away_abbr = _abbr(match.get('equipe_away', ''))

        rivaux_data[uid]['pts'] += pts
        if pts > 0:
            rivaux_data[uid]['nb_bons'] += 1
        if p.get('is_score_exact'):
            rivaux_data[uid]['nb_exacts'] += 1
            if rivaux_data[uid]['exact_match'] is None:
                rivaux_data[uid]['exact_match'] = f"{home_abbr}-{away_abbr} ({sh}-{sa})"
        if mise > rivaux_data[uid]['grosse_mise']:
            rivaux_data[uid]['grosse_mise'] = mise
            rivaux_data[uid]['grosse_mise_match'] = f"{home_abbr}-{away_abbr}"
            rivaux_data[uid]['grosse_mise_bon'] = pts > 0
        # Prono bizarre : grosse diff de score (ex: 5-0, 0-4...)
        if ph is not None and pa is not None and abs(ph - pa) >= 4:
            rivaux_data[uid]['pronos_bizarres'].append(f"{ph}-{pa} sur {home_abbr}-{away_abbr}")

    for v in rivaux_data.values():
        v['pts'] = round(v['pts'], 2)
        v['joker'] = jokers_map.get(v['uid'])

    if not rivaux_data:
        return None

    classement_rivaux = sorted(rivaux_data.values(), key=lambda x: x['pts'], reverse=True)
    meilleur_jeu = max(classement_rivaux, key=lambda x: (x['nb_bons'], x['nb_exacts']))
    pire_jeu = min(classement_rivaux, key=lambda x: (x['nb_bons'], x['nb_exacts']))
    nb_rivaux = len(classement_rivaux)
    rivaux_devant = [v for v in classement_rivaux if v['pts'] > user_pts]
    rivaux_derriere = [v for v in classement_rivaux if v['pts'] < user_pts]
    nb_devant = len(rivaux_devant)
    nb_derriere = len(rivaux_derriere)

    double_joueurs = [v['pseudo'] for v in classement_rivaux if v['joker'] == 'DOUBLE']
    vol_joueurs = [v['pseudo'] for v in classement_rivaux if v['joker'] == 'VOL']

    # --- Construction du message centre sur le JEU ---
    parties = []

    # 1. Meilleur joueur cote jeu
    if meilleur_jeu['nb_bons'] == nb_matchs:
        phrases = [
            f"**{meilleur_jeu['pseudo']}** a tout vu venir — {nb_matchs}/{nb_matchs} bons pronos. Parfait.",
            f"Semaine parfaite pour **{meilleur_jeu['pseudo']}** : {nb_matchs} pronos, {nb_matchs} bons. Rien a redire.",
        ]
        parties.append(random.choice(phrases))
    elif meilleur_jeu['nb_exacts'] >= 2:
        parties.append(random.choice([
            f"**{meilleur_jeu['pseudo']}** a cartonne avec {meilleur_jeu['nb_bons']}/{nb_matchs} bons pronos et {meilleur_jeu['nb_exacts']} scores exacts. Il lit les matchs.",
            f"Belle lecture de **{meilleur_jeu['pseudo']}** : {meilleur_jeu['nb_exacts']} scores exacts et {meilleur_jeu['nb_bons']} bons sur {nb_matchs}. Chapeau.",
        ]))
    elif meilleur_jeu['nb_exacts'] == 1 and meilleur_jeu['exact_match']:
        parties.append(random.choice([
            f"**{meilleur_jeu['pseudo']}** s'en sort avec {meilleur_jeu['nb_bons']}/{nb_matchs} et un score exact sur {meilleur_jeu['exact_match']}. Bonne semaine.",
            f"{meilleur_jeu['nb_bons']} bons pronos pour **{meilleur_jeu['pseudo']}**, et il a cloue le score exact de {meilleur_jeu['exact_match']}.",
        ]))
    elif meilleur_jeu['nb_bons'] > 0:
        parties.append(random.choice([
            f"**{meilleur_jeu['pseudo']}** s'en tire le mieux avec {meilleur_jeu['nb_bons']}/{nb_matchs} pronos corrects.",
            f"Meilleure lecture de la semaine : **{meilleur_jeu['pseudo']}** avec {meilleur_jeu['nb_bons']}/{nb_matchs}.",
        ]))

    # 2. Pire joueur cote jeu (si different)
    if pire_jeu['uid'] != meilleur_jeu['uid']:
        if pire_jeu['nb_bons'] == 0:
            parties.append(random.choice([
                f"A l'inverse, **{pire_jeu['pseudo']}** n'a rien touche : 0/{nb_matchs}. Semaine a oublier.",
                f"**{pire_jeu['pseudo']}** peut rentrer chez lui : 0 bon prono sur {nb_matchs}. Brutal.",
            ]))
        elif pire_jeu['nb_bons'] == 1:
            parties.append(random.choice([
                f"**{pire_jeu['pseudo']}** n'a sauve qu'un seul prono sur {nb_matchs}. Pas la semaine.",
                f"Galere pour **{pire_jeu['pseudo']}** : 1/{nb_matchs} seulement.",
            ]))

    # 3. Scores exacts marquants (hors meilleur_jeu)
    autres_exacts = [v for v in classement_rivaux if v['nb_exacts'] > 0 and v['uid'] != meilleur_jeu['uid'] and v['exact_match']]
    if autres_exacts:
        v = autres_exacts[0]
        parties.append(random.choice([
            f"**{v['pseudo']}** a aussi touche un score exact : {v['exact_match']}.",
            f"Petit exploit de **{v['pseudo']}** avec le score exact de {v['exact_match']}.",
        ]))

    # 4. Gros parieur (mise >= 50)
    gros_miseurs = [v for v in classement_rivaux if v['grosse_mise'] >= 50 and v['grosse_mise_match']]
    if gros_miseurs:
        v = gros_miseurs[0]
        if v['grosse_mise_bon']:
            parties.append(random.choice([
                f"**{v['pseudo']}** a joue {v['grosse_mise']} pts sur {v['grosse_mise_match']} — et c'est passe. Audacieux.",
                f"Belle confiance de **{v['pseudo']}** : {v['grosse_mise']} pts sur {v['grosse_mise_match']}, bien joue.",
            ]))
        else:
            parties.append(random.choice([
                f"**{v['pseudo']}** a balance {v['grosse_mise']} pts sur {v['grosse_mise_match']}... et ca n'a pas marche. Ca fait mal.",
                f"**{v['pseudo']}** a tente le tout pour le tout ({v['grosse_mise']} pts sur {v['grosse_mise_match']}). Mauvais pari.",
            ]))

    # 5. Prono bizarre
    for v in classement_rivaux:
        if v['pronos_bizarres']:
            parties.append(random.choice([
                f"**{v['pseudo']}** a joue {v['pronos_bizarres'][0]}. Original.",
                f"Curieux prono de **{v['pseudo']}** : {v['pronos_bizarres'][0]}. On en parle pas.",
            ]))
            break

    # 6. Jokers
    if double_joueurs:
        noms_d = ', '.join(f'**{p}**' for p in double_joueurs)
        match_d = next((v for v in classement_rivaux if v['pseudo'] in double_joueurs), None)
        if match_d and match_d['nb_bons'] >= 2:
            parties.append(f"{noms_d} avait le joker x2 — {match_d['nb_bons']}/{nb_matchs} bons pronos, ca lui a bien servi.")
        elif match_d and match_d['nb_bons'] <= 1:
            parties.append(f"{noms_d} avait le joker x2 mais seulement {match_d['nb_bons']}/{nb_matchs} bon(s) prono(s). Dommage.")
        else:
            parties.append(f"{noms_d} jouait avec le joker Points Doubles.")
    if vol_joueurs:
        noms_v = ', '.join(f'**{p}**' for p in vol_joueurs)
        parties.append(f"{noms_v} avait vole les pronos d'un rival — ses resultats ne lui appartenaient meme pas.")

    message = " ".join(parties) if parties else f"Semaine en demi-teinte pour tes rivaux — personne ne s'est vraiment distingue."

    # --- Bilan final ---
    user_bilan = f"Toi : **{user_bons}/{nb_matchs}**"
    if user_exacts > 0:
        user_bilan += f" dont {user_exacts} exact(s) 🎯"
    bilan = f"\n\n📊 **Recap J{semaine_id}** — {user_bilan} | {nb_devant} rival(ux) devant, {nb_derriere} derriere."
    message += bilan

    return {
        'message': message,
        'classement': classement_rivaux
    }
