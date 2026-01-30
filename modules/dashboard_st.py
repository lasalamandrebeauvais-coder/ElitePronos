"""
Module Dashboard Streamlit pour Elite Pronos
Tableau de bord principal du joueur - Version Supabase
"""
import streamlit as st
import os
from datetime import datetime, timedelta
from PIL import Image

# Import Supabase
from modules.supabase_db import get_supabase
from modules.database_manager import (
    get_countdown_j1, get_saison_label, get_saison_actuelle,
    get_journee_courante
)

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
    - Classement general
    - Forme (5 dernieres journees)
    - Jokers disponibles
    """
    supabase = get_supabase()

    stats = {
        'rang': '--',
        'total_points': 0,
        'nb_semaines': 0,
        'scores_exacts': 0,
        'forme': [],
        'jokers_doubles': 0,
        'jokers_voles': 0,
        'nb_joueurs': 0
    }

    try:
        # === 1. CLASSEMENT GENERAL ===
        # Recuperer tous les utilisateurs actifs avec leurs points
        utilisateurs = supabase.get_all_utilisateurs(statut='Actif')
        classement = []

        for u in utilisateurs:
            predictions = supabase._request('GET',
                f'predictions?user_id=eq.{u["id"]}&saison_id=eq.{saison_id}&select=points_gagnes,is_score_exact'
            ) or []

            total = sum(p.get('points_gagnes', 0) or 0 for p in predictions)
            exacts = sum(1 for p in predictions if p.get('is_score_exact'))

            classement.append({
                'id': u['id'],
                'pseudo': u['pseudo'],
                'points': total,
                'scores_exacts': exacts
            })

        # Trier par points
        classement.sort(key=lambda x: x['points'], reverse=True)
        stats['nb_joueurs'] = len(classement)

        # Trouver le rang du joueur
        for idx, joueur in enumerate(classement):
            if joueur['id'] == user_id:
                stats['rang'] = idx + 1
                stats['total_points'] = joueur['points']
                stats['scores_exacts'] = joueur['scores_exacts']
                break

        # === 2. FORME (5 dernieres journees) ===
        # Recuperer les matchs par journee
        journee_courante = get_journee_courante(saison_id)

        # Calculer les points par journee pour les 5 dernieres
        forme_data = []
        for j in range(max(1, journee_courante - 4), journee_courante + 1):
            # Recuperer les matchs de cette journee
            matchs = supabase.get_matches_journee(saison_id, j)
            if not matchs:
                continue

            match_ids = [m['id'] for m in matchs]
            match_ids_str = ','.join(map(str, match_ids))

            # Recuperer les predictions du joueur pour cette journee
            predictions = supabase._request('GET',
                f'predictions?user_id=eq.{user_id}&match_id=in.({match_ids_str})&select=points_gagnes'
            ) or []

            if predictions:
                pts_journee = sum(p.get('points_gagnes', 0) or 0 for p in predictions)
                forme_data.append({'journee': j, 'points': pts_journee})

        stats['nb_semaines'] = len(forme_data)

        # Convertir en indicateurs de forme (5 derniers)
        for fd in forme_data[-5:]:
            pts = fd['points']
            if pts >= 50:
                stats['forme'].append('up')
            elif pts >= 0:
                stats['forme'].append('stable')
            else:
                stats['forme'].append('down')

        # === 3. JOKERS DISPONIBLES ===
        stock = supabase.get_stock_jokers(user_id, saison_id)
        if not stock:
            # Initialiser le stock si absent
            stock = supabase.init_stock_jokers(user_id, saison_id)

        if stock:
            stats['jokers_doubles'] = stock.get('joker_double', 0) or 0
            stats['jokers_voles'] = stock.get('joker_vol', 0) or 0
        else:
            # Fallback si erreur d'initialisation
            stats['jokers_doubles'] = 0
            stats['jokers_voles'] = 0

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
            avatar_img = Image.open(avatar_path)
            st.image(avatar_img, width=80)
        else:
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
        if st.button("Deconnexion", type="secondary"):
            from modules.login_st import logout
            logout()
            st.session_state.page = "Connexion"
            st.rerun()

    st.markdown("---")

    # === ZONE STATISTIQUES (3 BOXES) ===
    st.markdown("### Mes Statistiques")

    col1, col2, col3 = st.columns(3)

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

    # Box 2: Forme (5 indicateurs)
    with col2:
        forme_icons = []
        for i in range(5):
            if i < len(stats['forme']):
                if stats['forme'][i] == 'up':
                    forme_icons.append('🟢')
                elif stats['forme'][i] == 'stable':
                    forme_icons.append('🟡')
                else:
                    forme_icons.append('🔴')
            else:
                forme_icons.append('⚪')

        forme_display = ' '.join(forme_icons)

        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Forme</div>
            <div style="font-size: 1.8em; margin: 10px 0;">{forme_display}</div>
            <div style="color: #AAAAAA; font-size: 0.8em;">{stats['nb_semaines']} semaines jouees</div>
        </div>
        """, unsafe_allow_html=True)

    # Box 3: Jokers
    with col3:
        # Afficher les jokers restants
        doubles_icons = "⚡" * stats['jokers_doubles'] + "<span style='color:#444;'>⚡</span>" * (3 - stats['jokers_doubles'])
        voles_icons = "🎯" * stats['jokers_voles'] + "<span style='color:#444;'>🎯</span>" * (2 - stats['jokers_voles'])

        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Jokers Disponibles</div>
            <div style="font-size: 1.5em; margin: 10px 0;">
                <span style="color: #FFD700;">{doubles_icons}</span>
            </div>
            <div style="font-size: 1.5em; margin: 5px 0;">
                <span style="color: #FFD700;">{voles_icons}</span>
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
            st.info("Module Profil en cours de developpement...")

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

    # Recuperer le joker directement
    supabase = get_supabase()
    journee = get_journee_courante(saison_id)

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
