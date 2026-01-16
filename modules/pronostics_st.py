"""
Module Pronostics Streamlit pour Elite Pronos
Saisie des pronostics de la semaine
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime

# Chemins
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Budget hebdomadaire
BUDGET_TOTAL = 100
MISE_MIN = 10
MISE_MAX = 60


def get_matchs_semaine():
    """
    Recupere les 4 matchs de la semaine en cours
    Priorite: Ligue 1 (FL1) d'abord, puis autres championnats
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Verifier si la table matches existe et a des donnees
        cursor.execute("SELECT COUNT(*) FROM matches")
        count = cursor.fetchone()[0]

        if count == 0:
            conn.close()
            return []

        # Recuperer la semaine active (matchs sans score final)
        cursor.execute("""
            SELECT DISTINCT semaine_id FROM matches
            WHERE is_active = 1 AND score_final_home IS NULL
            ORDER BY semaine_id DESC LIMIT 1
        """)
        result = cursor.fetchone()

        if result:
            semaine_id = result[0]
            # Recuperer les matchs de cette semaine
            cursor.execute("""
                SELECT id, championnat, equipe_home, equipe_away,
                       cote_home, cote_draw, cote_away, date_match
                FROM matches
                WHERE semaine_id = ?
                ORDER BY
                    CASE WHEN championnat = 'FL1' THEN 0 ELSE 1 END,
                    id
                LIMIT 4
            """, (semaine_id,))
        else:
            # Fallback: tous les matchs actifs
            cursor.execute("""
                SELECT id, championnat, equipe_home, equipe_away,
                       cote_home, cote_draw, cote_away, date_match
                FROM matches
                WHERE is_active = 1
                ORDER BY
                    CASE WHEN championnat = 'FL1' THEN 0 ELSE 1 END,
                    id
                LIMIT 4
            """)

        matchs = cursor.fetchall()
        conn.close()
        return matchs

    except Exception as e:
        conn.close()
        return []


def get_pronos_existants(user_id):
    """Recupere les pronostics deja saisis par l'utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT match_id, score_prono_home, score_prono_away, mise_points
        FROM predictions
        WHERE user_id = ? AND match_id IN (SELECT id FROM matches)
    """, (user_id,))

    pronos = {p[0]: {'home': p[1], 'away': p[2], 'mise': p[3]} for p in cursor.fetchall()}
    conn.close()

    return pronos


def get_joker_semaine():
    """Recupere le joker utilise cette semaine"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT type FROM joker_semaine LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def sauvegarder_pronostics(user_id, pronos_data, joker_type):
    """
    Sauvegarde les pronostics dans la base de donnees
    pronos_data: dict {match_id: {'choix': '1/N/2', 'mise': int, 'home': int, 'away': int}}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Supprimer les anciens pronostics de cet utilisateur pour ces matchs
        match_ids = list(pronos_data.keys())
        if match_ids:
            placeholders = ','.join(['?' for _ in match_ids])
            cursor.execute(f"""
                DELETE FROM predictions
                WHERE user_id = ? AND match_id IN ({placeholders})
            """, [user_id] + match_ids)

        # Inserer les nouveaux pronostics
        for match_id, data in pronos_data.items():
            cursor.execute("""
                INSERT INTO predictions (user_id, match_id, score_prono_home, score_prono_away, mise_points, points_gagnes)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (user_id, match_id, data['home'], data['away'], data['mise']))

        # Sauvegarder le joker via le nouveau systeme
        if joker_type and joker_type != "AUCUN":
            # Recuperer la semaine_id du premier match
            cursor.execute("SELECT semaine_id FROM matches WHERE id = ?", (match_ids[0],))
            result = cursor.fetchone()
            semaine_id = result[0] if result else None

            if semaine_id:
                # Utiliser le systeme de jokers du database_manager
                from modules.database_manager import utiliser_joker_double, utiliser_joker_vol
                if joker_type == "DOUBLE":
                    utiliser_joker_double(user_id, semaine_id)
                # VOL necessite une cible - a gerer separement

        conn.commit()
        conn.close()
        return True, "Pronostics enregistres avec succes!"

    except Exception as e:
        conn.close()
        return False, f"Erreur: {str(e)}"


def get_championnat_nom(code):
    """Retourne le nom complet du championnat"""
    championnats = {
        'FL1': 'Ligue 1',
        'PL': 'Premier League',
        'PD': 'La Liga',
        'SA': 'Serie A',
        'BL1': 'Bundesliga'
    }
    return championnats.get(code, code)


def afficher_pronostics(user):
    """Affiche l'interface de saisie des pronostics"""

    # Style CSS Elite pour les cartes
    st.markdown("""
    <style>
        .match-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #FFD700;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
        }

        .match-header {
            text-align: center;
            color: #FFD700;
            font-size: 0.8em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .team-name {
            font-size: 1.1em;
            font-weight: bold;
            color: white;
        }

        .cote-box {
            background: #0a0a1a;
            border: 1px solid #FFD700;
            border-radius: 8px;
            padding: 8px 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .cote-box:hover {
            background: #FFD700;
            color: #0a0a1a;
        }

        .cote-selected {
            background: #FFD700 !important;
            color: #0a0a1a !important;
        }

        .budget-bar {
            background: #1a1a2e;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
        }

        .budget-fill {
            background: linear-gradient(90deg, #FFD700, #FFA500);
            height: 100%;
            transition: width 0.3s ease;
        }

        .joker-card {
            background: linear-gradient(135deg, #2d1f3d 0%, #1a1a2e 100%);
            border: 2px solid #9b59b6;
            border-radius: 15px;
            padding: 15px;
            text-align: center;
        }

        .success-message {
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: #0a0a1a;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Retour"):
            st.session_state.dashboard_section = None
            st.rerun()

    with col_title:
        st.markdown("## ⚽ Mes Pronostics")

    st.markdown("---")

    # Recuperer les matchs
    matchs = get_matchs_semaine()

    if not matchs:
        st.warning("Aucun match disponible cette semaine. L'admin doit charger les matchs.")
        return

    # Initialiser les variables de session pour les pronos
    if 'pronos' not in st.session_state:
        # Charger les pronostics existants de l'utilisateur
        pronos_existants = get_pronos_existants(user['id'])
        st.session_state.pronos = pronos_existants if pronos_existants else {}

    if 'joker_selected' not in st.session_state:
        st.session_state.joker_selected = "AUCUN"

    # === AFFICHAGE DES MATCHS ===
    st.markdown("### 📋 Matchs de la Semaine")

    total_mise = 0
    pronos_valides = True

    for match in matchs:
        match_id, championnat, home, away, cote_h, cote_n, cote_a, date_match = match

        # Initialiser le prono pour ce match si pas encore fait
        if match_id not in st.session_state.pronos:
            st.session_state.pronos[match_id] = {
                'home': 0,
                'away': 0,
                'mise': 25,
                'choix': None
            }

        with st.container():
            # En-tete du match
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 2px solid #FFD700;
                border-radius: 15px 15px 0 0;
                padding: 10px;
                text-align: center;
            ">
                <span style="color: #FFD700; font-size: 0.9em;">
                    🏆 {get_championnat_nom(championnat)}
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Corps du match
            col1, col2, col3 = st.columns([2, 1, 2])

            with col1:
                st.markdown(f"### 🏠 {home}")
                score_home = st.number_input(
                    "Buts",
                    min_value=0,
                    max_value=9,
                    value=st.session_state.pronos[match_id]['home'],
                    key=f"home_{match_id}"
                )
                st.session_state.pronos[match_id]['home'] = score_home

            with col2:
                st.markdown("<div style='text-align: center; padding-top: 30px;'>", unsafe_allow_html=True)
                st.markdown("### VS")
                st.markdown("</div>", unsafe_allow_html=True)

            with col3:
                st.markdown(f"### 🏃 {away}")
                score_away = st.number_input(
                    "Buts",
                    min_value=0,
                    max_value=9,
                    value=st.session_state.pronos[match_id]['away'],
                    key=f"away_{match_id}"
                )
                st.session_state.pronos[match_id]['away'] = score_away

            # Cotes
            st.markdown("**Cotes :**")
            cote_col1, cote_col2, cote_col3 = st.columns(3)

            with cote_col1:
                st.metric("1 (Dom)", f"{cote_h:.2f}")
            with cote_col2:
                st.metric("N (Nul)", f"{cote_n:.2f}")
            with cote_col3:
                st.metric("2 (Ext)", f"{cote_a:.2f}")

            # Mise
            st.markdown("**💰 Mise (10-60 pts) :**")
            mise = st.slider(
                "Mise",
                min_value=MISE_MIN,
                max_value=MISE_MAX,
                value=st.session_state.pronos[match_id]['mise'],
                step=5,
                key=f"mise_{match_id}",
                label_visibility="collapsed"
            )
            st.session_state.pronos[match_id]['mise'] = mise
            total_mise += mise

            st.markdown("---")

    # === BARRE DE BUDGET ===
    st.markdown("### 💰 Budget")

    budget_pct = min((total_mise / BUDGET_TOTAL) * 100, 100)
    budget_color = "#00FF00" if total_mise == BUDGET_TOTAL else ("#FFD700" if total_mise < BUDGET_TOTAL else "#FF0000")

    st.markdown(f"""
    <div style="
        background: #1a1a2e;
        border-radius: 10px;
        padding: 3px;
        margin: 10px 0;
    ">
        <div style="
            background: {budget_color};
            width: {budget_pct}%;
            height: 25px;
            border-radius: 8px;
            transition: all 0.3s ease;
        "></div>
    </div>
    <div style="text-align: center; color: {'#00FF00' if total_mise == BUDGET_TOTAL else '#FFD700'};">
        <strong>{total_mise} / {BUDGET_TOTAL} points utilises</strong>
    </div>
    """, unsafe_allow_html=True)

    if total_mise != BUDGET_TOTAL:
        if total_mise < BUDGET_TOTAL:
            st.warning(f"Il vous reste {BUDGET_TOTAL - total_mise} points a repartir.")
        else:
            st.error(f"Vous depassez le budget de {total_mise - BUDGET_TOTAL} points!")
        pronos_valides = False

    st.markdown("")

    # === JOKERS ===
    st.markdown("### 🃏 Joker de la Semaine")
    st.caption("Un seul joker peut etre active par semaine")

    joker_col1, joker_col2, joker_col3 = st.columns(3)

    with joker_col1:
        if st.button("❌ AUCUN", use_container_width=True,
                     type="primary" if st.session_state.joker_selected == "AUCUN" else "secondary"):
            st.session_state.joker_selected = "AUCUN"
            st.rerun()

    with joker_col2:
        if st.button("⚡ POINTS DOUBLES", use_container_width=True,
                     type="primary" if st.session_state.joker_selected == "DOUBLE" else "secondary"):
            st.session_state.joker_selected = "DOUBLE"
            st.rerun()

    with joker_col3:
        if st.button("🎯 POINTS VOLES", use_container_width=True,
                     type="primary" if st.session_state.joker_selected == "VOLE" else "secondary"):
            st.session_state.joker_selected = "VOLE"
            st.rerun()

    if st.session_state.joker_selected != "AUCUN":
        st.info(f"Joker selectionne : **{st.session_state.joker_selected}**")

    st.markdown("---")

    # === VALIDATION ===
    st.markdown("### ✅ Validation")

    if st.button("VALIDER MES PRONOSTICS", type="primary", use_container_width=True, disabled=not pronos_valides):
        if pronos_valides:
            # Preparer les donnees
            pronos_data = {}
            for match_id, data in st.session_state.pronos.items():
                pronos_data[match_id] = {
                    'home': data['home'],
                    'away': data['away'],
                    'mise': data['mise']
                }

            # Sauvegarder
            success, message = sauvegarder_pronostics(
                user['id'],
                pronos_data,
                st.session_state.joker_selected
            )

            if success:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                    color: #0a0a1a;
                    padding: 20px;
                    border-radius: 15px;
                    text-align: center;
                    font-weight: bold;
                    margin: 20px 0;
                ">
                    ✅ {message}
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

                # Reset pour prochaine saisie
                st.session_state.pronos = {}
                st.session_state.joker_selected = "AUCUN"
            else:
                st.error(message)

    # Recap des pronos
    if st.session_state.pronos:
        st.markdown("### 📝 Recapitulatif")
        for match in matchs:
            match_id = match[0]
            home = match[2]
            away = match[3]
            if match_id in st.session_state.pronos:
                p = st.session_state.pronos[match_id]
                st.write(f"**{home}** {p['home']} - {p['away']} **{away}** | Mise: {p['mise']} pts")
