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


@st.cache_data(ttl=30)
def get_debrief_rivaux(user_id, saison_id, semaine_id):
    """
    Genere un debrief specifique sur les rivaux avec bilan provisionnel (cache 30s)
    """
    supabase = get_supabase()

    # Recuperer les rivaux
    rivaux_ids = supabase.get_rivaux_ids(user_id)
    if not rivaux_ids:
        return None

    # Recuperer les matchs de la journee
    matchs = supabase.get_matches_journee(saison_id, semaine_id)
    if not matchs:
        return None

    match_ids = [m['id'] for m in matchs]
    match_ids_str = ','.join(map(str, match_ids))
    rivaux_ids_str = ','.join(map(str, rivaux_ids))

    # Predictions des rivaux
    predictions = supabase._request('GET',
        f'predictions?match_id=in.({match_ids_str})&user_id=in.({rivaux_ids_str})&select=user_id,points_gagnes,mise_bonus_gc,utilisateurs(pseudo)'
    ) or []

    # Predictions du joueur lui-meme
    user_preds = supabase._request('GET',
        f'predictions?match_id=in.({match_ids_str})&user_id=eq.{user_id}&select=points_gagnes'
    ) or []
    user_pts = round(sum(p.get('points_gagnes') or 0 for p in user_preds), 2)

    # Jokers actifs des rivaux
    jokers_rivaux = supabase._request('GET',
        f'jokers_historique?utilisateur_id=in.({rivaux_ids_str})&semaine_id=eq.{semaine_id}&select=utilisateur_id,type_joker'
    ) or []
    jokers_map = {j['utilisateur_id']: j['type_joker'] for j in jokers_rivaux}

    # Agreger par rival
    rivaux_pts = {}
    for p in predictions:
        uid = p['user_id']
        pseudo = p['utilisateurs']['pseudo'] if p.get('utilisateurs') else 'Inconnu'
        if uid not in rivaux_pts:
            rivaux_pts[uid] = {'pseudo': pseudo, 'points_journee': 0, 'bonus_gc': 0, 'uid': uid}
        rivaux_pts[uid]['points_journee'] += p.get('points_gagnes') or 0
        rivaux_pts[uid]['bonus_gc'] += p.get('mise_bonus_gc') or 0

    for v in rivaux_pts.values():
        v['points_journee'] = round(v['points_journee'], 2)
        v['joker'] = jokers_map.get(v['uid'])

    if not rivaux_pts:
        return None

    # Classement des rivaux
    classement_rivaux = sorted(rivaux_pts.values(), key=lambda x: x['points_journee'], reverse=True)
    meilleur = classement_rivaux[0]
    pire = classement_rivaux[-1]

    rivaux_devant = [v for v in classement_rivaux if v['points_journee'] > user_pts]
    rivaux_derriere = [v for v in classement_rivaux if v['points_journee'] < user_pts]
    rivaux_egalite = [v for v in classement_rivaux if v['points_journee'] == user_pts]

    nb_devant = len(rivaux_devant)
    nb_derriere = len(rivaux_derriere)
    nb_rivaux = len(classement_rivaux)

    # Stats supplementaires
    tous_negatifs = all(v['points_journee'] <= 0 for v in classement_rivaux)
    tous_positifs = all(v['points_journee'] > 0 for v in classement_rivaux)
    gc_joueurs = [v['pseudo'] for v in classement_rivaux if v['bonus_gc'] > 0]
    double_joueurs = [v['pseudo'] for v in classement_rivaux if v['joker'] == 'DOUBLE']
    vol_joueurs = [v['pseudo'] for v in classement_rivaux if v['joker'] == 'VOL']
    ecart_max = round(meilleur['points_journee'] - pire['points_journee'], 2) if nb_rivaux > 1 else 0

    # --- Phrase principale selon la situation ---
    if nb_devant == 0 and user_pts > 0:
        # Joueur en tete de ses rivaux
        phrases_tete = [
            f"T'es devant tous tes rivaux cette journee. {meilleur['pseudo']} essaie de t'accrocher avec {meilleur['points_journee']} pts, mais c'est toi qui menes. Profite.",
            f"Premier parmi tes rivaux pour l'instant. Mais ne te detends pas trop, **{meilleur['pseudo']}** est a {meilleur['points_journee']} pts et les matchs ne sont pas tous termines.",
            f"Tes rivaux sont tous dans ton sillage. **{meilleur['pseudo']}** fait {meilleur['points_journee']} pts, mais c'est encore toi le boss. Pour l'instant.",
            f"Bilan provisoire : tu domines. Tes {nb_rivaux} rivaux sont derriere toi. Le plus dangereux reste **{meilleur['pseudo']}** ({meilleur['points_journee']} pts).",
        ]
        message = random.choice(phrases_tete)
    elif nb_devant == nb_rivaux:
        # Joueur derriere tous ses rivaux
        phrases_derriere = [
            f"Tous tes rivaux sont devant toi actuellement. **{meilleur['pseudo']}** mene avec {meilleur['points_journee']} pts. C'est pas l'heure de paniquer... enfin si, un peu.",
            f"**{meilleur['pseudo']}** en tete, **{pire['pseudo']}** ferme la marche... et toi tu es ou exactement ? Derriere tout le monde. Bilan provisoire : pas glorieux.",
            f"Mauvaise nouvelle : tes {nb_rivaux} rivaux sont tous au-dessus de toi pour l'instant. **{meilleur['pseudo']}** ecrase tout ({meilleur['points_journee']} pts). Il reste des matchs, mais faut se reveiller.",
            f"Je vais pas te mentir : tu es dernier parmi tes rivaux. **{meilleur['pseudo']}** est a {meilleur['points_journee']} pts devant. L'ecart est de {round(meilleur['points_journee'] - user_pts, 2)} pts. Courage.",
        ]
        message = random.choice(phrases_derriere)
    elif nb_devant > 0 and nb_derriere > 0:
        # Dans le ventre mou
        phrases_milieu = [
            f"**{nb_devant}** rival(ux) devant toi, **{nb_derriere}** derriere. Tu es dans le ventre mou. **{meilleur['pseudo']}** mene ({meilleur['points_journee']} pts), **{pire['pseudo']}** ramasse ({pire['points_journee']} pts).",
            f"Position intermediaire : {nb_devant} rival(ux) t'ont devance pour l'instant, {nb_derriere} sont derriere. **{meilleur['pseudo']}** est la principale menace avec {meilleur['points_journee']} pts.",
            f"C'est serre. **{rivaux_devant[0]['pseudo']}** est juste au-dessus de toi ({rivaux_devant[0]['points_journee']} pts). {nb_derriere} rival(ux) derriere toi. La journee n'est pas finie.",
            f"Tu es en milieu de peloton. **{meilleur['pseudo']}** mene la danse avec {meilleur['points_journee']} pts, **{pire['pseudo']}** est en galere ({pire['points_journee']} pts). Toi ? Entre les deux.",
        ]
        message = random.choice(phrases_milieu)
    elif tous_negatifs:
        phrases_catastrophe = [
            f"Tout le monde est dans le rouge cette journee. **{meilleur['pseudo']}** limite la casse avec seulement {meilleur['points_journee']} pts. Journee noire pour tout le monde.",
            f"Carnage general. Tes rivaux souffrent autant que toi. **{pire['pseudo']}** prend la plus grosse claque ({pire['points_journee']} pts). C'est une journee a oublier pour tout le monde.",
        ]
        message = random.choice(phrases_catastrophe)
    else:
        message = f"**{meilleur['pseudo']}** mene provisoirement avec {meilleur['points_journee']} pts. Situation a surveiller."

    # --- Bilan provisionnel ---
    if user_pts > 0:
        user_bilan = f"Toi : **+{user_pts} pts**"
    elif user_pts < 0:
        user_bilan = f"Toi : **{user_pts} pts** (dans le rouge)"
    else:
        user_bilan = "Toi : **0 pts** (pas encore joue ou matchs en cours)"

    bilan_parts = [f"📊 **Bilan provisoire J{semaine_id}** — {user_bilan} | {nb_devant} rival(ux) devant, {nb_derriere} derriere."]

    if ecart_max > 0 and nb_rivaux > 1:
        bilan_parts.append(f"Ecart max entre rivaux : {ecart_max} pts.")

    message += " " + " ".join(bilan_parts)

    # --- Contexte jokers ---
    extras = []
    if gc_joueurs:
        noms_gc = ', '.join(f'**{p}**' for p in gc_joueurs)
        extras.append(random.choice([
            f"{noms_gc} joue avec le bonus Grand Chelem cette semaine. 40 pts de budget en plus, ca peut tout changer.",
            f"Attention a {noms_gc} et son bonus GC — budget etendu a 140 pts, le danger est reel.",
        ]))
    if double_joueurs:
        noms_d = ', '.join(f'**{p}**' for p in double_joueurs)
        extras.append(random.choice([
            f"{noms_d} a joue son joker DOUBLE — si la semaine se passe bien pour lui, ca va faire mal.",
            f"Le joker x2 de {noms_d} peut tout faire basculer si ses pronos sont bons.",
        ]))
    if vol_joueurs:
        noms_v = ', '.join(f'**{p}**' for p in vol_joueurs)
        extras.append(random.choice([
            f"{noms_v} a vole les pronos d'un rival — ses points dependent entierement de quelqu'un d'autre. Karma.",
            f"Joker VOL pour {noms_v} : il mise tout sur les pronos d'un autre. Risque calcule... ou pas.",
        ]))
    if extras:
        message += " " + random.choice(extras)

    return {
        'message': message,
        'classement': classement_rivaux
    }
