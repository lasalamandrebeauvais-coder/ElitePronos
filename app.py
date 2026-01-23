import streamlit as st
import sys
import os
import sqlite3

# Ajouter le chemin du projet pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration de la page
st.set_page_config(
    page_title="Elite Pronos",
    page_icon="⚽",
    layout="wide"
)

# Import des modules
from modules import DB_PATH, create_database
from modules.inscription_st import afficher_formulaire_inscription
from modules.admin_panel_st import afficher_panel_admin
from modules.login_st import (
    afficher_formulaire_login,
    afficher_header_utilisateur,
    is_logged_in,
    get_current_user,
    logout,
    init_session
)
from modules.dashboard_st import afficher_dashboard
from modules.database_manager import init_database
from modules.reglement_st import afficher_reglement

# Initialiser la base de donnees (cree les tables si elles n'existent pas)
create_database()
init_database()

# Activation temporaire du compte admin "baggio"
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE utilisateurs SET statut = 'Actif' WHERE pseudo = 'baggio'")
    conn.commit()
    conn.close()
except:
    pass

# Initialiser la session
init_session()

# Style CSS Elite - Bleu Nuit avec etoiles dorees
# Utilisation de background-image sur le body principal pour compatibilite Streamlit
st.markdown("""
<style>
    /* ===== FOND BLEU NUIT AVEC ETOILES DOREES ===== */
    .stApp {
        background:
            radial-gradient(2px 2px at 20px 30px, #D4AF37, transparent),
            radial-gradient(2px 2px at 40px 70px, #D4AF37, transparent),
            radial-gradient(1px 1px at 90px 40px, #FFD700, transparent),
            radial-gradient(2px 2px at 130px 80px, #D4AF37, transparent),
            radial-gradient(1px 1px at 160px 120px, #FFD700, transparent),
            radial-gradient(2px 2px at 200px 50px, #D4AF37, transparent),
            radial-gradient(1px 1px at 250px 160px, #FFD700, transparent),
            radial-gradient(2px 2px at 300px 100px, #D4AF37, transparent),
            radial-gradient(1px 1px at 350px 60px, #FFD700, transparent),
            radial-gradient(2px 2px at 400px 140px, #D4AF37, transparent),
            radial-gradient(1px 1px at 50px 180px, #FFD700, transparent),
            radial-gradient(2px 2px at 150px 220px, #D4AF37, transparent),
            radial-gradient(1px 1px at 280px 180px, #FFD700, transparent),
            radial-gradient(2px 2px at 380px 250px, #D4AF37, transparent),
            linear-gradient(135deg, #001529 0%, #002040 50%, #001529 100%) !important;
        background-size: 400px 300px, 400px 300px, 400px 300px, 400px 300px,
                         400px 300px, 400px 300px, 400px 300px, 400px 300px,
                         400px 300px, 400px 300px, 400px 300px, 400px 300px,
                         400px 300px, 400px 300px, 100% 100% !important;
        background-attachment: fixed !important;
    }

    /* ===== TITRES EN OR ===== */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
    [data-testid="stHeader"] {
        color: #D4AF37 !important;
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.3) !important;
    }

    /* ===== TOUS LES TEXTES EN BLANC PUR ===== */
    p, span, label, div, li, td, th,
    .stMarkdown, .stMarkdown p, .stMarkdown span,
    .stText, .stText p,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    .element-container, .element-container p, .element-container span {
        color: #FFFFFF !important;
    }

    /* ===== CAPTIONS EN OR (pas gris) ===== */
    .stCaption, [data-testid="stCaptionContainer"],
    .stCaption p, small, .caption,
    [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] span {
        color: #D4AF37 !important;
        opacity: 1 !important;
    }

    /* ===== METRICS - Labels en Or, Valeurs en Or ===== */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #001529 0%, #002040 100%) !important;
        border: 2px solid #D4AF37 !important;
        border-radius: 15px !important;
        padding: 15px !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFD700 !important;
        font-weight: bold !important;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] div {
        color: #D4AF37 !important;
    }

    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] span {
        color: #FFFFFF !important;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #001529 0%, #002040 100%) !important;
        border-right: 2px solid #D4AF37 !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #FFFFFF !important;
    }

    /* ===== BOUTONS ELITE ===== */
    .stButton > button {
        background: linear-gradient(135deg, #D4AF37 0%, #FFD700 100%) !important;
        color: #001529 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 30px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(212, 175, 55, 0.6) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ===== INPUTS ===== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea {
        background-color: #002040 !important;
        color: #FFFFFF !important;
        border: 2px solid #D4AF37 !important;
        border-radius: 10px !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea textarea::placeholder {
        color: #AAAAAA !important;
    }

    /* ===== SELECTBOX ===== */
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] {
        background-color: #002040 !important;
        border: 2px solid #D4AF37 !important;
        border-radius: 10px !important;
    }

    .stSelectbox [data-baseweb="select"] span {
        color: #FFFFFF !important;
    }

    /* ===== SELECTBOX DROPDOWN (POPOVER & LISTBOX) ===== */
    /* Fond du menu deroulant */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="menu"],
    [data-baseweb="menu"] > div {
        background-color: #001529 !important;
        border: 2px solid #D4AF37 !important;
        border-radius: 10px !important;
    }

    /* Liste des options */
    ul[role="listbox"],
    [data-baseweb="menu"] ul {
        background-color: #001529 !important;
        padding: 5px !important;
    }

    /* Options du menu */
    li[role="option"],
    [data-baseweb="menu"] li,
    ul[role="listbox"] li {
        color: #FFFFFF !important;
        background-color: #001529 !important;
        padding: 10px 15px !important;
        border-radius: 5px !important;
        margin: 2px 0 !important;
    }

    /* Survol des options - Fond Dore, Texte Bleu Nuit */
    li[role="option"]:hover,
    [data-baseweb="menu"] li:hover,
    ul[role="listbox"] li:hover,
    li[role="option"][aria-selected="true"],
    [data-baseweb="menu"] li[aria-selected="true"] {
        background-color: #D4AF37 !important;
        color: #001529 !important;
        font-weight: bold !important;
    }

    /* Option selectionnee/focus */
    li[role="option"]:focus,
    li[role="option"][data-highlighted="true"],
    [data-baseweb="menu"] li:focus {
        background-color: #D4AF37 !important;
        color: #001529 !important;
        outline: none !important;
    }

    /* Icone fleche du selectbox */
    .stSelectbox svg {
        fill: #D4AF37 !important;
    }

    /* ===== SLIDER ===== */
    .stSlider > div > div > div {
        background-color: #D4AF37 !important;
    }

    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"] {
        color: #FFFFFF !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #001529 !important;
        border-bottom: 2px solid #D4AF37 !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #FFFFFF !important;
    }

    .stTabs [aria-selected="true"] {
        color: #FFD700 !important;
        border-bottom-color: #FFD700 !important;
    }

    /* ===== EXPANDERS ===== */
    .streamlit-expanderHeader {
        background-color: #002040 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 10px !important;
    }

    .streamlit-expanderContent {
        background-color: #001529 !important;
        border: 1px solid #D4AF37 !important;
        border-top: none !important;
    }

    /* ===== ALERTES ===== */
    .stAlert, [data-testid="stAlert"] {
        background-color: #002040 !important;
        border: 2px solid #D4AF37 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    .stAlert p, [data-testid="stAlert"] p {
        color: #FFFFFF !important;
    }

    /* Success alert */
    [data-testid="stAlert"][data-baseweb="notification"] {
        background-color: #002040 !important;
    }

    /* ===== DATAFRAMES & TABLES ===== */
    .stDataFrame, .stTable {
        background-color: #001529 !important;
    }

    .stDataFrame th, .stTable th {
        background-color: #D4AF37 !important;
        color: #001529 !important;
    }

    .stDataFrame td, .stTable td {
        background-color: #002040 !important;
        color: #FFFFFF !important;
    }

    /* ===== SCROLLBAR CUSTOM ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #001529;
    }

    ::-webkit-scrollbar-thumb {
        background: #D4AF37;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #FFD700;
    }

    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Titre principal
st.title("ELITE PRONOS")

# Initialiser la session state pour la navigation
if 'page' not in st.session_state:
    # Si non connecte, commencer par la page Connexion
    # Si connecte, aller a la page Accueil
    st.session_state.page = "Accueil" if is_logged_in() else "Connexion"

# =====================================================
# SI NON CONNECTE : Afficher Login ou Inscription
# =====================================================
if not is_logged_in():
    # Menu de navigation reduit
    st.sidebar.image("https://via.placeholder.com/150x150/D4AF37/000000?text=EP", width=100)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Bienvenue!")
    st.sidebar.info("Connectez-vous pour acceder a votre espace.")

    pages = ["Connexion", "S'inscrire"]
    default_index = pages.index(st.session_state.page) if st.session_state.page in pages else 0

    menu = st.sidebar.selectbox("Navigation", pages, index=default_index, label_visibility="collapsed")

    if menu != st.session_state.page:
        st.session_state.page = menu

    # Afficher la page correspondante
    if menu == "Connexion":
        afficher_formulaire_login()

    elif menu == "S'inscrire":
        afficher_formulaire_inscription()

    st.sidebar.markdown("---")
    st.sidebar.markdown("<small>Elite Pronos v1.0</small>", unsafe_allow_html=True)

# =====================================================
# SI CONNECTE : Afficher l'application complete
# =====================================================
else:
    user = get_current_user()

    # Menu de navigation dans la sidebar
    st.sidebar.image("https://via.placeholder.com/150x150/D4AF37/000000?text=EP", width=100)
    st.sidebar.markdown("---")

    # Info utilisateur connecte
    st.sidebar.success(f"Connecte: **{user['pseudo']}**")
    if st.sidebar.button("Deconnexion", use_container_width=True):
        logout()
        st.session_state.page = "Connexion"
        st.rerun()

    st.sidebar.markdown("---")

    # Liste des pages pour utilisateur connecte
    pages = ["Accueil", "Tableau de bord", "Reglement", "Admin"]

    # Gerer la page par defaut apres connexion
    if st.session_state.page not in pages:
        st.session_state.page = "Accueil"

    default_index = pages.index(st.session_state.page)

    menu = st.sidebar.selectbox("Navigation", pages, index=default_index)

    if menu != st.session_state.page:
        st.session_state.page = menu

    # === PAGE ACCUEIL ===
    if menu == "Accueil":
        user_id = user['id']  # ID utilisateur pour les requetes

        # Afficher le statut de la base de donnees
        if os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Recuperer la saison et journee dynamiquement
                from modules.database_manager import get_saison_actuelle, get_saison_label, get_journee_courante
                saison_id = get_saison_actuelle()
                saison_label = get_saison_label(saison_id)
                journee_courante = get_journee_courante(saison_id)

                # Compter uniquement les matchs de la journee courante
                cursor.execute("""
                    SELECT COUNT(*) FROM matches
                    WHERE saison_id = ? AND semaine_id = ? AND is_active = 1
                """, (saison_id, journee_courante))
                nb_matchs_journee = cursor.fetchone()[0]

                # === MESSAGE KINGO (en haut) ===
                cursor.execute("SELECT valeur FROM app_settings WHERE cle = 'debrief_accueil'")
                debrief_result = cursor.fetchone()
                if debrief_result and debrief_result[0]:
                    message_bot = debrief_result[0].replace('\\n', '\n')
                else:
                    message_bot = "Bienvenue dans l'arene des pronostiqueurs ! Que les cotes soient en votre faveur cette semaine."

                # Afficher Kingo avec mascotte
                kingo_col1, kingo_col2 = st.columns([1, 4])
                with kingo_col1:
                    kingo_path = os.path.join(os.path.dirname(__file__), 'assets', 'kingo accueil.png')
                    if os.path.exists(kingo_path):
                        from PIL import Image
                        kingo_img = Image.open(kingo_path)
                        st.image(kingo_img, width=80)

                with kingo_col2:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        border: 2px solid #D4AF37;
                        border-radius: 10px;
                        padding: 15px;
                    ">
                        <div style="color: #D4AF37; font-size: 1em; font-weight: bold; margin-bottom: 3px;">
                            👑 KINGO
                        </div>
                        <div style="color: #AAAAAA; font-size: 0.75em; font-style: italic; margin-bottom: 8px;">
                            Le roi des pronostics, celui que tout le monde veut detroner
                        </div>
                        <div style="color: #FFFFFF; font-size: 0.95em;">{message_bot}</div>
                    </div>
                    """, unsafe_allow_html=True)

                if nb_matchs_journee == 0:
                    # Aucun match - verifier si c'est juillet (attente nouveau calendrier)
                    from datetime import datetime
                    mois_actuel = datetime.now().month

                    if mois_actuel == 7:
                        # Juillet = attente du calendrier de la PROCHAINE saison
                        prochaine_saison = saison_id + 1
                        prochain_label = f"{prochaine_saison}-{prochaine_saison + 1}"
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #001529 0%, #002040 100%);
                            border: 2px solid #D4AF37;
                            border-radius: 15px;
                            padding: 30px;
                            text-align: center;
                            margin: 20px 0;
                        ">
                            <div style="font-size: 3em; margin-bottom: 15px;">⏳</div>
                            <h3 style="color: #D4AF37; margin: 0;">En attente du calendrier {prochain_label}</h3>
                            <p style="color: #FFFFFF; margin-top: 15px;">
                                Le calendrier officiel de la Ligue 1 sera bientot disponible.<br>
                                <strong style="color: #FFD700;">Debut prevu : mi-aout {prochaine_saison}</strong>
                            </p>
                            <p style="color: #D4AF37; font-size: 0.9em; margin-top: 20px;">
                                Les inscriptions ouvriront 30 jours avant le coup d'envoi !
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Pas juillet = essayer de charger les matchs automatiquement
                        try:
                            from modules.bot_sourcing import sourcing_journee
                            nb_importes = sourcing_journee(force_reimport=False)
                            if nb_importes > 0:
                                st.rerun()  # Recharger la page avec les nouveaux matchs
                            else:
                                st.info(f"📅 Chargement des matchs J{journee_courante} en cours...")
                                st.button("🔄 Actualiser", on_click=lambda: st.rerun())
                        except Exception as e:
                            st.warning(f"⚠️ Impossible de charger les matchs: {e}")
                else:
                    # === TUNNEL DE TRANSITION TEMPOREL ===
                    from modules.database_manager import get_countdown_pronostics_journee, get_date_premiere_journee
                    from datetime import datetime, timedelta

                    countdown = get_countdown_pronostics_journee(journee_courante, saison_id)
                    date_journee = get_date_premiere_journee(journee_courante, saison_id)

                    # Verifier si des scores sont disponibles pour cette journee
                    cursor.execute("""
                        SELECT COUNT(*) FROM matches
                        WHERE saison_id = ? AND semaine_id = ? AND score_final_home IS NOT NULL
                    """, (saison_id, journee_courante))
                    nb_matchs_avec_score = cursor.fetchone()[0]

                    now = datetime.now()
                    date_fermeture = date_journee - timedelta(hours=1) if date_journee else now

                    # Determiner l'etat du tunnel
                    if countdown and not countdown.get('expired', False):
                        # ETAT 1: Countdown compact en haut (2 lignes)
                        st.markdown(f"""
                        <div style="
                            background: #001529;
                            border: 1px solid #D4AF37;
                            border-radius: 8px;
                            padding: 10px 20px;
                            margin: 10px 0;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        ">
                            <span style="color: #D4AF37;">⏱️ Pronostics J{journee_courante}</span>
                            <span style="color: #FFD700; font-weight: bold; font-size: 1.1em;">
                                {countdown['days']}j {countdown['hours']}h {countdown['minutes']}m
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                        # Verifier si l'utilisateur a deja valide ses pronostics
                        cursor.execute("""
                            SELECT m.id, m.equipe_home, m.equipe_away, p.score_prono_home, p.score_prono_away, p.mise_points
                            FROM predictions p
                            JOIN matches m ON p.match_id = m.id
                            WHERE p.user_id = ? AND m.saison_id = ? AND m.semaine_id = ?
                        """, (user_id, saison_id, journee_courante))
                        mes_pronos = cursor.fetchall()

                        if mes_pronos:
                            # === BLOC 2: MES PRONOSTICS (remplace BLOC 1) ===
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, #0A3D0A 0%, #001529 100%);
                                border: 1px solid #00FF00;
                                border-radius: 10px;
                                padding: 15px;
                                margin: 10px 0;
                            ">
                                <div style="color: #00FF00; font-size: 0.9em; margin-bottom: 10px; text-align: center;">✅ MES PRONOSTICS J{journee_courante}</div>
                            """, unsafe_allow_html=True)

                            for match_id, home, away, score_h, score_a, mise in mes_pronos:
                                st.markdown(f"""
                                <div style="
                                    display: flex; justify-content: space-between; align-items: center;
                                    padding: 8px; margin: 5px 0; background: #002040; border-radius: 6px;
                                ">
                                    <span style="color: #FFFFFF; flex: 1; font-size: 0.9em;">{home}</span>
                                    <span style="color: #4488FF; font-weight: bold;">{score_h} - {score_a}</span>
                                    <span style="color: #FFFFFF; flex: 1; text-align: right; font-size: 0.9em;">{away}</span>
                                    <span style="color: #00FF00; font-weight: bold; margin-left: 10px;">{mise}pts</span>
                                </div>
                                """, unsafe_allow_html=True)

                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            # === BLOC 1: MATCHS DE LA SEMAINE AVEC COTES ===
                            cursor.execute("""
                                SELECT equipe_home, equipe_away, cote_home, cote_draw, cote_away
                                FROM matches
                                WHERE saison_id = ? AND semaine_id = ? AND is_active = 1
                                ORDER BY date_match
                            """, (saison_id, journee_courante))
                            matchs_semaine = cursor.fetchall()

                            if matchs_semaine:
                                st.markdown(f"""
                                <div style="
                                    background: #001529;
                                    border: 1px solid #D4AF37;
                                    border-radius: 10px;
                                    padding: 15px;
                                    margin: 10px 0;
                                ">
                                    <div style="color: #D4AF37; font-size: 0.9em; margin-bottom: 10px; text-align: center;">⚽ MATCHS J{journee_courante}</div>
                                """, unsafe_allow_html=True)

                                for home, away, cote_h, cote_n, cote_a in matchs_semaine:
                                    st.markdown(f"""
                                    <div style="
                                        display: flex; justify-content: space-between; align-items: center;
                                        padding: 8px; margin: 5px 0; background: #002040; border-radius: 6px;
                                    ">
                                        <div style="flex: 1; text-align: center;">
                                            <span style="color: #FFFFFF; font-size: 0.9em;">{home}</span>
                                            <span style="color: #FF0000; font-size: 0.8em;"> ({cote_h})</span>
                                        </div>
                                        <div style="color: #AAAAAA; font-size: 0.8em; padding: 0 5px;">N:{cote_n}</div>
                                        <div style="flex: 1; text-align: center;">
                                            <span style="color: #FFFFFF; font-size: 0.9em;">{away}</span>
                                            <span style="color: #FF0000; font-size: 0.8em;"> ({cote_a})</span>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                st.markdown("</div>", unsafe_allow_html=True)

                    elif nb_matchs_avec_score > 0:
                        # ETAT 4: Des scores sont disponibles - Afficher RESULTATS + TOUS LES PRONOS
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #1a472a 0%, #2d5a3c 100%);
                            border: 2px solid #00FF00;
                            border-radius: 15px;
                            padding: 20px;
                            text-align: center;
                            margin: 20px 0;
                        ">
                            <h4 style="color: #00FF00; margin: 0;">📊 RESULTATS J{journee_courante}</h4>
                            <p style="color: #FFFFFF; margin: 10px 0 0 0;">
                                {nb_matchs_avec_score}/{nb_matchs_journee} match(s) termine(s)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Afficher chaque match avec son score + tous les pronos des joueurs
                        cursor.execute("""
                            SELECT m.id, m.equipe_home, m.equipe_away, m.score_final_home, m.score_final_away,
                                   m.score_mi_temps_home, m.score_mi_temps_away
                            FROM matches m
                            WHERE m.saison_id = ? AND m.semaine_id = ?
                            ORDER BY m.date_match
                        """, (saison_id, journee_courante))
                        matchs_journee = cursor.fetchall()

                        for match_id, home, away, score_h, score_a, mi_h, mi_a in matchs_journee:
                            # Score du match (ou en cours)
                            if score_h is not None:
                                score_display = f"{score_h} - {score_a}"
                                score_color = "#00FF00"
                                statut = "Terminé"
                            elif mi_h is not None:
                                score_display = f"{mi_h} - {mi_a}"
                                score_color = "#FFD700"
                                statut = "Mi-temps"
                            else:
                                score_display = "- vs -"
                                score_color = "#AAAAAA"
                                statut = "A venir"

                            st.markdown(f"""
                            <div style="background: #001529; border: 1px solid #D4AF37; border-radius: 10px; padding: 15px; margin: 10px 0;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <span style="color: #FFFFFF; font-weight: bold;">{home}</span>
                                    <div style="text-align: center;">
                                        <span style="color: {score_color}; font-weight: bold; font-size: 1.3em;">{score_display}</span>
                                        <div style="color: #AAAAAA; font-size: 0.7em;">{statut}</div>
                                    </div>
                                    <span style="color: #FFFFFF; font-weight: bold;">{away}</span>
                                </div>
                            """, unsafe_allow_html=True)

                            # Recuperer les pronos de tous les joueurs pour ce match
                            cursor.execute("""
                                SELECT u.pseudo, p.score_prono_home, p.score_prono_away, p.mise_points
                                FROM predictions p
                                JOIN utilisateurs u ON p.user_id = u.id
                                WHERE p.match_id = ?
                                ORDER BY u.pseudo
                            """, (match_id,))
                            pronos_match = cursor.fetchall()

                            if pronos_match:
                                for pseudo, ph, pa, mise in pronos_match:
                                    # Verifier si le prono est gagnant
                                    prono_ok = ""
                                    if score_h is not None:
                                        if ph == score_h and pa == score_a:
                                            prono_ok = "🎯"  # Score exact
                                        elif (ph > pa and score_h > score_a) or (ph < pa and score_h < score_a) or (ph == pa and score_h == score_a):
                                            prono_ok = "✅"  # Bon 1N2
                                        else:
                                            prono_ok = "❌"

                                    st.markdown(f"""
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 5px 10px; border-top: 1px solid #333;">
                                        <span style="color: #D4AF37;">@{pseudo}</span>
                                        <span style="color: #4488FF; font-weight: bold;">{ph} - {pa}</span>
                                        <span style="color: #00FF00;">{mise} pts</span>
                                        <span style="font-size: 1.1em;">{prono_ok}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                            st.markdown("</div>", unsafe_allow_html=True)

                    elif date_journee and now < date_fermeture + timedelta(hours=1):
                        # ETAT 2: H+0 a H+1 apres deadline - Rectangle rouge PRONOSTICS CLOS
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%);
                            border: 2px solid #FF4444;
                            border-radius: 15px;
                            padding: 20px;
                            text-align: center;
                            margin: 20px 0;
                        ">
                            <h4 style="color: #FFFFFF; margin: 0;">⏰ PRONOSTICS CLOS</h4>
                            <p style="color: #FFD700; margin: 10px 0 0 0;">
                                Les pronostics de la J{journee_courante} sont fermes.<br>
                                <span style="color: #FFFFFF;">Premier match dans moins d'une heure !</span>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Afficher la synthese des pronostics apres cloture
                        cursor.execute("""
                            SELECT m.id, m.equipe_home, m.equipe_away, m.cote_home, m.cote_draw, m.cote_away
                            FROM matches m
                            WHERE m.saison_id = ? AND m.semaine_id = ? AND m.is_active = 1
                            ORDER BY m.date_match
                        """, (saison_id, journee_courante))
                        matchs_synthese = cursor.fetchall()

                        if matchs_synthese:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                                border: 2px solid #9b59b6;
                                border-radius: 15px;
                                padding: 20px;
                                margin: 15px 0;
                            ">
                                <h4 style="color: #9b59b6; margin: 0 0 15px 0; text-align: center;">
                                    📋 SYNTHESE DES PRONOS J{journee_courante}
                                </h4>
                            """, unsafe_allow_html=True)

                            for match_id, home, away, cote_h, cote_n, cote_a in matchs_synthese:
                                # Recuperer les pronostics pour ce match
                                cursor.execute("""
                                    SELECT u.pseudo, p.score_prono_home, p.score_prono_away, p.mise_points
                                    FROM predictions p
                                    JOIN utilisateurs u ON p.user_id = u.id
                                    WHERE p.match_id = ?
                                    ORDER BY u.pseudo
                                """, (match_id,))
                                pronos_match = cursor.fetchall()

                                st.markdown(f"""
                                <div style="background: #002040; border-radius: 10px; padding: 15px; margin: 10px 0; border-left: 3px solid #D4AF37;">
                                    <div style="color: #D4AF37; font-weight: bold; margin-bottom: 10px; text-align: center;">
                                        {home} vs {away}
                                    </div>
                                """, unsafe_allow_html=True)

                                if pronos_match:
                                    for pseudo, score_h, score_a, mise in pronos_match:
                                        st.markdown(f"""
                                        <div style="display: flex; justify-content: space-between; padding: 5px 10px; border-bottom: 1px solid #333;">
                                            <span style="color: #FFFFFF;">@{pseudo}</span>
                                            <span style="color: #FFD700; font-weight: bold;">{score_h}-{score_a}</span>
                                            <span style="color: #FFFFFF; font-size: 0.9em;">{mise} pts</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.markdown("""<p style="color: #FFFFFF; text-align: center; font-size: 0.9em;">Aucun pronostic</p>""", unsafe_allow_html=True)

                                st.markdown("</div>", unsafe_allow_html=True)

                            st.markdown("</div>", unsafe_allow_html=True)

                    else:
                        # ETAT 3: H+1+ apres deadline, pas encore de scores - Afficher SYNTHESE
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                            border: 2px solid #9b59b6;
                            border-radius: 15px;
                            padding: 20px;
                            text-align: center;
                            margin: 20px 0;
                        ">
                            <h4 style="color: #9b59b6; margin: 0;">📋 SYNTHESE DES PRONOS J{journee_courante}</h4>
                            <p style="color: #FFFFFF; margin: 10px 0 0 0;">
                                Les matchs sont en cours. Resultats a venir !
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Afficher la synthese complete des pronostics
                        cursor.execute("""
                            SELECT m.id, m.equipe_home, m.equipe_away, m.cote_home, m.cote_draw, m.cote_away
                            FROM matches m
                            WHERE m.saison_id = ? AND m.semaine_id = ? AND m.is_active = 1
                            ORDER BY m.date_match
                        """, (saison_id, journee_courante))
                        matchs_synthese = cursor.fetchall()

                        if matchs_synthese:
                            for match_id, home, away, cote_h, cote_n, cote_a in matchs_synthese:
                                cursor.execute("""
                                    SELECT u.pseudo, p.score_prono_home, p.score_prono_away, p.mise_points
                                    FROM predictions p
                                    JOIN utilisateurs u ON p.user_id = u.id
                                    WHERE p.match_id = ?
                                    ORDER BY u.pseudo
                                """, (match_id,))
                                pronos_match = cursor.fetchall()

                                st.markdown(f"""
                                <div style="background: #002040; border-radius: 10px; padding: 15px; margin: 10px 0; border-left: 3px solid #9b59b6;">
                                    <div style="color: #D4AF37; font-weight: bold; margin-bottom: 10px; text-align: center;">
                                        {home} vs {away}
                                    </div>
                                """, unsafe_allow_html=True)

                                if pronos_match:
                                    for pseudo, score_h, score_a, mise in pronos_match:
                                        st.markdown(f"""
                                        <div style="display: flex; justify-content: space-between; padding: 5px 10px; border-bottom: 1px solid #333;">
                                            <span style="color: #FFFFFF;">@{pseudo}</span>
                                            <span style="color: #FFD700; font-weight: bold;">{score_h}-{score_a}</span>
                                            <span style="color: #FFFFFF; font-size: 0.9em;">{mise} pts</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.markdown("""<p style="color: #FFFFFF; text-align: center; font-size: 0.9em;">Aucun pronostic</p>""", unsafe_allow_html=True)

                                st.markdown("</div>", unsafe_allow_html=True)

                conn.close()

            except Exception as e:
                st.error(f"Erreur de lecture: {e}")

        # Bouton Tableau de bord en bas
        st.markdown("---")
        if st.button("📊 TABLEAU DE BORD", type="primary", use_container_width=True):
            st.session_state.page = "Tableau de bord"
            st.rerun()

    # === PAGE TABLEAU DE BORD ===
    elif menu == "Tableau de bord":
        afficher_dashboard(user)

    # === PAGE REGLEMENT ===
    elif menu == "Reglement":
        afficher_reglement()

    # === PAGE ADMIN ===
    elif menu == "Admin":
        afficher_panel_admin()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("<small>Elite Pronos v1.0</small>", unsafe_allow_html=True)
