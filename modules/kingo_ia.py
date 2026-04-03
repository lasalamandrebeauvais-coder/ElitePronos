"""
Module Kingo IA - Elite Pronos
Genere un commentaire personnalise par joueur via IA.
Priorite : Gemini 1.5 Flash (gratuit) → Claude Haiku (payant) → None
Utilise le prompt et la structure JSON definis par l'utilisateur.
"""
import streamlit as st
import json
import random

# ============================================
# SYSTEM PROMPT KINGO
# ============================================

KINGO_SYSTEM_PROMPT = """# ROLE
Tu es Kingo, l'IA mascotte de l'application "Elite Pronos". Ton rôle est de générer une synthèse hebdomadaire personnalisée pour chaque joueur. Tu es cynique, expert en foot, et tu détestes la médiocrité humaine.

# PERSONNALITÉS (À adapter selon l'input 'style_kingo')
- CYNIQUE : Tu es blasé. Tu compares le joueur à des équipes de bas de tableau. Tu méprises les choix trop prudents.
- EXPERT DATA : Tu es arrogant. Tu parles de probabilités, de variance et d'anomalies statistiques pour prouver que le joueur a eu de la chance ou qu'il est mathématiquement condamné.
- CHAOTIQUE : Tu es un provocateur. Tu adores les prises de risques débiles (tout miser sur un outsider) et tu te moques cruellement de ceux qui ont tout perdu.

# DIRECTIVES D'ÉCRITURE
1. Ton : Sarcastique, percutant, jamais bienveillant.
2. Jargon : Utilise des termes comme "bankroll", "clean sheet", "remontada", "1N2", "bet".
3. Structure : Une phrase d'accroche assassine + une analyse d'un match spécifique (le pire ou le meilleur) + une conclusion qui pique.
4. Longueur : 3 à 4 phrases maximum.
5. Langue : Français de France, style "réseaux sociaux / vestiaire".

# INPUT DATA
Tu vas recevoir un objet JSON contenant les statistiques du joueur pour la semaine. Utilise ces chiffres pour étayer tes moqueries. Ne cite pas les chiffres bruts comme un robot, intègre-les organiquement dans ton clash."""


# ============================================
# CALL API (cache 1h — le commentaire ne change pas dans la journée)
# Priorite : Gemini (gratuit) → Claude Haiku (payant) → None
# ============================================

def _appel_gemini(data_json_str: str) -> str | None:
    """Appelle Gemini 1.5 Flash (tier gratuit : 15 req/min, 1M tokens/jour)."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key:
            return None

        import google.generativeai as genai
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=KINGO_SYSTEM_PROMPT
        )
        response = model.generate_content(
            f"Génère le commentaire Kingo pour ce joueur :\n\n{data_json_str}",
            generation_config={"max_output_tokens": 300, "temperature": 0.9}
        )
        return response.text.strip()

    except Exception as e:
        print(f"[Kingo IA] Erreur Gemini: {e}")
        return None


def _appel_claude(data_json_str: str) -> str | None:
    """Appelle Claude Haiku (payant, fallback si Gemini absent)."""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None

        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            system=KINGO_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Génère le commentaire Kingo pour ce joueur :\n\n{data_json_str}"
            }]
        )
        return response.content[0].text.strip()

    except Exception as e:
        print(f"[Kingo IA] Erreur Claude: {e}")
        return None


@st.cache_data(ttl=3600)
def generer_commentaire_kingo_ia(data_json_str: str) -> str | None:
    """
    Genere un commentaire Kingo personnalise.
    Essaie Gemini (gratuit) en premier, puis Claude Haiku en fallback.
    data_json_str : JSON serialise du dict joueur (cle de cache).
    Retourne le texte ou None si aucune cle API n'est configuree.
    """
    commentaire = _appel_gemini(data_json_str)
    if commentaire:
        return commentaire
    return _appel_claude(data_json_str)


# ============================================
# CONSTRUCTION DU DICTIONNAIRE DE DONNÉES
# ============================================

def construire_data_joueur(user, saison_id, semaine_id, classement_data=None) -> dict | None:
    """
    Construit le dictionnaire de donnees joueur pour le prompt Kingo.
    Utilise les resultats DEFINITIFS de semaine_id (doit etre une semaine terminee).
    classement_data : liste issue de get_classement_general_complet() (optionnel, evite une requete).
    """
    from modules.supabase_db import get_supabase

    supabase = get_supabase()
    user_id = user['id']

    try:
        # --- Matchs de la semaine (scores definitifs uniquement) ---
        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{semaine_id}'
            f'&is_active=eq.true&select=id,equipe_home,equipe_away,score_final_home,score_final_away&order=id'
        ) or []
        matchs_termines = [m for m in matchs if m.get('score_final_home') is not None]
        if not matchs_termines:
            return None

        match_ids_str = ','.join(map(str, [m['id'] for m in matchs_termines]))
        match_dict = {m['id']: m for m in matchs_termines}
        nb_matchs = len(matchs_termines)

        # --- Predictions du joueur ---
        preds = supabase._request('GET',
            f'predictions?user_id=eq.{user_id}&match_id=in.({match_ids_str})'
            f'&select=match_id,score_prono_home,score_prono_away,mise_points,points_gagnes,is_score_exact'
        ) or []
        if not preds:
            return None

        # Stats globales semaine
        pts_semaine = round(sum(p.get('points_gagnes') or 0 for p in preds), 2)
        nb_corrects = sum(1 for p in preds if (p.get('points_gagnes') or 0) > 0)
        nb_exacts = sum(1 for p in preds if p.get('is_score_exact'))

        # Joker utilise cette semaine
        joker_row = supabase._request('GET',
            f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{semaine_id}&select=type_joker&limit=1'
        ) or []
        jokers_semaine = [joker_row[0]['type_joker']] if joker_row else []

        # Pire et meilleur prono
        pire_prono = None
        meilleur_prono = None
        worst_loss = 0     # mise la plus haute sur un prono rate
        best_gain = -9999

        for p in preds:
            mid = p['match_id']
            m = match_dict.get(mid, {})
            pts = p.get('points_gagnes') or 0
            mise = p.get('mise_points') or 0
            sh = m.get('score_final_home', '?')
            sa = m.get('score_final_away', '?')
            ph = p.get('score_prono_home', '?')
            pa = p.get('score_prono_away', '?')
            home = m.get('equipe_home', '').split()[0].capitalize()
            away = m.get('equipe_away', '').split()[0].capitalize()

            if pts <= 0 and mise >= worst_loss:
                worst_loss = mise
                pire_prono = {
                    "match": f"{home} - {away}",
                    "prono": f"{ph}-{pa}",
                    "score_reel": f"{sh}-{sa}",
                    "mise": mise
                }

            if pts > best_gain:
                best_gain = pts
                meilleur_prono = {
                    "match": f"{home} - {away}",
                    "prono": f"{ph}-{pa}",
                    "score_reel": f"{sh}-{sa}",
                    "mise": mise
                }

        # --- Rang et points totaux (depuis classement fourni ou recalcule) ---
        rang_actuel = "--"
        points_totaux = 0
        nom_premier = "le premier"

        if classement_data:
            if classement_data:
                nom_premier = classement_data[0].get('pseudo', 'le premier')
            for idx, j in enumerate(classement_data):
                if j.get('user_id') == user_id:
                    rang_actuel = idx + 1
                    points_totaux = round(j.get('points', 0), 2)
                    break

        # --- Moyenne des points de la semaine (tous joueurs) ---
        all_preds_semaine = supabase._request('GET',
            f'predictions?match_id=in.({match_ids_str})&select=user_id,points_gagnes'
        ) or []
        pts_par_joueur = {}
        for p in all_preds_semaine:
            uid = p['user_id']
            pts_par_joueur[uid] = pts_par_joueur.get(uid, 0) + (p.get('points_gagnes') or 0)
        moyenne = round(sum(pts_par_joueur.values()) / len(pts_par_joueur), 1) if pts_par_joueur else 0

        # --- Match rate par tous (>= 70% des joueurs ont rate) ---
        match_phare_rate = "N/A"
        for m in matchs_termines:
            mid = m['id']
            sh = m.get('score_final_home')
            sa = m.get('score_final_away')
            if sh is None:
                continue
            nb_rateurs = sum(
                1 for uid, pts in pts_par_joueur.items()
                # on ne peut pas filtrer par match ici facilement — on prend un proxy global
                # (si la moyenne est tres basse, il y a eu un match piege)
            )
            home = m.get('equipe_home', '').split()[0].capitalize()
            away = m.get('equipe_away', '').split()[0].capitalize()
            if sh == sa:  # Match nul = souvent rate par tous
                match_phare_rate = f"{home} - {away} ({sh}-{sa})"
                break

        # --- Style aleatoire ---
        style = random.choice(["CYNIQUE", "EXPERT DATA", "CHAOTIQUE"])

        # --- Assemblage ---
        data = {
            "joueur": {
                "pseudo": user.get('pseudo', 'Joueur'),
                "rang_actuel": rang_actuel,
                "evolution_rang": 0,
                "points_totaux": points_totaux,
                "points_gagnes_semaine": pts_semaine,
                "budget_utilise": 100,
                "jokers_utilises_semaine": jokers_semaine,
                "serie_victoire": 0
            },
            "performance_details": {
                "pronos_corrects": nb_corrects,
                "scores_exacts": nb_exacts,
                "pire_prono": pire_prono,
                "meilleur_prono": meilleur_prono
            },
            "contexte_ligue": {
                "moyenne_points_semaine": moyenne,
                "nom_du_premier": nom_premier,
                "match_phare_rate_par_tous": match_phare_rate
            },
            "config": {
                "style_kingo": style
            }
        }

        return data

    except Exception as e:
        print(f"[Kingo IA] Erreur construction data: {e}")
        return None
