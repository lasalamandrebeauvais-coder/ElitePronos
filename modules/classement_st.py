"""
Module Classement Streamlit pour Elite Pronos
Classements avec 3 onglets : General, Ma Semaine, Records
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime

# Chemins
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')


def get_classement_general_complet():
    """
    Recupere le classement general avec toutes les stats:
    - Place, Pseudo, Points, Bons pronos, Scores exacts, Grand Chelem
    - Jokers restants (Doubles, Voles), Meilleure place
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Recuperer les stats de base pour chaque joueur
        cursor.execute("""
            SELECT
                u.id,
                u.pseudo,
                COALESCE(SUM(p.points_gagnes), 0) as total_points,
                COUNT(CASE WHEN p.points_gagnes > 0 THEN 1 END) as bons_pronos,
                COUNT(CASE WHEN p.is_score_exact = 1 THEN 1 END) as scores_exacts
            FROM utilisateurs u
            LEFT JOIN predictions p ON u.id = p.user_id
            WHERE u.statut = 'Actif'
            GROUP BY u.id, u.pseudo
            ORDER BY total_points DESC
        """)
        joueurs_base = cursor.fetchall()

        classement = []
        for idx, (user_id, pseudo, points, bons_pronos, scores_exacts) in enumerate(joueurs_base):
            # Compter les Grand Chelem (4/4 bons pronos sur une semaine)
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT m.semaine_id
                    FROM predictions p
                    JOIN matches m ON p.match_id = m.id
                    WHERE p.user_id = ? AND p.points_gagnes > 0
                    GROUP BY m.semaine_id
                    HAVING COUNT(*) >= 4
                )
            """, (user_id,))
            nb_grand_chelem = cursor.fetchone()[0]

            # Jokers restants - Points Doubles
            cursor.execute("""
                SELECT COALESCE(jokers_double, 2) FROM stock_jokers WHERE utilisateur_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            jokers_double = row[0] if row else 2

            # Jokers restants - Points Voles
            cursor.execute("""
                SELECT COALESCE(jokers_vol, 2) FROM stock_jokers WHERE utilisateur_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            jokers_vol = row[0] if row else 2

            # Meilleure place (simulation basee sur le rang actuel)
            meilleure_place = idx + 1  # Pour l'instant = rang actuel

            classement.append({
                'place': idx + 1,
                'user_id': user_id,
                'pseudo': pseudo,
                'points': points,
                'bons_pronos': bons_pronos,
                'scores_exacts': scores_exacts,
                'grand_chelem': nb_grand_chelem,
                'jokers_double': jokers_double,
                'jokers_vol': jokers_vol,
                'meilleure_place': meilleure_place
            })

        conn.close()
        return classement

    except Exception as e:
        conn.close()
        return []


def get_historique_joueur(user_id):
    """Recupere l'historique des pronostics par journee pour un joueur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Recuperer la saison active
        cursor.execute("SELECT id FROM saisons WHERE is_active = 1")
        saison_row = cursor.fetchone()
        saison_id = saison_row[0] if saison_row else 2025

        # Recuperer toutes les journees avec pronostics
        cursor.execute("""
            SELECT DISTINCT m.semaine_id
            FROM predictions p
            JOIN matches m ON p.match_id = m.id
            WHERE p.user_id = ? AND m.saison_id = ?
            ORDER BY m.semaine_id DESC
        """, (user_id, saison_id))
        journees = [row[0] for row in cursor.fetchall()]

        historique = []
        for journee in journees:
            # Recuperer les pronostics de cette journee
            cursor.execute("""
                SELECT m.equipe_home, m.equipe_away,
                       p.score_prono_home, p.score_prono_away,
                       p.mise_points, p.points_gagnes,
                       m.score_final_home, m.score_final_away,
                       p.is_score_exact
                FROM predictions p
                JOIN matches m ON p.match_id = m.id
                WHERE p.user_id = ? AND m.semaine_id = ? AND m.saison_id = ?
                ORDER BY m.date_match
            """, (user_id, journee, saison_id))
            pronos = cursor.fetchall()

            # Calculer le total de la journee
            total_journee = sum(p[5] or 0 for p in pronos)

            historique.append({
                'journee': journee,
                'pronos': pronos,
                'total': total_journee
            })

        conn.close()
        return historique

    except Exception as e:
        conn.close()
        return []


def get_records_joueur(user_id):
    """Recupere les records d'un joueur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Nombre de scores exacts
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE user_id = ? AND is_score_exact = 1
        """, (user_id,))
        nb_scores_exacts = cursor.fetchone()[0]

        # Nombre de bons pronostics (1N2 correct)
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE user_id = ? AND points_gagnes > 0
        """, (user_id,))
        nb_bons_pronos = cursor.fetchone()[0]

        # Meilleur score en une journee
        cursor.execute("""
            SELECT COALESCE(MAX(total), 0) FROM (
                SELECT SUM(p.points_gagnes) as total
                FROM predictions p
                JOIN matches m ON p.match_id = m.id
                WHERE p.user_id = ?
                GROUP BY m.semaine_id
            )
        """, (user_id,))
        meilleur_journee = cursor.fetchone()[0] or 0

        conn.close()
        return {
            'scores_exacts': nb_scores_exacts,
            'bons_pronos': nb_bons_pronos,
            'meilleur_journee': meilleur_journee
        }

    except Exception as e:
        conn.close()
        return {'scores_exacts': 0, 'bons_pronos': 0, 'meilleur_journee': 0}


def afficher_classement(user):
    """Affiche le module de classement complet"""

    # Style CSS Elite
    st.markdown("""
    <style>
        h1, h2, h3 { color: #FFD700 !important; }
        .stButton > button { color: #FFD700 !important; border-color: #FFD700 !important; }
    </style>
    """, unsafe_allow_html=True)

    # Header avec bouton retour JAUNE et mascotte
    col_back, col_title, col_mascot = st.columns([0.6, 4.5, 0.8])
    with col_back:
        st.markdown("""
        <style>
            div[data-testid="column"]:first-child button {
                color: #FFD700 !important;
                border-color: #FFD700 !important;
                background-color: transparent !important;
            }
        </style>
        """, unsafe_allow_html=True)
        if st.button("◀", help="Retour", use_container_width=True, key="btn_retour_classement"):
            st.session_state.dashboard_section = None
            st.rerun()
    with col_title:
        st.markdown("## 🏆 Classement Elite")
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo classements.png")
        if os.path.exists(mascot_path):
            from PIL import Image
            mascot_img = Image.open(mascot_path)
            st.image(mascot_img, width=70)

    st.markdown("---")

    current_user_id = user['id']

    # Onglets (3 onglets - sans Assiduite)
    tab1, tab2, tab3 = st.tabs(["🥇 General", "📅 Ma Semaine", "🔥 Records"])

    # === ONGLET GENERAL ===
    with tab1:
        st.markdown("### Classement General")
        st.caption("Cumul total des points de la saison")

        classement = get_classement_general_complet()

        if classement:
            # Header du tableau compact
            st.markdown("""
            <div style="
                display: grid;
                grid-template-columns: 0.4fr 1.2fr 0.6fr 0.5fr 0.5fr 0.4fr 0.4fr 0.4fr 0.5fr;
                gap: 3px;
                padding: 8px 5px;
                background: #D4AF37;
                border-radius: 8px 8px 0 0;
                font-size: 0.65em;
                font-weight: bold;
                color: #001529;
                text-align: center;
            ">
                <span>#</span>
                <span style="text-align: left;">Pseudo</span>
                <span>Points</span>
                <span>Pronos</span>
                <span>Scores</span>
                <span>GC</span>
                <span>J.D</span>
                <span>J.V</span>
                <span>Best</span>
            </div>
            """, unsafe_allow_html=True)

            # Lignes du tableau
            for joueur in classement:
                is_current = (joueur['user_id'] == current_user_id)
                bg_color = "#002855" if is_current else "#001529"
                border = "border: 1px solid #FFD700;" if is_current else ""

                # Couleur de la place
                if joueur['place'] == 1:
                    place_color = "#FFD700"
                elif joueur['place'] == 2:
                    place_color = "#C0C0C0"
                elif joueur['place'] == 3:
                    place_color = "#CD7F32"
                else:
                    place_color = "#FFFFFF"

                st.markdown(f"""
                <div style="
                    display: grid;
                    grid-template-columns: 0.4fr 1.2fr 0.6fr 0.5fr 0.5fr 0.4fr 0.4fr 0.4fr 0.5fr;
                    gap: 3px;
                    padding: 6px 5px;
                    background: {bg_color};
                    {border}
                    font-size: 0.7em;
                    align-items: center;
                    border-bottom: 1px solid #333;
                ">
                    <span style="color: {place_color}; font-weight: bold; text-align: center;">{joueur['place']}</span>
                    <span style="color: #FFFFFF; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{joueur['pseudo']}</span>
                    <span style="color: #00FF00; font-weight: bold; text-align: center;">{joueur['points']}</span>
                    <span style="color: #4488FF; text-align: center;">{joueur['bons_pronos']}</span>
                    <span style="color: #FFD700; text-align: center;">{joueur['scores_exacts']}</span>
                    <span style="color: #FF00FF; text-align: center;">{joueur['grand_chelem']}</span>
                    <span style="color: #00FFFF; text-align: center;">{joueur['jokers_double']}</span>
                    <span style="color: #FF6600; text-align: center;">{joueur['jokers_vol']}</span>
                    <span style="color: #AAAAAA; text-align: center;">{joueur['meilleure_place']}</span>
                </div>
                """, unsafe_allow_html=True)

            # Legende
            st.markdown("""
            <div style="margin-top: 10px; font-size: 0.6em; color: #888; text-align: center;">
                GC = Grand Chelem | J.D = Jokers Doubles | J.V = Jokers Vol | Best = Meilleure place
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Aucun joueur dans le classement.")

    # === ONGLET MA SEMAINE ===
    with tab2:
        st.markdown("### Mon Historique")
        st.caption("Historique de mes pronostics par journee")

        historique = get_historique_joueur(current_user_id)

        if historique:
            for h in historique:
                # Total de la journee
                total_color = "#00FF00" if h['total'] >= 0 else "#FF4444"

                with st.expander(f"📅 Journee {h['journee']} - {'+' if h['total'] > 0 else ''}{h['total']} pts", expanded=(h == historique[0])):
                    # Header
                    st.markdown("""
                    <div style="display: grid; grid-template-columns: 2fr 1fr 0.8fr 1fr 0.8fr; gap: 5px; padding: 5px; font-size: 0.7em; color: #888; background: #002040; border-radius: 5px;">
                        <span>Match</span>
                        <span style="text-align: center;">Prono</span>
                        <span style="text-align: center;">Mise</span>
                        <span style="text-align: center;">Score</span>
                        <span style="text-align: center;">Pts</span>
                    </div>
                    """, unsafe_allow_html=True)

                    for prono in h['pronos']:
                        home, away, ph, pa, mise, pts, score_h, score_a, is_exact = prono

                        # Icone resultat
                        if score_h is not None:
                            if is_exact:
                                icon = "🎯"
                            elif pts and pts > 0:
                                icon = "✅"
                            else:
                                icon = "❌"
                            score_display = f"{score_h}-{score_a}"
                        else:
                            icon = "⏳"
                            score_display = "-"

                        pts_val = pts if pts else 0
                        pts_color = "#00FF00" if pts_val > 0 else "#FF4444" if pts_val < 0 else "#888"

                        home_short = home[:10] + ".." if len(home) > 12 else home
                        away_short = away[:10] + ".." if len(away) > 12 else away

                        st.markdown(f"""
                        <div style="display: grid; grid-template-columns: 2fr 1fr 0.8fr 1fr 0.8fr; gap: 5px; padding: 5px; font-size: 0.75em; border-bottom: 1px solid #333;">
                            <span style="color: #FFFFFF;" title="{home} vs {away}">{home_short} - {away_short}</span>
                            <span style="color: #4488FF; text-align: center;">{ph}-{pa}</span>
                            <span style="color: #FFD700; text-align: center;">{mise}</span>
                            <span style="color: #00FF00; text-align: center;">{score_display} {icon}</span>
                            <span style="color: {pts_color}; text-align: center; font-weight: bold;">{'+' if pts_val > 0 else ''}{pts_val}</span>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Aucun historique disponible.")

    # === ONGLET RECORDS ===
    with tab3:
        st.markdown("### Mes Records")
        st.caption("Mes performances personnelles")

        records = get_records_joueur(current_user_id)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1a472a 0%, #2d5a3c 100%);
                border: 2px solid #00FF00;
                border-radius: 15px;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-size: 2.5em; color: #00FF00; font-weight: bold;">🎯</div>
                <div style="font-size: 2em; color: #FFFFFF; font-weight: bold;">{records['scores_exacts']}</div>
                <div style="color: #00FF00; font-size: 0.9em;">Scores Exacts</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1a3a5c 0%, #2d4a6c 100%);
                border: 2px solid #4488FF;
                border-radius: 15px;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-size: 2.5em; color: #4488FF; font-weight: bold;">✅</div>
                <div style="font-size: 2em; color: #FFFFFF; font-weight: bold;">{records['bons_pronos']}</div>
                <div style="color: #4488FF; font-size: 0.9em;">Bons Pronostics</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #5c3a1a 0%, #6c4a2d 100%);
                border: 2px solid #FFD700;
                border-radius: 15px;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">🏆</div>
                <div style="font-size: 2em; color: #FFFFFF; font-weight: bold;">{records['meilleur_journee']}</div>
                <div style="color: #FFD700; font-size: 0.9em;">Record Journee</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #AAAAAA; padding: 10px;">
        <small>Classements mis a jour en temps reel</small>
    </div>
    """, unsafe_allow_html=True)
