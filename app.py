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
        color: #888888 !important;
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
    # Si connecte, aller au Tableau de bord
    st.session_state.page = "Tableau de bord" if is_logged_in() else "Connexion"

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

    menu = st.sidebar.selectbox("", pages, index=default_index)

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
        afficher_header_utilisateur()

        st.header("Bienvenue sur Elite Pronos")
        st.write("Votre plateforme de pronostics football entre amis!")

        # Afficher le statut de la base de donnees
        if os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE statut = 'Actif'")
                nb_users = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM matches WHERE is_active = 1")
                nb_matchs = cursor.fetchone()[0]

                # Recuperer la saison dynamiquement
                from modules.database_manager import get_saison_actuelle, get_saison_label
                saison_label = get_saison_label(get_saison_actuelle())

                col1, col2, col3 = st.columns(3)
                col1.metric("Joueurs actifs", nb_users)
                col2.metric("Matchs en cours", nb_matchs)
                col3.metric("Saison", saison_label)

                # === COUNTDOWN / MESSAGE ATTENTE CALENDRIER ===
                st.markdown("---")

                if nb_matchs == 0:
                    # Aucun match en base - afficher message d'attente
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
                        <h3 style="color: #D4AF37; margin: 0;">En attente du calendrier {saison_label}</h3>
                        <p style="color: #FFFFFF; margin-top: 15px;">
                            Le calendrier officiel de la Ligue 1 sera bientot disponible.<br>
                            <strong style="color: #FFD700;">Debut prevu : 23 aout 2026</strong>
                        </p>
                        <p style="color: #D4AF37; font-size: 0.9em; margin-top: 20px;">
                            Les inscriptions ouvriront 30 jours avant le coup d'envoi !
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Matchs disponibles - afficher countdown prochain match
                    from modules.database_manager import get_journee_courante, get_countdown_pronostics_journee
                    journee = get_journee_courante()
                    countdown = get_countdown_pronostics_journee(journee)

                    if countdown and not countdown.get('expired', False):
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #001529 0%, #002040 100%);
                            border: 2px solid #D4AF37;
                            border-radius: 15px;
                            padding: 25px;
                            text-align: center;
                            margin: 20px 0;
                        ">
                            <h4 style="color: #D4AF37; margin: 0 0 15px 0;">⏱️ PRONOSTICS J{journee} - TEMPS RESTANT</h4>
                            <div style="display: flex; justify-content: center; gap: 20px;">
                                <div style="text-align: center;">
                                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">{countdown['days']:02d}</div>
                                    <div style="color: #D4AF37; font-size: 0.8em;">JOURS</div>
                                </div>
                                <div style="font-size: 2.5em; color: #FFD700;">:</div>
                                <div style="text-align: center;">
                                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">{countdown['hours']:02d}</div>
                                    <div style="color: #D4AF37; font-size: 0.8em;">HEURES</div>
                                </div>
                                <div style="font-size: 2.5em; color: #FFD700;">:</div>
                                <div style="text-align: center;">
                                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">{countdown['minutes']:02d}</div>
                                    <div style="color: #D4AF37; font-size: 0.8em;">MIN</div>
                                </div>
                            </div>
                            <p style="color: #888; font-size: 0.8em; margin-top: 15px;">
                                Fermeture : {countdown.get('date_fermeture', 'N/A')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif countdown and countdown.get('expired', False):
                        st.markdown("""
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
                                Les pronostics de cette journee sont fermes. Resultats bientot !
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                # === DEBRIEF BOT ===
                cursor.execute("SELECT valeur FROM app_settings WHERE cle = 'debrief_accueil'")
                debrief_result = cursor.fetchone()
                conn.close()

                if debrief_result and debrief_result[0]:
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        border: 2px solid #9b59b6;
                        border-radius: 15px;
                        padding: 20px;
                        margin: 15px 0;
                    ">
                        <div style="color: #9b59b6; font-size: 0.9em; margin-bottom: 10px;">
                            🤖 LE BOT ELITE
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(debrief_result[0].replace('\\n', '\n'))
                    st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erreur de lecture: {e}")

        st.markdown("---")
        st.markdown("### Pret a jouer?")
        if st.button("VOIR MON TABLEAU DE BORD", type="primary"):
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
