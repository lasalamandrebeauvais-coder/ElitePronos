"""
Module Dashboard Streamlit pour Elite Pronos
Tableau de bord principal du joueur - Version Supabase
"""
import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime, timedelta
from PIL import Image

# Import Supabase
from modules.supabase_db import get_supabase
from modules.database_manager import (
    get_countdown_j1, get_saison_label, get_saison_actuelle,
    get_journee_courante
)

# Cache pour les donnees lourdes (TTL 30 secondes pour mise a jour rapide)
@st.cache_data(ttl=30)
def get_classement_cache(saison_id):
    """Recupere le classement general avec cache"""
    supabase = get_supabase()

    # Une seule requete pour toutes les predictions
    all_predictions = supabase._request('GET',
        f'predictions?saison_id=eq.{saison_id}&select=user_id,points_gagnes,is_score_exact'
    ) or []

    # Agreger par utilisateur
    user_stats = {}
    for p in all_predictions:
        uid = p['user_id']
        if uid not in user_stats:
            user_stats[uid] = {'points': 0, 'exacts': 0}
        user_stats[uid]['points'] += (p.get('points_gagnes') or 0)
        if p.get('is_score_exact'):
            user_stats[uid]['exacts'] += 1

    # Recuperer les pseudos
    utilisateurs = supabase.get_all_utilisateurs(statut='Actif')

    classement = []
    for u in utilisateurs:
        uid = u['id']
        stats = user_stats.get(uid, {'points': 0, 'exacts': 0})
        classement.append({
            'id': uid,
            'pseudo': u['pseudo'],
            'points': stats['points'],
            'scores_exacts': stats['exacts']
        })

    classement.sort(key=lambda x: x['points'], reverse=True)
    return classement


@st.cache_data(ttl=30)
def get_classement_par_journee(saison_id):
    """Calcule le classement (rang) de chaque joueur a chaque journee (points cumules)"""
    supabase = get_supabase()

    all_preds = supabase._request('GET',
        f'predictions?saison_id=eq.{saison_id}&select=user_id,points_gagnes,matches(semaine_id)'
    ) or []

    # Grouper par user puis par journee
    user_journees = {}
    for p in all_preds:
        if p.get('matches'):
            uid = p['user_id']
            j = p['matches'].get('semaine_id')
            if j:
                if uid not in user_journees:
                    user_journees[uid] = {}
                user_journees[uid][j] = user_journees[uid].get(j, 0) + (p.get('points_gagnes') or 0)

    if not user_journees:
        return {}, []

    toutes_journees = sorted(set(j for uj in user_journees.values() for j in uj))

    # Pour chaque journee, calculer le cumul de chaque joueur puis classer
    # resultat: {user_id: {journee: rang}}
    rangs = {uid: {} for uid in user_journees}
    for j in toutes_journees:
        cumuls = []
        for uid in user_journees:
            cumul = sum(user_journees[uid].get(jj, 0) for jj in toutes_journees if jj <= j)
            cumuls.append((uid, cumul))
        cumuls.sort(key=lambda x: x[1], reverse=True)
        for rang, (uid, _) in enumerate(cumuls, 1):
            rangs[uid][j] = rang

    return rangs, toutes_journees

# Chemin avatars
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')


def get_avatar_path(pseudo):
    """Retourne le chemin de l'avatar du joueur"""
    avatar_file = os.path.join(AVATARS_PATH, f"{pseudo}.png")
    if os.path.exists(avatar_file):
        return avatar_file
    return None


def get_user_stats_supabase(user_id, saison_id):
    """
    Recupere les statistiques du joueur depuis Supabase
    Version optimisee avec cache
    """
    supabase = get_supabase()

    stats = {
        'rang': '--',
        'total_points': 0,
        'nb_semaines': 0,
        'scores_exacts': 0,
        'jokers_doubles': 0,
        'jokers_voles': 0,
        'nb_joueurs': 0
    }

    try:
        # === 1. CLASSEMENT (depuis cache) ===
        classement = get_classement_cache(saison_id)
        stats['nb_joueurs'] = len(classement)

        for idx, joueur in enumerate(classement):
            if joueur['id'] == user_id:
                stats['rang'] = idx + 1
                stats['total_points'] = joueur['points']
                stats['scores_exacts'] = joueur['scores_exacts']
                break

        # === 2. NB SEMAINES ===
        predictions_user = supabase._request('GET',
            f'predictions?user_id=eq.{user_id}&saison_id=eq.{saison_id}&select=match_id,matches(semaine_id)'
        ) or []

        semaines_jouees = set()
        for p in predictions_user:
            if p.get('matches'):
                j = p['matches'].get('semaine_id')
                if j:
                    semaines_jouees.add(j)
        stats['nb_semaines'] = len(semaines_jouees)

        # === 3. JOKERS ===
        stock = supabase.get_stock_jokers(user_id, saison_id)
        if stock:
            stats['jokers_doubles'] = stock.get('joker_double', 0) or 0
            stats['jokers_voles'] = stock.get('joker_vol', 0) or 0

    except Exception as e:
        print(f"Erreur get_user_stats_supabase: {e}")

    return stats


def get_semaine_info():
    """Retourne les infos de la semaine en cours"""
    now = datetime.now()
    semaine_no = now.isocalendar()[1]

    # Date limite = Vendredi 20h
    days_until_friday = (4 - now.weekday()) % 7
    if days_until_friday == 0 and now.hour >= 20:
        days_until_friday = 7
    date_limite = now + timedelta(days=days_until_friday)
    date_limite = date_limite.replace(hour=20, minute=0, second=0)

    return {
        'numero': semaine_no,
        'date_limite': date_limite.strftime("%A %d %B %H:%M")
    }


def afficher_dashboard(user):
    """Affiche le tableau de bord complet"""

    # Initialiser la section du dashboard
    if 'dashboard_section' not in st.session_state:
        st.session_state.dashboard_section = None

    # === SI UNE SECTION EST SELECTIONNEE ===
    if st.session_state.dashboard_section == "pronostics":
        from modules.pronostics_st import afficher_pronostics
        afficher_pronostics(user)
        return

    if st.session_state.dashboard_section == "classement":
        from modules.classement_st import afficher_classement
        afficher_classement(user)
        return

    if st.session_state.dashboard_section == "amis":
        from modules.amis_st import afficher_amis
        afficher_amis(user)
        return

    if st.session_state.dashboard_section == "profil":
        from modules.profil_st import afficher_profil
        afficher_profil(user)
        return

    if st.session_state.dashboard_section == "challenges":
        from modules.challenges_st import afficher_challenges
        afficher_challenges(user)
        return

    # === STYLE CSS ELITE ===
    st.markdown("""
    <style>
        .stat-box {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #FFD700;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin: 10px 0;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #FFD700;
        }
        .stat-label {
            font-size: 0.9em;
            color: #aaa;
            text-transform: uppercase;
        }
    </style>
    """, unsafe_allow_html=True)

    # Recuperer les stats depuis Supabase
    saison_id = get_saison_actuelle()
    stats = get_user_stats_supabase(user['id'], saison_id)
    semaine = get_semaine_info()

    # === HEADER ===
    header_col1, header_col2, header_col3 = st.columns([1, 4, 1])

    with header_col1:
        avatar_path = get_avatar_path(user['pseudo'])
        if avatar_path:
            try:
                avatar_img = Image.open(avatar_path)
                st.image(avatar_img, width=80)
            except Exception:
                avatar_path = None
        if not avatar_path:
            st.markdown(f"""
            <div style="
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #FFD700, #FFA500);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2em;
                color: #0a0a1a;
                font-weight: bold;
            ">{user['pseudo'][0].upper()}</div>
            """, unsafe_allow_html=True)

    with header_col2:
        prenom = user.get('prenom') or user['pseudo']
        st.markdown(f"## Bienvenue, {prenom} !")
        st.caption(f"@{user['pseudo']} - Saison {get_saison_label(saison_id)}")

    with header_col3:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.dashboard_section = None
            st.session_state.page = "Accueil"
            st.rerun()

    # === ZONE STATISTIQUES (3 BOXES) ===
    st.markdown("### Mes Statistiques")

    col1, col2, col3 = st.columns([1, 2, 1])

    # Box 1: Classement
    with col1:
        rang_display = stats['rang'] if stats['rang'] != '--' else '--'
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Classement</div>
            <div class="stat-value">#{rang_display}</div>
            <div style="color: #AAAAAA; font-size: 0.8em;">sur {stats['nb_joueurs']} joueurs</div>
        </div>
        """, unsafe_allow_html=True)

    # Box 2: Progression (classement par journee)
    with col2:
        rangs_all, journees_list = get_classement_par_journee(saison_id)
        user_rangs = rangs_all.get(user['id'], {})

        if user_rangs and journees_list:
            # Recuperer les rivaux (max 5)
            supabase_dash = get_supabase()
            rivaux_ids = supabase_dash.get_rivaux_ids(user['id'])[:5]

            # Pseudos des rivaux
            rivaux_pseudos = {}
            if rivaux_ids:
                all_users = supabase_dash.get_all_utilisateurs(statut='Actif')
                pseudo_map = {u['id']: u['pseudo'] for u in all_users}
                for rid in rivaux_ids:
                    rivaux_pseudos[rid] = pseudo_map.get(rid, '???')

            # Rang actuel du joueur
            derniere_j = journees_list[-1]
            rang_actuel = user_rangs.get(derniere_j, '--')

            # Legende HTML
            couleurs_rivaux = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#A78BFA', '#F97316']
            legende_items = '<span style="font-size:0.8em;color:#ccc;display:flex;align-items:center;gap:5px;"><span style="display:inline-block;width:16px;height:3px;background:#00FF00;border-radius:2px;"></span> Toi</span>'
            for i, rid in enumerate(rivaux_ids):
                pseudo = rivaux_pseudos.get(rid, '???')[:8]
                c = couleurs_rivaux[i]
                legende_items += f'<span style="font-size:0.8em;color:#ccc;display:flex;align-items:center;gap:5px;"><span style="display:inline-block;width:16px;height:3px;background:{c};border-radius:2px;border-top:1px dashed {c};"></span> {pseudo}</span>'

            st.markdown(f"""
            <div class="stat-box" style="padding: 12px 15px 8px 15px;">
                <div class="stat-label" style="margin-bottom: 4px;">Progression</div>
                <div class="stat-value" style="font-size: 1.8em;">#{rang_actuel}</div>
                <div style="display: flex; justify-content: center; gap: 12px; margin-top: 6px; flex-wrap: wrap;">
                    {legende_items}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Construire les donnees du joueur
            df_toi = pd.DataFrame([{'journee': j, 'Rang': user_rangs[j]} for j in journees_list if j in user_rangs])

            x_ax = alt.X('journee:O', axis=alt.Axis(
                title=None, labelAngle=0, labelColor='#888',
                labelExpr="'J' + datum.value"
            ))
            y_ax = alt.Y('Rang:Q', axis=alt.Axis(title=None, labelColor='#888'),
                         scale=alt.Scale(reverse=True))

            line_toi = alt.Chart(df_toi).mark_line(
                color='#00FF00', strokeWidth=2.5, point=True
            ).encode(x=x_ax, y=y_ax)

            layers = [line_toi]

            # Courbes des rivaux
            for i, rid in enumerate(rivaux_ids):
                rival_rangs = rangs_all.get(rid, {})
                if rival_rangs:
                    df_rival = pd.DataFrame([{'journee': j, 'Rang': rival_rangs[j]} for j in journees_list if j in rival_rangs])
                    line_rival = alt.Chart(df_rival).mark_line(
                        color=couleurs_rivaux[i], strokeWidth=1.5, strokeDash=[6, 3]
                    ).encode(x=x_ax, y=y_ax)
                    layers.append(line_rival)

            chart = alt.layer(*layers).properties(
                height=180, background='transparent'
            ).configure_view(strokeWidth=0).configure(padding=0)

            st.altair_chart(chart, use_container_width=True)
        else:
            st.markdown("""
            <div class="stat-box" style="padding: 15px;">
                <div class="stat-label">Progression</div>
                <div style="text-align: center; color: #AAAAAA; font-size: 0.85em; padding: 20px 0;">
                    Aucune donnee disponible
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Box 3: Jokers
    with col3:
        # Afficher uniquement les jokers restants (sans les gris)
        doubles_icons = "⚡ " * stats['jokers_doubles'] if stats['jokers_doubles'] > 0 else "0"
        voles_icons = "🎯 " * stats['jokers_voles'] if stats['jokers_voles'] > 0 else "0"

        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Jokers Disponibles</div>
            <div style="font-size: 1.5em; margin: 10px 0;">
                <span style="color: #FFD700;">{doubles_icons.strip()}</span>
            </div>
            <div style="font-size: 1.5em; margin: 5px 0;">
                <span style="color: #FFD700;">{voles_icons.strip()}</span>
            </div>
            <div style="color: #AAAAAA; font-size: 0.7em;">⚡ Doubles ({stats['jokers_doubles']}/3) | 🎯 Voles ({stats['jokers_voles']}/2)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("")

    # === MENU NAVIGATION (4 BOUTONS) ===
    st.markdown("### Actions")

    nav_col1, nav_col2 = st.columns(2)

    with nav_col1:
        if st.button("PRONOSTICS\n\nSaisir mes pronos", use_container_width=True, type="primary"):
            st.session_state.dashboard_section = "pronostics"
            st.rerun()

        st.markdown("")

        if st.button("MES RIVAUX\n\nVoir et suivre", use_container_width=True):
            st.session_state.dashboard_section = "amis"
            st.rerun()

    with nav_col2:
        if st.button("CLASSEMENT\n\nVoir le ranking", use_container_width=True):
            st.session_state.dashboard_section = "classement"
            st.rerun()

        st.markdown("")

        if st.button("PROFIL\n\nMes informations", use_container_width=True):
            st.session_state.dashboard_section = "profil"
            st.rerun()

    # 3eme ligne : Challenges
    st.markdown("")
    nav_col3, nav_col4 = st.columns(2)
    with nav_col3:
        if st.button("CHALLENGES\n\nMes defis", use_container_width=True):
            st.session_state.dashboard_section = "challenges"
            st.rerun()

    # === STATS RAPIDES ===
    st.markdown("---")
    st.markdown("### Resume")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.metric("Total Points", f"{stats['total_points']:.0f}")

    with metric_col2:
        st.metric("Scores Exacts", stats['scores_exacts'])

    with metric_col3:
        st.metric("Semaines", stats['nb_semaines'])

    with metric_col4:
        jokers_restants = stats['jokers_doubles'] + stats['jokers_voles']
        st.metric("Jokers Restants", jokers_restants)

    # === MES PRONOSTICS DE LA JOURNEE ===
    st.markdown("---")
    st.markdown("### Mes pronostics")

    # Recuperer le joker directement (meme requete que sauvegarde)
    supabase = get_supabase()
    saisons_data = supabase._request('GET', 'saisons?is_active=eq.true&select=journee_courante')
    journee = saisons_data[0].get('journee_courante', 1) if saisons_data else 1

    joker_data = supabase._request('GET',
        f'jokers_historique?utilisateur_id=eq.{user["id"]}&semaine_id=eq.{journee}&select=type_joker,cible_vol_id'
    )

    if joker_data and len(joker_data) > 0:
        type_joker = joker_data[0].get('type_joker')
        if type_joker == 'DOUBLE':
            st.info("⚡ **Points Doubles** joue cette semaine")
        elif type_joker == 'VOL':
            cible_id = joker_data[0].get('cible_vol_id')
            cible_pseudo = "???"
            if cible_id:
                cible_user = supabase._request('GET', f'utilisateurs?id=eq.{cible_id}&select=pseudo')
                if cible_user and len(cible_user) > 0:
                    cible_pseudo = cible_user[0].get('pseudo', '???')
            st.info(f"🎯 **Points Voles** joue cette semaine sur **{cible_pseudo}**")

    # Recuperer et afficher les pronostics
    from modules.pronostics_st import get_pronos_existants, get_matchs_semaine
    pronos = get_pronos_existants(user['id'])
    matchs = get_matchs_semaine()

    if pronos and matchs:

        # Afficher les pronostics en compact
        for match in matchs:
            match_id = match[0]
            home = match[2]
            away = match[3]
            if match_id in pronos:
                p = pronos[match_id]
                st.markdown(f"""
                <div style="
                    background: #0A183D;
                    border: 1px solid #333;
                    border-radius: 6px;
                    padding: 8px 12px;
                    margin: 4px 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 0.85em;
                ">
                    <span style="color: #FFF; flex: 1;">{home}</span>
                    <span style="color: #4488FF; font-weight: bold; margin: 0 10px;">{p['home']} - {p['away']}</span>
                    <span style="color: #FFF; flex: 1; text-align: right;">{away}</span>
                    <span style="color: #00FF00; margin-left: 15px; font-weight: bold;">{p['mise']}pts</span>
                </div>
                """, unsafe_allow_html=True)

    # === COUNTDOWN J1 ===
    countdown = get_countdown_j1()
    if countdown and not countdown.get('passed', True):
        st.markdown("---")
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #FFD700;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin: 10px 0;
        ">
            <div style="color: #FFD700; font-size: 1.1em; margin-bottom: 10px;">
                SAISON {get_saison_label(saison_id)} - COUP D'ENVOI J1
            </div>
            <div style="display: flex; justify-content: center; gap: 25px;">
                <div>
                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                        {countdown['days']}
                    </div>
                    <div style="color: #AAAAAA; font-size: 0.8em;">JOURS</div>
                </div>
                <div>
                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                        {countdown['hours']}
                    </div>
                    <div style="color: #AAAAAA; font-size: 0.8em;">HEURES</div>
                </div>
                <div>
                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                        {countdown['minutes']}
                    </div>
                    <div style="color: #AAAAAA; font-size: 0.8em;">MIN</div>
                </div>
            </div>
            <div style="color: #aaa; font-size: 0.9em; margin-top: 10px;">
                {countdown.get('date_j1', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # === FOOTER ===
    st.markdown("---")
    journee = get_journee_courante(saison_id)
    st.markdown(f"""
    <div style="text-align: center; color: #AAAAAA; padding: 20px;">
        <strong style="color: #FFD700;">Journee {journee}</strong> - Saison {get_saison_label(saison_id)}<br>
        <span style="font-size: 0.9em;">Date limite de saisie : {semaine['date_limite']}</span>
    </div>
    """, unsafe_allow_html=True)
