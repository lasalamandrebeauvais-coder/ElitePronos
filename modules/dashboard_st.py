"""
Module Dashboard Streamlit pour Elite Pronos
Tableau de bord principal du joueur avec countdown J1
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta
from PIL import Image

# Chemins
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')

# Import countdown et jokers
try:
    from modules.database_manager import (
        get_countdown_j1, get_saison_label, get_saison_actuelle,
        get_stock_jokers
    )
    HAS_MANAGER = True
except ImportError:
    HAS_MANAGER = False


def get_avatar_path(pseudo):
    """Retourne le chemin de l'avatar du joueur"""
    avatar_file = os.path.join(AVATARS_PATH, f"{pseudo}.png")
    if os.path.exists(avatar_file):
        return avatar_file
    return None


def get_user_stats(user_id):
    """Recupere les statistiques du joueur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stats = {
        'rang': '--',
        'total_points': 0,
        'nb_semaines': 0,
        'scores_exacts': 0,
        'forme': [],
        'joker_double': True,
        'joker_vole': True
    }

    try:
        # Recuperer l'historique
        cursor.execute("""
            SELECT points_gagnes, nb_scores_exacts, grand_chelem_valide
            FROM historique
            ORDER BY id DESC
            LIMIT 5
        """)
        historique = cursor.fetchall()

        if historique:
            stats['nb_semaines'] = len(historique)
            stats['total_points'] = sum(h[0] for h in historique if h[0])
            stats['scores_exacts'] = sum(h[1] for h in historique if h[1])

            # Calculer la forme (5 derniers resultats)
            for h in historique:
                pts = h[0] if h[0] else 0
                if pts >= 100:
                    stats['forme'].append('up')
                elif pts >= 50:
                    stats['forme'].append('stable')
                else:
                    stats['forme'].append('down')

        # Verifier les jokers utilises cette semaine
        cursor.execute("SELECT type FROM joker_semaine")
        joker_used = cursor.fetchone()
        if joker_used:
            if joker_used[0] == 'DOUBLE':
                stats['joker_double'] = False
            elif joker_used[0] == 'VOLE':
                stats['joker_vole'] = False

    except Exception as e:
        pass

    conn.close()
    return stats


def get_semaine_info():
    """Retourne les infos de la semaine en cours"""
    now = datetime.now()
    # Calculer le numero de semaine
    semaine_no = now.isocalendar()[1]

    # Date limite = Vendredi 20h de la semaine en cours
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
        /* Dark Mode Elite */
        .stApp {
            background: linear-gradient(180deg, #0a0a1a 0%, #0d1b2a 100%);
        }

        /* Titres dores */
        h1, h2, h3 {
            color: #FFD700 !important;
        }

        /* Box Stats */
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

        /* Avatar circulaire */
        .avatar-circle {
            border-radius: 50%;
            border: 3px solid #FFD700;
            width: 80px;
            height: 80px;
            object-fit: cover;
        }
    </style>
    """, unsafe_allow_html=True)

    # Recuperer les stats
    stats = get_user_stats(user['id'])
    semaine = get_semaine_info()

    # === HEADER ===
    header_col1, header_col2, header_col3 = st.columns([1, 4, 1])

    with header_col1:
        # Avatar
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
        st.caption(f"@{user['pseudo']}")

    with header_col3:
        if st.button("🚪 Deconnexion", type="secondary"):
            from modules.login_st import logout
            logout()
            st.session_state.page = "Connexion"
            st.rerun()

    st.markdown("---")

    # === ZONE STATISTIQUES (3 BOXES) ===
    st.markdown("### 📊 Mes Statistiques")

    col1, col2, col3 = st.columns(3)

    # Box 1: Classement
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Classement</div>
            <div class="stat-value">#{stats['rang']}</div>
            <div style="color: #888; font-size: 0.8em;">sur 100 joueurs</div>
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
            <div style="color: #888; font-size: 0.8em;">{stats['nb_semaines']} semaines jouees</div>
        </div>
        """, unsafe_allow_html=True)

    # Box 3: Jokers
    with col3:
        double_style = "color: #FFD700;" if stats['joker_double'] else "color: #444; text-decoration: line-through;"
        vole_style = "color: #FFD700;" if stats['joker_vole'] else "color: #444; text-decoration: line-through;"

        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Jokers Disponibles</div>
            <div style="font-size: 2em; margin: 10px 0;">
                <span style="{double_style}" title="Points Doubles">⚡</span>
                <span style="margin: 0 10px; color: #444;">|</span>
                <span style="{vole_style}" title="Points Voles">🎯</span>
            </div>
            <div style="color: #888; font-size: 0.7em;">⚡ Doubles | 🎯 Voles</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("")

    # === MENU NAVIGATION (4 BOUTONS) ===
    st.markdown("### 🎮 Actions")

    nav_col1, nav_col2 = st.columns(2)

    with nav_col1:
        # Bouton Pronostics
        if st.button("⚽ PRONOSTICS\n\nSaisir mes pronos", use_container_width=True, type="primary"):
            st.session_state.dashboard_section = "pronostics"
            st.rerun()

        st.markdown("")

        # Bouton Amis
        if st.button("👥 AMIS\n\nVoir mes rivaux", use_container_width=True):
            st.session_state.dashboard_section = "amis"
            st.rerun()

    with nav_col2:
        # Bouton Classement
        if st.button("🏆 CLASSEMENT\n\nVoir le ranking", use_container_width=True):
            st.session_state.dashboard_section = "classement"
            st.rerun()

        st.markdown("")

        # Bouton Profil
        if st.button("👤 PROFIL\n\nMes informations", use_container_width=True):
            st.info("Module Profil en cours de developpement...")

    # === STATS RAPIDES ===
    st.markdown("---")
    st.markdown("### 📈 Resume")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.metric("Total Points", f"{stats['total_points']:.0f}")

    with metric_col2:
        st.metric("Scores Exacts", stats['scores_exacts'])

    with metric_col3:
        st.metric("Semaines", stats['nb_semaines'])

    with metric_col4:
        st.metric("Jokers Restants", int(stats['joker_double']) + int(stats['joker_vole']))

    # === COUNTDOWN J1 ===
    if HAS_MANAGER:
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
                    SAISON {get_saison_label(get_saison_actuelle())} - COUP D'ENVOI J1
                </div>
                <div style="display: flex; justify-content: center; gap: 25px;">
                    <div>
                        <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                            {countdown['days']}
                        </div>
                        <div style="color: #888; font-size: 0.8em;">JOURS</div>
                    </div>
                    <div>
                        <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                            {countdown['hours']}
                        </div>
                        <div style="color: #888; font-size: 0.8em;">HEURES</div>
                    </div>
                    <div>
                        <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                            {countdown['minutes']}
                        </div>
                        <div style="color: #888; font-size: 0.8em;">MIN</div>
                    </div>
                </div>
                <div style="color: #aaa; font-size: 0.9em; margin-top: 10px;">
                    {countdown.get('date_j1', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # === FOOTER ===
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #888; padding: 20px;">
        <strong style="color: #FFD700;">Semaine {semaine['numero']}</strong><br>
        <span style="font-size: 0.9em;">Date limite de saisie : {semaine['date_limite']}</span>
    </div>
    """, unsafe_allow_html=True)
