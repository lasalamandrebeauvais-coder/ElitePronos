"""
Module Classement Streamlit pour Elite Pronos
Classements avec 4 onglets : Général, Ma Semaine, Records, Assiduité
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime

# Chemins
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')


def get_avatar_path(pseudo):
    """Retourne le chemin de l'avatar du joueur"""
    avatar_file = os.path.join(AVATARS_PATH, f"{pseudo}.png")
    if os.path.exists(avatar_file):
        return avatar_file
    return None


def get_classement_general():
    """Récupère le classement général (cumul total des points)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # La table pronostics n'a pas de colonne utilisateur_id
        # On utilise la table predictions si elle existe, sinon fallback
        cursor.execute("""
            SELECT u.id, u.pseudo, u.prenom,
                   COALESCE(SUM(p.points_gagnes), 0) as total_points
            FROM utilisateurs u
            LEFT JOIN predictions p ON u.id = p.user_id
            WHERE u.statut = 'Actif'
            GROUP BY u.id, u.pseudo, u.prenom
            ORDER BY total_points DESC
        """)
        classement = cursor.fetchall()
    except Exception:
        # Fallback: juste les utilisateurs avec 0 points
        cursor.execute("""
            SELECT id, pseudo, prenom, 0 as total_points
            FROM utilisateurs
            WHERE statut = 'Actif'
            ORDER BY pseudo
        """)
        classement = cursor.fetchall()
    finally:
        conn.close()
    return classement


def get_classement_semaine():
    """Récupère le classement de la semaine en cours"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    semaine_actuelle = datetime.now().isocalendar()[1]

    try:
        cursor.execute("""
            SELECT u.id, u.pseudo, u.prenom,
                   COALESCE(SUM(p.points_gagnes), 0) as points_semaine
            FROM utilisateurs u
            LEFT JOIN predictions p ON u.id = p.user_id
            LEFT JOIN matches m ON p.match_id = m.id AND m.semaine_id = ?
            WHERE u.statut = 'Actif'
            GROUP BY u.id, u.pseudo, u.prenom
            ORDER BY points_semaine DESC
        """, (semaine_actuelle,))
        classement = cursor.fetchall()
    except Exception:
        cursor.execute("""
            SELECT id, pseudo, prenom, 0 as points_semaine
            FROM utilisateurs
            WHERE statut = 'Actif'
            ORDER BY pseudo
        """)
        classement = cursor.fetchall()
    finally:
        conn.close()
    return classement


def get_classement_records():
    """Récupère le classement des meilleurs scores en une semaine"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.id, u.pseudo, u.prenom,
                   COALESCE(MAX(week_scores.week_total), 0) as record_points
            FROM utilisateurs u
            LEFT JOIN (
                SELECT p.user_id, m.semaine_id, SUM(p.points_gagnes) as week_total
                FROM predictions p
                JOIN matches m ON p.match_id = m.id
                GROUP BY p.user_id, m.semaine_id
            ) week_scores ON u.id = week_scores.user_id
            WHERE u.statut = 'Actif'
            GROUP BY u.id, u.pseudo, u.prenom
            ORDER BY record_points DESC
        """)
        classement = cursor.fetchall()
    except Exception:
        cursor.execute("""
            SELECT id, pseudo, prenom, 0 as record_points
            FROM utilisateurs
            WHERE statut = 'Actif'
            ORDER BY pseudo
        """)
        classement = cursor.fetchall()
    finally:
        conn.close()
    return classement


def get_classement_assiduite():
    """Récupère le classement par nombre de pronostics validés"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.id, u.pseudo, u.prenom,
                   COUNT(p.id) as nb_pronos
            FROM utilisateurs u
            LEFT JOIN predictions p ON u.id = p.user_id
            WHERE u.statut = 'Actif'
            GROUP BY u.id, u.pseudo, u.prenom
            ORDER BY nb_pronos DESC
        """)
        classement = cursor.fetchall()
    except Exception:
        cursor.execute("""
            SELECT id, pseudo, prenom, 0 as nb_pronos
            FROM utilisateurs
            WHERE statut = 'Actif'
            ORDER BY pseudo
        """)
        classement = cursor.fetchall()
    finally:
        conn.close()
    return classement


def get_evolution(user_id):
    """Calcule l'évolution du rang (Simulation pour le moment)"""
    import random
    return random.choice(['up', 'down', 'stable'])


def afficher_podium(classement, stat_label="Points"):
    """Affiche le podium des 3 premiers"""
    if not classement:
        st.info("Aucun joueur dans le classement.")
        return

    st.markdown("""
    <style>
        .podium-place { text-align: center; padding: 15px; border-radius: 15px; min-width: 120px; }
        .podium-1 { background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #0a0a1a; }
        .podium-2 { background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%); color: #0a0a1a; }
        .podium-3 { background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%); color: white; }
        .podium-avatar { width: 60px; height: 60px; border-radius: 50%; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; font-size: 1.5em; font-weight: bold; background: rgba(255,255,255,0.3); }
        .podium-pseudo { font-weight: bold; font-size: 1em; margin-bottom: 5px; }
        .podium-score { font-size: 1.2em; font-weight: bold; }
        .podium-rank { font-size: 2em; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    medals = ["🥇", "🥈", "🥉"]
    styles = ["podium-1", "podium-2", "podium-3"]
    positions = [1, 0, 2]  # Ordre: 2ème, 1er, 3ème

    for col_idx, pos in enumerate(positions):
        if len(classement) > pos:
            user = classement[pos]
            pseudo = user[1] if user[1] else "N/A"
            score = user[3] if len(user) > 3 else 0
            initial = pseudo[0].upper() if pseudo else "?"

            with cols[col_idx]:
                st.markdown(f"""
                <div class="podium-place {styles[pos]}">
                    <div class="podium-rank">{medals[pos]}</div>
                    <div class="podium-avatar">{initial}</div>
                    <div class="podium-pseudo">{pseudo}</div>
                    <div class="podium-score">{score} {stat_label}</div>
                </div>
                """, unsafe_allow_html=True)


def afficher_tableau_classement(classement, current_user_id, stat_label="Points"):
    """Affiche le tableau complet du classement"""
    if not classement:
        return

    st.markdown("---")

    for idx, user in enumerate(classement):
        user_id = user[0]
        pseudo = user[1] if user[1] else "N/A"
        score = user[3] if len(user) > 3 else 0
        is_current = (user_id == current_user_id)

        row_style = "border: 2px solid #FFD700; box-shadow: 0 0 10px rgba(255,215,0,0.3);" if is_current else ""

        st.markdown(f"""
        <div style="display: flex; align-items: center; padding: 12px 15px; margin: 5px 0; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 10px; {row_style}">
            <div style="width: 50px; font-weight: bold; color: #FFD700; font-size: 1.1em;">#{idx+1}</div>
            <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #FFD700, #FFA500); display: flex; align-items: center; justify-content: center; color: #0a0a1a; font-weight: bold; margin-right: 15px;">{pseudo[0].upper()}</div>
            <div style="flex: 1; font-weight: bold; color: white;">{pseudo}</div>
            <div style="font-weight: bold; color: #FFD700; font-size: 1.1em;">{score} {stat_label}</div>
        </div>
        """, unsafe_allow_html=True)


def afficher_classement(user):
    """Affiche le module de classement complet"""

    # Style CSS Elite
    st.markdown("""
    <style>
        h1, h2, h3 { color: #FFD700 !important; }
    </style>
    """, unsafe_allow_html=True)

    # Header avec bouton retour
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Retour"):
            st.session_state.dashboard_section = None
            st.rerun()

    with col_title:
        st.markdown("## 🏆 Classement Elite")

    st.markdown("---")

    current_user_id = user['id']

    # Onglets
    tab1, tab2, tab3, tab4 = st.tabs(["🥇 Général", "📅 Ma Semaine", "🔥 Records", "📈 Assiduité"])

    with tab1:
        st.markdown("### Classement Général")
        st.caption("Cumul total des points de la saison")
        data = get_classement_general()
        afficher_podium(data, "pts")
        afficher_tableau_classement(data, current_user_id, "pts")

    with tab2:
        semaine_no = datetime.now().isocalendar()[1]
        st.markdown(f"### Classement Semaine {semaine_no}")
        st.caption("Points de la semaine en cours")
        data = get_classement_semaine()
        afficher_podium(data, "pts")
        afficher_tableau_classement(data, current_user_id, "pts")

    with tab3:
        st.markdown("### Hall of Fame")
        st.caption("Meilleurs scores en une seule semaine")
        data = get_classement_records()
        afficher_podium(data, "pts max")
        afficher_tableau_classement(data, current_user_id, "pts")

    with tab4:
        st.markdown("### Classement Assiduité")
        st.caption("Nombre de pronostics validés")
        data = get_classement_assiduite()
        afficher_podium(data, "pronos")
        afficher_tableau_classement(data, current_user_id, "pronos")

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 10px;">
        <small>Classements mis à jour en temps réel</small>
    </div>
    """, unsafe_allow_html=True)
