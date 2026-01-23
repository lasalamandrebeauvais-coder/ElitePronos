"""
Module Pronostics Streamlit pour Elite Pronos
Saisie des pronostics de la semaine
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta

# Chemins
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

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


def get_deadline_pronostics():
    """
    Retourne la date limite pour soumettre les pronostics
    = date du premier match de la semaine - 1 heure
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Recuperer la date du premier match actif de la semaine
        cursor.execute("""
            SELECT MIN(date_match) FROM matches
            WHERE is_active = 1 AND score_final_home IS NULL
            AND date_match IS NOT NULL
        """)
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            # Parser la date
            try:
                first_match = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    first_match = datetime.strptime(result[0], "%Y-%m-%d")
                except:
                    return None
            # Deadline = 1h avant le premier match
            return first_match - timedelta(hours=1)
        return None
    except:
        conn.close()
        return None


def get_countdown_pronostics():
    """
    Retourne le temps restant avant la deadline
    Format: {'days': X, 'hours': X, 'minutes': X, 'seconds': X, 'expired': bool}
    """
    deadline = get_deadline_pronostics()
    if not deadline:
        return None

    now = datetime.now()
    diff = deadline - now

    if diff.total_seconds() <= 0:
        return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0, 'expired': True}

    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'expired': False
    }


def afficher_pronostics(user):
    """Affiche l'interface de saisie des pronostics - Version COMPACTE"""

    # Verifier si des pronos existent deja
    pronos_existants = get_pronos_existants(user['id'])
    mode_edition = st.session_state.get('mode_edition_pronos', False)

    # Header compact avec mascotte
    col_back, col_mascot, col_title, col_countdown = st.columns([0.8, 0.8, 2.5, 2])
    with col_back:
        if st.button("← Retour"):
            st.session_state.dashboard_section = None
            st.session_state.mode_edition_pronos = False
            st.rerun()
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo pronostics.png")
        if os.path.exists(mascot_path):
            from PIL import Image
            mascot_img = Image.open(mascot_path)
            st.image(mascot_img, width=60)
    with col_title:
        st.markdown("### ⚽ Pronostics")

    # Countdown compact
    countdown = get_countdown_pronostics()
    with col_countdown:
        if countdown and not countdown.get('expired'):
            st.markdown(f"""
            <div style="text-align: right; color: #FFD700; font-size: 0.9em;">
                ⏱️ <b>{countdown['days']}j {countdown['hours']}h {countdown['minutes']}m</b>
            </div>
            """, unsafe_allow_html=True)
        elif countdown and countdown.get('expired'):
            st.markdown("<div style='text-align: right; color: #FF4444;'>⏰ CLOS</div>", unsafe_allow_html=True)

    # Recuperer les matchs
    matchs = get_matchs_semaine()
    if not matchs:
        st.warning("Aucun match disponible.")
        return

    # === SI PRONOS DEJA VALIDES ET PAS EN MODE EDITION ===
    if pronos_existants and not mode_edition:
        st.markdown("### ✅ Vos pronostics validés")

        for match in matchs:
            match_id, championnat, home, away, cote_h, cote_n, cote_a, date_match = match
            if match_id in pronos_existants:
                p = pronos_existants[match_id]
                st.markdown(f"""
                <div style="
                    background: #0A183D;
                    border: 1px solid #00FF00;
                    border-radius: 8px;
                    padding: 10px;
                    margin: 5px 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <span style="color: #FFFFFF;">{home}</span>
                    <span style="color: #4488FF; font-weight: bold; font-size: 1.2em;">{p['home']} - {p['away']}</span>
                    <span style="color: #FFFFFF;">{away}</span>
                    <span style="color: #00FF00; font-weight: bold;">{p['mise']} pts</span>
                </div>
                """, unsafe_allow_html=True)

        # Bouton Modifier
        st.markdown("")
        if st.button("✏️ MODIFIER MES PRONOSTICS", type="secondary", use_container_width=True):
            st.session_state.mode_edition_pronos = True
            st.session_state.pronos = pronos_existants.copy()
            st.rerun()
        return

    # === MODE SAISIE / EDITION ===
    if 'pronos' not in st.session_state or not st.session_state.pronos:
        st.session_state.pronos = pronos_existants if pronos_existants else {}
    if 'joker_selected' not in st.session_state:
        st.session_state.joker_selected = "AUCUN"

    total_mise = 0
    pronos_valides = True

    # === AFFICHAGE COMPACT: 2 MATCHS PAR LIGNE ===
    for i in range(0, len(matchs), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            if i + j < len(matchs):
                match = matchs[i + j]
                match_id, championnat, home, away, cote_h, cote_n, cote_a, date_match = match

                # Init prono
                if match_id not in st.session_state.pronos:
                    st.session_state.pronos[match_id] = {'home': 0, 'away': 0, 'mise': 25}

                with col:
                    # Carte match - Equipes + COTES EN ROUGE
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #0A183D 0%, #001529 100%);
                        border: 1px solid #D4AF37;
                        border-radius: 10px;
                        padding: 10px;
                        margin-bottom: 5px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1; text-align: center;">
                                <div style="color: #FFFFFF; font-weight: bold; font-size: 0.9em;">{home}</div>
                                <div style="color: #FF0000; font-size: 0.9em; font-weight: bold;">{cote_h:.2f}</div>
                            </div>
                            <div style="color: #D4AF37; font-weight: bold; padding: 0 5px;">VS</div>
                            <div style="flex: 1; text-align: center;">
                                <div style="color: #FFFFFF; font-weight: bold; font-size: 0.9em;">{away}</div>
                                <div style="color: #FF0000; font-size: 0.9em; font-weight: bold;">{cote_a:.2f}</div>
                            </div>
                        </div>
                        <div style="text-align: center; color: #FF0000; font-size: 0.8em; margin-top: 3px;">
                            N: {cote_n:.2f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Scores en BLEU
                    sc1, sc2, sc3 = st.columns([1, 0.5, 1])
                    with sc1:
                        score_home = st.number_input(
                            f"H{match_id}", min_value=0, max_value=9,
                            value=st.session_state.pronos[match_id]['home'],
                            key=f"h_{match_id}", label_visibility="collapsed"
                        )
                        st.session_state.pronos[match_id]['home'] = score_home
                    with sc2:
                        st.markdown("<div style='text-align:center; padding-top:5px; color:#0066FF; font-size:1.5em; font-weight:bold;'>-</div>", unsafe_allow_html=True)
                    with sc3:
                        score_away = st.number_input(
                            f"A{match_id}", min_value=0, max_value=9,
                            value=st.session_state.pronos[match_id]['away'],
                            key=f"a_{match_id}", label_visibility="collapsed"
                        )
                        st.session_state.pronos[match_id]['away'] = score_away

                    # Points en VERT (en dessous)
                    mise = st.number_input(
                        f"M{match_id}", min_value=MISE_MIN, max_value=MISE_MAX,
                        value=st.session_state.pronos[match_id]['mise'],
                        step=5, key=f"m_{match_id}", label_visibility="collapsed"
                    )
                    st.session_state.pronos[match_id]['mise'] = mise
                    st.markdown(f"<div style='text-align:center; color:#00FF00; font-size: 1em; font-weight: bold;'>{mise} pts</div>", unsafe_allow_html=True)

                    total_mise += st.session_state.pronos[match_id]['mise']

    # === BUDGET ===
    st.markdown("---")
    budget_ok = total_mise == BUDGET_TOTAL
    budget_color = "#00FF00" if budget_ok else ("#FFD700" if total_mise < BUDGET_TOTAL else "#FF4444")

    st.markdown(f"""
    <div style="background: #1a1a2e; border-radius: 8px; padding: 2px; margin: 5px 0;">
        <div style="background: {budget_color}; width: {min(total_mise/BUDGET_TOTAL*100, 100)}%; height: 18px; border-radius: 6px;"></div>
    </div>
    <div style="text-align: center; color: {budget_color}; font-size: 0.9em;">
        <b>{total_mise} / {BUDGET_TOTAL} pts</b> {' ✓' if budget_ok else ''}
    </div>
    """, unsafe_allow_html=True)

    if not budget_ok:
        pronos_valides = False

    # === JOKERS (sans Aucun) ===
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:#AAAAAA; font-size:0.8em;'>Joker (optionnel)</div>", unsafe_allow_html=True)
    jk1, jk2 = st.columns(2)
    with jk1:
        if st.button("⚡ Points Doublés", use_container_width=True,
                     type="primary" if st.session_state.joker_selected == "DOUBLE" else "secondary"):
            st.session_state.joker_selected = "DOUBLE" if st.session_state.joker_selected != "DOUBLE" else "AUCUN"
            st.rerun()
    with jk2:
        if st.button("🎯 Points Volés", use_container_width=True,
                     type="primary" if st.session_state.joker_selected == "VOLE" else "secondary"):
            st.session_state.joker_selected = "VOLE" if st.session_state.joker_selected != "VOLE" else "AUCUN"
            st.rerun()

    # === VALIDATION ===
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    if st.button("✅ VALIDER", type="primary", use_container_width=True, disabled=not pronos_valides):
        if pronos_valides:
            pronos_data = {mid: {'home': d['home'], 'away': d['away'], 'mise': d['mise']}
                          for mid, d in st.session_state.pronos.items()}
            success, message = sauvegarder_pronostics(user['id'], pronos_data, st.session_state.joker_selected)
            if success:
                st.success(message)
                st.balloons()
                st.session_state.pronos = {}
                st.session_state.joker_selected = "AUCUN"
                st.session_state.mode_edition_pronos = False
            else:
                st.error(message)
