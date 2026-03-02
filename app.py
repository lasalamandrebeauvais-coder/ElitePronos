import streamlit as st
import sys
import os

# Ajouter le chemin du projet pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration de la page
st.set_page_config(
    page_title="Elite Pronos",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import des modules (Supabase uniquement)
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
from modules.reglement_st import afficher_reglement
from modules.scheduler_resultats import get_scheduler_status

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

    /* ===== FLECHES EVOLUTION CLASSEMENT ===== */
    [data-testid="stMarkdownContainer"] span.evol-up,
    .stMarkdown span.evol-up,
    span.evol-up {
        color: #00FF00 !important;
        font-weight: bold !important;
    }
    [data-testid="stMarkdownContainer"] span.evol-down,
    .stMarkdown span.evol-down,
    span.evol-down {
        color: #FF4444 !important;
        font-weight: bold !important;
    }
    [data-testid="stMarkdownContainer"] span.evol-same,
    .stMarkdown span.evol-same,
    span.evol-same {
        color: #888888 !important;
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

    /* ===== COLONNES & CONTENEURS TRANSPARENTS ===== */
    [data-testid="stColumn"],
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    .stColumn, .block-container {
        background-color: transparent !important;
    }

    [data-testid="stImage"] {
        background-color: transparent !important;
    }

    /* Conteneurs internes Streamlit */
    [data-testid="stElementContainer"],
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stImageContainer"],
    .element-container,
    [data-testid="stColumn"] > div,
    [data-testid="stColumn"] > div > div {
        background-color: transparent !important;
        background: transparent !important;
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
        background-color: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        color: #FFD700 !important;
        border-bottom-color: #FFD700 !important;
    }

    /* Tab panels - FORCER fond sombre sur TOUS les conteneurs */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #001529 !important;
    }

    .stTabs [data-baseweb="tab-panel"] > div,
    .stTabs [data-baseweb="tab-panel"] > div > div,
    .stTabs [data-baseweb="tab-panel"] > div > div > div,
    .stTabs [data-baseweb="tab-panel"] iframe,
    .stTabs [data-baseweb="tab-panel"] .element-container,
    .stTabs [data-baseweb="tab-panel"] .stMarkdown,
    .stTabs [data-baseweb="tab-panel"] [data-testid="stMarkdownContainer"] {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* Forcer les tableaux dans les tabs */
    .stTabs table {
        background-color: #001529 !important;
    }

    .stTabs table th {
        background-color: #D4AF37 !important;
        color: #001529 !important;
    }

    .stTabs table td {
        background-color: #001529 !important;
        color: #FFFFFF !important;
    }

    .stTabs table td span {
        color: inherit !important;
    }

    /* ===== EXPANDERS (anciens + nouveaux selectors) ===== */
    .streamlit-expanderHeader,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] [data-testid="stExpanderToggleDetails"] {
        background-color: #002040 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 10px !important;
    }

    .streamlit-expanderContent,
    [data-testid="stExpander"] > div[data-testid="stExpanderDetails"],
    [data-testid="stExpander"] [role="group"] {
        background-color: #001529 !important;
        border: 1px solid #D4AF37 !important;
        border-top: none !important;
    }

    [data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
    }

    /* ===== FORMS ===== */
    [data-testid="stForm"],
    [data-testid="stForm"] > div,
    .stForm {
        background-color: #001529 !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 10px !important;
    }

    /* ===== CONTAINERS AVEC BORDURE ===== */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: transparent !important;
        background: transparent !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* ===== CATCH-ALL : forcer fond sombre sur TOUS les divs internes ===== */
    .main .block-container,
    .main .block-container > div,
    .main .block-container > div > div,
    .main .block-container > div > div > div {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* Widgets internes Streamlit */
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stCheckbox"],
    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"],
    [data-testid="stRadio"] label {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }

    /* Multiselect / Tags */
    [data-baseweb="tag"] {
        background-color: #D4AF37 !important;
        color: #001529 !important;
    }

    /* Toast / Snackbar */
    [data-testid="stToast"],
    [data-testid="stSnackbar"] {
        background-color: #002040 !important;
        color: #FFFFFF !important;
        border: 1px solid #D4AF37 !important;
    }

    /* Dialog / Modal */
    [data-testid="stModal"] > div,
    [role="dialog"] {
        background-color: #001529 !important;
        border: 2px solid #D4AF37 !important;
    }

    /* Number input buttons */
    .stNumberInput button {
        background-color: #002040 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
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
        font-size: 0.65rem !important;
    }

    .stDataFrame td, .stTable td {
        background-color: #002040 !important;
        color: #FFFFFF !important;
        font-size: 0.65rem !important;
    }

    /* Cellules compactes dans les dataframes */
    .stDataFrame [data-testid="glideDataEditor"] {
        font-size: 0.65rem !important;
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
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    .viewerBadge_container__r5tak {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    #stDecoration {display: none !important;}

    /* ===== MOBILE RESPONSIVE ===== */

    /* Tableaux larges : scroll horizontal */
    .ep-table-scroll {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin: 0 -5px;
        padding: 0 5px;
    }

    /* Classement header + rows : largeur min pour scroll */
    .ep-classement-header, .ep-classement-row {
        min-width: 420px;
    }

    @media (max-width: 768px) {

        /* Headings plus compacts */
        h1 { font-size: 1.4em !important; }
        h2 { font-size: 1.15em !important; }
        h3 { font-size: 1em !important; }

        /* Boutons */
        .stButton > button {
            padding: 8px 16px !important;
            font-size: 0.85em !important;
            border-radius: 20px !important;
        }

        /* Tabs : texte plus petit */
        .stTabs [data-baseweb="tab"] {
            font-size: 0.7em !important;
            padding: 6px 8px !important;
        }

        /* Metrics */
        [data-testid="metric-container"] {
            padding: 10px !important;
        }

        /* Match row grids : colonnes reduites */
        .ep-match-row {
            grid-template-columns: 2fr 45px 2fr 40px !important;
            font-size: 0.75em !important;
            padding: 5px 6px !important;
        }
        .ep-match-status {
            font-size: 0.65em !important;
        }

        /* Countdown boxes */
        .ep-countdown {
            gap: 8px !important;
        }
        .ep-countdown > div {
            min-width: 45px !important;
            padding: 6px 8px !important;
        }
        .ep-countdown > div > div:first-child {
            font-size: 1.2em !important;
        }

        /* Duel : stack vertical */
        .ep-duel {
            flex-direction: column !important;
            align-items: center !important;
            gap: 10px !important;
        }
        .ep-duel > div {
            min-width: 180px !important;
            width: 80% !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            min-width: 200px !important;
            max-width: 250px !important;
        }
    }

    @media (max-width: 480px) {

        /* Encore plus compact */
        h1 { font-size: 1.2em !important; }
        h2 { font-size: 1em !important; }

        /* Tabs encore plus petits */
        .stTabs [data-baseweb="tab"] {
            font-size: 0.65em !important;
            padding: 5px 5px !important;
        }

        /* Match row */
        .ep-match-row {
            grid-template-columns: 1fr 45px 1fr !important;
            font-size: 0.7em !important;
        }

        /* Countdown */
        .ep-countdown > div {
            min-width: 38px !important;
            padding: 5px 6px !important;
        }

        /* Duel full width */
        .ep-duel > div {
            width: 95% !important;
            padding: 12px 15px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Mascotte + Titre principal
_kingo_title_path = os.path.join(os.path.dirname(__file__), 'assets', 'kingo accueil.png')
_kt_col1, _kt_col2 = st.columns([1, 5])
with _kt_col1:
    if os.path.exists(_kingo_title_path):
        try:
            from PIL import Image as _PILImage
            st.image(_PILImage.open(_kingo_title_path), width=90)
        except Exception:
            pass
with _kt_col2:
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

    # Liste des pages pour utilisateur connecte (Admin visible uniquement pour les admins)
    from modules.database_manager import get_is_admin_cached
    is_admin = get_is_admin_cached(user['id'])
    if is_admin:
        pages = ["Admin", "Accueil", "Tableau de bord", "Reglement"]
    else:
        pages = ["Accueil", "Tableau de bord", "Reglement"]

    # Gerer la page par defaut apres connexion
    if st.session_state.page not in pages:
        st.session_state.page = "Admin" if is_admin else "Accueil"

    default_index = pages.index(st.session_state.page)

    menu = st.sidebar.selectbox("Navigation", pages, index=default_index)

    if menu != st.session_state.page:
        st.session_state.page = menu

    # === PAGE ACCUEIL ===
    if menu == "Accueil":
        user_id = user['id']  # ID utilisateur pour les requetes

        # Utiliser Supabase pour l'accueil
        try:
            from modules.supabase_db import get_supabase
            from modules.database_manager import (get_saison_actuelle, get_saison_label, get_journee_courante,
                get_countdown_pronostics_journee_cached, get_mvp_semaine, get_matchs_journee_cached,
                get_user_predictions_cached, get_rivaux_ids_cached, get_rivaux_predictions_cached,
                get_user_joker_cached, get_recap_data_cached)

            supabase = get_supabase()
            saison_id = get_saison_actuelle()
            saison_label = get_saison_label(saison_id)
            journee_courante = get_journee_courante(saison_id)

            # Recuperer le countdown pour les pronostics (cache 10s)
            countdown = get_countdown_pronostics_journee_cached(journee_courante, saison_id)

            # Compter uniquement les matchs de la journee courante (cache 30s)
            matchs_journee = get_matchs_journee_cached(saison_id, journee_courante)
            nb_matchs_journee = len(matchs_journee)

            # === SYNTHESE KINGO (en haut) ===
            from modules.synthese_st import get_synthese_accueil

            # Generer la synthese dynamique
            synthese = get_synthese_accueil(saison_id, journee_courante)
            message_kingo = synthese['commentaire']

            # Afficher bloc Kingo style journal / news
            from datetime import datetime as _dt_now
            _date_str = _dt_now.now().strftime("%d/%m/%Y")
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a1a2e 100%);
                border: 2px solid #D4AF37;
                border-radius: 12px;
                padding: 0;
                margin: 10px 0 15px 0;
                overflow: hidden;
            ">
                <!-- Bandeau titre journal -->
                <div style="
                    background: linear-gradient(90deg, #D4AF37 0%, #B8960C 100%);
                    padding: 8px 18px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <span style="color: #000; font-size: 1.1em; font-weight: 900; letter-spacing: 1px; text-transform: uppercase;">
                        KINGO NEWS
                    </span>
                    <span style="color: #000; font-size: 0.75em; font-weight: 600;">
                        Journee {journee_courante} &mdash; {_date_str}
                    </span>
                </div>
                <!-- Contenu article -->
                <div style="padding: 18px 20px 15px 20px;">
                    <div style="
                        color: #D4AF37;
                        font-size: 1.15em;
                        font-weight: 800;
                        margin-bottom: 6px;
                        letter-spacing: 0.5px;
                    ">
                        Synthese J{journee_courante}
                    </div>
                    <div style="
                        color: #8b949e;
                        font-size: 0.8em;
                        font-style: italic;
                        margin-bottom: 12px;
                        padding-bottom: 10px;
                        border-bottom: 1px solid #30363d;
                    ">
                        Par Kingo, le roi des pronostics
                    </div>
                    <div style="
                        color: #e6edf3;
                        font-size: 1.05em;
                        line-height: 1.7;
                        text-align: justify;
                    ">{message_kingo}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # === BANDEAU MVP DE LA SEMAINE PRECEDENTE ===
            if journee_courante > 1:
                mvp_data = get_mvp_semaine(journee_courante - 1, saison_id)
                if mvp_data:
                    mvp_pseudo = mvp_data['pseudo']
                    mvp_pts = mvp_data['points_journee']
                    is_me = (mvp_data['user_id'] == user_id)
                    if is_me:
                        mvp_msg = f"C'est vous ! Vous avez domine la J{journee_courante - 1}"
                    else:
                        mvp_msg = f"A detroner cette semaine !"
                    st.markdown(f"""
                    <style>
                        @keyframes shimmer {{
                            0% {{ background-position: -200% center; }}
                            100% {{ background-position: 200% center; }}
                        }}
                        @keyframes pulse-glow {{
                            0%, 100% {{ box-shadow: 0 0 15px rgba(212,175,55,0.4); }}
                            50% {{ box-shadow: 0 0 30px rgba(255,215,0,0.7); }}
                        }}
                        .mvp-banner {{
                            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%);
                            border: 2px solid #D4AF37;
                            border-radius: 12px;
                            padding: 15px 20px;
                            margin: 10px 0;
                            text-align: center;
                            animation: pulse-glow 3s ease-in-out infinite;
                            position: relative;
                            overflow: hidden;
                        }}
                        .mvp-banner::before {{
                            content: '';
                            position: absolute;
                            top: 0; left: 0; right: 0; bottom: 0;
                            background: linear-gradient(90deg, transparent, rgba(212,175,55,0.1), transparent);
                            background-size: 200% 100%;
                            animation: shimmer 4s linear infinite;
                        }}
                        .mvp-title {{
                            color: #D4AF37;
                            font-size: 0.7em;
                            letter-spacing: 3px;
                            text-transform: uppercase;
                            margin-bottom: 6px;
                        }}
                        .mvp-pseudo {{
                            background: linear-gradient(90deg, #D4AF37, #FFD700, #D4AF37);
                            background-size: 200% auto;
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                            font-size: 1.4em;
                            font-weight: bold;
                            animation: shimmer 3s linear infinite;
                        }}
                        .mvp-points {{
                            display: inline-block;
                            background: linear-gradient(135deg, #D4AF37, #B8960C);
                            color: #001529;
                            font-weight: bold;
                            font-size: 0.85em;
                            padding: 3px 12px;
                            border-radius: 20px;
                            margin-top: 6px;
                        }}
                        .mvp-sub {{
                            color: #AAAAAA;
                            font-size: 0.75em;
                            font-style: italic;
                            margin-top: 4px;
                        }}
                    </style>
                    <div class="mvp-banner">
                        <div class="mvp-title">Meilleur joueur J{journee_courante - 1}</div>
                        <div class="mvp-pseudo">🏆 {mvp_pseudo} 🏆</div>
                        <div class="mvp-points">{mvp_pts} pts</div>
                        <div class="mvp-sub">{mvp_msg}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # === BLOC COMPTE À REBOURS / PRONOSTICS FERMÉS ===
            if countdown and not countdown.get('expired', False):
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #D4AF37 0%, #B8960C 100%);
                        border-radius: 10px;
                        padding: 12px 20px;
                        margin: 10px 0;
                        text-align: center;
                    ">
                        <div style="color: #001529; font-size: 0.75em; margin-bottom: 8px; font-weight: bold;">
                            ⏱️ FERMETURE DES PRONOSTICS
                        </div>
                        <div class="ep-countdown" style="display: flex; justify-content: center; gap: 15px;">
                            <div style="background: #001529; border-radius: 8px; padding: 8px 15px; min-width: 60px;">
                                <div style="color: #FFD700; font-size: 1.5em; font-weight: bold;">{countdown['days']}</div>
                                <div style="color: #FFFFFF; font-size: 0.7em;">JOURS</div>
                            </div>
                            <div style="background: #001529; border-radius: 8px; padding: 8px 15px; min-width: 60px;">
                                <div style="color: #FFD700; font-size: 1.5em; font-weight: bold;">{countdown['hours']}</div>
                                <div style="color: #FFFFFF; font-size: 0.7em;">HEURES</div>
                            </div>
                            <div style="background: #001529; border-radius: 8px; padding: 8px 15px; min-width: 60px;">
                                <div style="color: #FFD700; font-size: 1.5em; font-weight: bold;">{countdown['minutes']}</div>
                                <div style="color: #FFFFFF; font-size: 0.7em;">MINUTES</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            elif countdown and countdown.get('expired', False):
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%);
                    border: 2px solid #FF4444;
                    border-radius: 10px;
                    padding: 12px 20px;
                    margin: 10px 0;
                    text-align: center;
                ">
                    <div style="color: #FFFFFF; font-size: 0.9em; font-weight: bold;">
                        ⏰ PRONOSTICS FERMÉS
                    </div>
                    <div style="color: #FFD700; font-size: 0.75em; margin-top: 5px;">
                        Les matchs de la J{journee_courante} sont en cours ou terminés
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # === BLOC MES PRONOSTICS DE LA JOURNÉE / MATCHS LIVE ===
            pronostics_ouverts = countdown and not countdown.get('expired', False)

            if pronostics_ouverts:
                # PRONOSTICS OUVERTS: Afficher les pronostics du joueur (cache 15s)
                predictions_data = get_user_predictions_cached(user_id, saison_id, journee_courante, match_ids_str if 'match_ids_str' in dir() else '')
                mes_pronos_accueil = [(p['matches']['id'], p['matches']['equipe_home'], p['matches']['equipe_away'], p['score_prono_home'], p['score_prono_away'], p['mise_points']) for p in predictions_data if p.get('matches') and p['matches'].get('semaine_id') == journee_courante]

                if mes_pronos_accueil:
                    _total_mise = sum(m[5] or 0 for m in mes_pronos_accueil)
                    _budget_total = 100
                    _reste = _budget_total - _total_mise
                    _couleur_reste = "#00FF00" if _reste >= 0 else "#FF4444"

                    st.markdown(f"""<div style="background: linear-gradient(135deg, #001529 0%, #002040 100%); border: 1px solid #4488FF; border-radius: 10px; padding: 12px; margin: 10px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="color: #4488FF; font-size: 0.85em; font-weight: bold;">⚽ MES PRONOSTICS DE LA JOURNÉE</span>
                            <span style="font-size: 0.8em;">
                                <span style="color: #AAAAAA;">Budget :</span>
                                <span style="color: #FFD700; font-weight: bold;">{_total_mise}</span>
                                <span style="color: #AAAAAA;">/</span>
                                <span style="color: #AAAAAA;">{_budget_total}</span>
                                <span style="color: {_couleur_reste}; font-size: 0.85em; margin-left: 4px;">({_reste} restant)</span>
                            </span>
                        </div>
                    """, unsafe_allow_html=True)

                    for match_id, home, away, score_h, score_a, mise in mes_pronos_accueil:
                        st.markdown(f"""<div class="ep-match-row" style="display: grid; grid-template-columns: 2fr 50px 2fr 45px; align-items: center; padding: 6px 8px; margin: 3px 0; background: #002040; border-radius: 5px; font-size: 0.8em;">
                            <span style="color: #FFFFFF; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{home}</span>
                            <span style="color: #4488FF; font-weight: bold; text-align: center;">{score_h}-{score_a}</span>
                            <span style="color: #FFFFFF; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{away}</span>
                            <span class="ep-match-status" style="color: #00FF00; font-weight: bold; text-align: center;">{mise}pt</span>
                        </div>""", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                # PRONOSTICS FERMÉS: Afficher les matchs avec scores live (reutilise matchs_journee)
                from datetime import datetime
                matchs_live = [(m['id'], m['equipe_home'], m['equipe_away'], m.get('date_match'), m.get('score_mi_temps_home'), m.get('score_mi_temps_away'), m.get('score_final_home'), m.get('score_final_away'), m.get('status', 'SCHEDULED')) for m in matchs_journee]

                if matchs_live:
                    # Statut du bot de mise a jour
                    bot_status = get_scheduler_status()

                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #001529 0%, #002040 100%);
                        border: 1px solid #00FF00;
                        border-radius: 10px;
                        padding: 12px;
                        margin: 10px 0;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="color: #00FF00; font-size: 0.85em; font-weight: bold;">
                                🔴 MATCHS EN DIRECT
                            </span>
                            <span style="color: {bot_status['couleur']}; font-size: 0.65em;">
                                ⚙️ {bot_status['message']}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)

                    jours_semaine = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

                    for match_id, home, away, date_match, mi_h, mi_a, final_h, final_a, status in matchs_live:
                        # Parser la date du match
                        date_info = ""
                        if date_match:
                            try:
                                if 'T' in str(date_match):
                                    dt = datetime.fromisoformat(str(date_match).replace('Z', '+00:00'))
                                else:
                                    dt = datetime.strptime(str(date_match), '%Y-%m-%d %H:%M:%S')
                                jour = jours_semaine[dt.weekday()]
                                date_info = f"{jour} {dt.day}/{dt.month} {dt.hour}h{dt.minute:02d}"
                            except:
                                date_info = ""

                        # Déterminer le score à afficher
                        if final_h is not None:
                            score_display = f"{final_h} - {final_a}"
                            score_color = "#00FF00"
                            status_text = "Terminé"
                        elif status in ['LIVE', 'IN_PLAY', 'PAUSED']:
                            if mi_h is not None:
                                score_display = f"{mi_h} - {mi_a}"
                            else:
                                score_display = "0 - 0"
                            score_color = "#FF4444"
                            status_text = "🔴 LIVE"
                        elif status == 'HT' or (mi_h is not None and status not in ['SCHEDULED', 'TIMED']):
                            score_display = f"{mi_h} - {mi_a}"
                            score_color = "#FFA500"
                            status_text = "Mi-temps"
                        else:
                            score_display = "- - -"
                            score_color = "#AAAAAA"
                            status_text = date_info if date_info else "À venir"

                        st.markdown(f"""
                        <div class="ep-match-row" style="
                            display: grid;
                            grid-template-columns: 2fr 70px 2fr 80px;
                            align-items: center;
                            padding: 8px;
                            margin: 4px 0;
                            background: #002040;
                            border-radius: 5px;
                            font-size: 0.85em;
                        ">
                            <span style="color: #FFFFFF; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{home}</span>
                            <span style="color: {score_color}; font-weight: bold; text-align: center;">{score_display}</span>
                            <span style="color: #FFFFFF; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{away}</span>
                            <span class="ep-match-status" style="color: {score_color}; text-align: center; font-size: 0.75em;">{status_text}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

            # === SOUS-MENUS (TABS) ===
            if nb_matchs_journee == 0:
                # Aucun match - verifier si c'est juillet (attente nouveau calendrier)
                from datetime import datetime
                mois_actuel = datetime.now().month

                if mois_actuel == 7:
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
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    try:
                        from modules.bot_sourcing import sourcing_journee
                        nb_importes = sourcing_journee(force_reimport=False)
                        if nb_importes > 0:
                            st.rerun()
                        else:
                            st.info(f"📅 Chargement des matchs J{journee_courante} en cours...")
                            st.button("🔄 Actualiser", on_click=lambda: st.rerun())
                    except Exception as e:
                        st.warning(f"⚠️ Impossible de charger les matchs: {e}")
            else:
                # === TABS NAVIGATION ===
                from modules.database_manager import get_date_premiere_journee
                from datetime import datetime, timedelta

                # Preparer les donnees communes
                nb_matchs_avec_score = sum(1 for m in matchs_journee if m.get('score_final_home') is not None)
                match_ids = [m['id'] for m in matchs_journee]
                match_ids_str = ','.join(map(str, match_ids))

                # Definir les tabs selon l'etat (avant/apres deadline)
                if pronostics_ouverts:
                    # Avant deadline: Tab Matchs par defaut, autres grises
                    tab_matchs, tab_tendances, tab_rivaux, tab_recap = st.tabs([
                        "⚽ Matchs",
                        "📊 Tendances",
                        "👥 Rivaux",
                        "📋 Recap"
                    ])
                    default_tab = tab_matchs
                else:
                    # Apres deadline: Tab Tendances par defaut
                    tab_tendances, tab_matchs, tab_rivaux, tab_recap = st.tabs([
                        "📊 Tendances",
                        "⚽ Matchs",
                        "👥 Rivaux",
                        "📋 Recap"
                    ])
                    default_tab = tab_tendances

                # === TAB MATCHS ===
                with tab_matchs:
                    matchs_semaine = [(m['equipe_home'], m['equipe_away'], m.get('cote_home'), m.get('cote_draw'), m.get('cote_away')) for m in matchs_journee]

                    if matchs_semaine:
                        st.markdown(f"""
                        <div style="background: #001529; border: 1px solid #D4AF37; border-radius: 10px; padding: 15px; margin: 10px 0;">
                            <div style="color: #D4AF37; font-size: 0.9em; margin-bottom: 10px; text-align: center;">⚽ MATCHS J{journee_courante}</div>
                        """, unsafe_allow_html=True)

                        for home, away, cote_h, cote_n, cote_a in matchs_semaine:
                            st.markdown(f"""
                            <div style="padding: 10px; margin: 8px 0; background: #002040; border-radius: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                    <span style="color: #FFFFFF; flex: 1; text-align: left; font-weight: bold;">{home}</span>
                                    <span style="color: #D4AF37; font-size: 0.9em;">VS</span>
                                    <span style="color: #FFFFFF; flex: 1; text-align: right; font-weight: bold;">{away}</span>
                                </div>
                                <div style="display: flex; justify-content: space-around; padding-top: 6px; border-top: 1px solid #333;">
                                    <span style="color: #00FF00; font-size: 0.85em;">1: <strong>{cote_h}</strong></span>
                                    <span style="color: #AAAAAA; font-size: 0.85em;">N: <strong>{cote_n}</strong></span>
                                    <span style="color: #FF6666; font-size: 0.85em;">2: <strong>{cote_a}</strong></span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

                # === TAB TENDANCES ===
                with tab_tendances:
                    if pronostics_ouverts:
                        st.markdown("""
                        <div style="background: #002040; border: 1px solid #666; border-radius: 10px; padding: 20px; text-align: center; color: #888;">
                            <div style="font-size: 2em; margin-bottom: 10px;">🔒</div>
                            <div>Les tendances seront visibles apres la fermeture des pronostics</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Afficher les tendances
                        if synthese['nb_joueurs'] > 0:
                            jokers_html = ""
                            if synthese.get('jokers'):
                                jokers_html = '<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #444;">'
                                jokers_html += '<span style="color: #FFD700; font-size: 0.8em;">⚡ JOKERS: </span>'
                                for j in synthese['jokers']:
                                    icon = "⚡" if j['type'] == "DOUBLE" else "🃏"
                                    jokers_html += f'<span style="color: #00BFFF; font-size: 0.8em;">{icon} {j["pseudo"]} </span>'
                                jokers_html += '</div>'

                            nb_j = synthese['nb_joueurs']
                            s = 's' if nb_j > 1 else ''
                            tendances_html = f'<div style="background:linear-gradient(135deg,#002040 0%,#001529 100%);border:1px solid #D4AF37;border-radius:10px;padding:12px;margin:10px 0;">'
                            tendances_html += f'<div style="color:#D4AF37;font-size:0.85em;margin-bottom:8px;text-align:center;font-weight:bold;">📊 TENDANCES ({nb_j} joueur{s})</div>'
                            tendances_html += synthese['stats_html']
                            tendances_html += jokers_html
                            tendances_html += '</div>'
                            st.markdown(tendances_html, unsafe_allow_html=True)
                        else:
                            st.info("Aucune tendance disponible pour cette journee.")

                # === TAB RIVAUX ===
                with tab_rivaux:
                    if pronostics_ouverts:
                        st.markdown("""
                        <div style="background: #002040; border: 1px solid #666; border-radius: 10px; padding: 20px; text-align: center; color: #888;">
                            <div style="font-size: 2em; margin-bottom: 10px;">🔒</div>
                            <div>Les pronostics des rivaux seront visibles apres la fermeture</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Afficher les resultats et rivaux
                        if nb_matchs_avec_score > 0:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3c 100%); border: 2px solid #00FF00; border-radius: 15px; padding: 15px; text-align: center; margin: 10px 0;">
                                <h4 style="color: #00FF00; margin: 0;">📊 RESULTATS J{journee_courante}</h4>
                                <p style="color: #FFFFFF; margin: 5px 0 0 0; font-size: 0.9em;">{nb_matchs_avec_score}/{nb_matchs_journee} match(s) termine(s)</p>
                            </div>
                            """, unsafe_allow_html=True)

                        # Recuperer les rivaux (cache 60s)
                        rivaux_ids = get_rivaux_ids_cached(user_id)

                        if match_ids and rivaux_ids:
                            rivaux_ids_str = ','.join(map(str, rivaux_ids))
                            all_predictions = supabase._request('GET', f'predictions?match_id=in.({match_ids_str})&user_id=in.({rivaux_ids_str})&select=user_id,points_gagnes,utilisateurs(id,pseudo)') or []
                            joueurs_dict = {}
                            for p in all_predictions:
                                uid = p['user_id']
                                pseudo = p['utilisateurs']['pseudo'] if p.get('utilisateurs') else 'Inconnu'
                                if uid not in joueurs_dict:
                                    joueurs_dict[uid] = {'pseudo': pseudo, 'total': 0}
                                joueurs_dict[uid]['total'] += p.get('points_gagnes') or 0
                            joueurs_journee = [(uid, data['pseudo'], round(data['total'], 2)) for uid, data in sorted(joueurs_dict.items(), key=lambda x: x[1]['total'], reverse=True)]

                            # Bloc MES PRONOSTICS (cache 15s)
                            _my_preds = get_user_predictions_cached(user_id, saison_id, journee_courante, match_ids_str)
                            my_pronos = [p for p in _my_preds if p.get('matches')]
                            my_joker = get_user_joker_cached(user_id, journee_courante)
                            my_joker_icon = ""
                            if my_joker:
                                jt = my_joker[0].get('type_joker', '')
                                my_joker_icon = "⚡" if jt == "DOUBLE" else "🃏" if jt == "VOL" else ""

                            my_total = round(sum(p.get('points_gagnes') or 0 for p in my_pronos), 2)
                            my_color = "#00FF00" if my_total >= 0 else "#FF4444"

                            html_me = f'<div style="background:linear-gradient(135deg,#001529 0%,#002040 100%);border:2px solid #00BFFF;border-radius:10px;padding:12px;margin:10px 0;">'
                            html_me += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #00BFFF;">'
                            html_me += f'<span style="color:#00BFFF;font-weight:bold;">👤 MOI</span>'
                            html_me += f'<span style="color:{my_color};font-weight:bold;">{"+" if my_total > 0 else ""}{my_total} pts</span></div>'

                            for p in my_pronos:
                                if not p.get('matches'):
                                    continue
                                m_p = p['matches']
                                ph, pa, mise = p['score_prono_home'], p['score_prono_away'], p['mise_points']
                                mise_gc = p.get('mise_bonus_gc') or 0
                                pts = round(p.get('points_gagnes') or 0, 2)
                                sh, sa = m_p.get('score_final_home'), m_p.get('score_final_away')
                                if sh is not None:
                                    icon_me = "🎯" if (ph == sh and pa == sa) else "✅" if ((ph > pa and sh > sa) or (ph < pa and sh < sa) or (ph == pa and sh == sa)) else "❌"
                                    score_d = f"{sh}-{sa}"
                                else:
                                    icon_me, score_d = "⏳", "-"
                                pts_c = "#00FF00" if pts > 0 else "#FF4444" if pts < 0 else "#888"
                                jd = my_joker_icon
                                gc_display = f'🏆{mise_gc}' if mise_gc > 0 else '—'
                                gc_color = "#FFD700" if mise_gc > 0 else "#444"
                                html_me += f'<div style="display:flex;padding:4px 0;border-top:1px solid #333;font-size:0.8em;">'
                                html_me += f'<span style="color:#FFFFFF;flex:3;text-align:left;">{m_p["equipe_home"][:12]} - {m_p["equipe_away"][:12]}</span>'
                                cote_me = m_p.get('cote_home', 2.0) if ph > pa else m_p.get('cote_away', 2.0) if ph < pa else m_p.get('cote_draw', 3.0)
                                html_me += f'<span style="color:#4488FF;flex:1;text-align:center;">{ph}-{pa}</span>'
                                html_me += f'<span style="color:#FFA500;flex:0.8;text-align:center;">{cote_me}</span>'
                                html_me += f'<span style="color:#FFD700;flex:1;text-align:center;">{mise}</span>'
                                html_me += f'<span style="color:{gc_color};flex:0.8;text-align:center;">{gc_display}</span>'
                                html_me += f'<span style="color:#FF00FF;flex:0.5;text-align:center;">{jd}</span>'
                                html_me += f'<span style="color:#00FF00;flex:1.5;text-align:center;">{score_d} {icon_me}</span>'
                                html_me += f'<span style="color:{pts_c};flex:1;text-align:right;">{"+" if pts > 0 else ""}{pts}</span></div>'
                            html_me += '</div>'
                            st.markdown(html_me, unsafe_allow_html=True)

                            # Bloc Kingo Rivaux
                            from modules.synthese_st import get_debrief_rivaux
                            debrief_rivaux = get_debrief_rivaux(user_id, saison_id, journee_courante)
                            if debrief_rivaux:
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, #2a1a4e 0%, #1a2a4e 100%);
                                    border: 2px solid #9932CC;
                                    border-radius: 10px;
                                    padding: 12px;
                                    margin: 10px 0;
                                ">
                                    <div style="color: #9932CC; font-size: 0.85em; font-weight: bold; margin-bottom: 5px;">
                                        👑 KINGO - Tes Rivaux
                                    </div>
                                    <div style="color: #FFFFFF; font-size: 0.85em;">
                                        {debrief_rivaux['message']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                            st.markdown(f"<div style='color: #D4AF37; font-size: 0.9em; margin: 15px 0 10px 0;'>📊 PRONOSTICS DE MES RIVAUX ({len(joueurs_journee)})</div>", unsafe_allow_html=True)

                            # Recuperer jokers et pronos (cache 15s - 1 seul appel groupe)
                            all_rivaux_ids = [j[0] for j in joueurs_journee]
                            all_rivaux_str = ','.join(map(str, all_rivaux_ids)) if all_rivaux_ids else '0'

                            _rivaux_data = get_rivaux_predictions_cached(all_rivaux_str, match_ids_str, journee_courante)
                            all_jokers = _rivaux_data['jokers']
                            jokers_map = {j['utilisateur_id']: j['type_joker'] for j in all_jokers}

                            all_pronos = _rivaux_data['predictions']
                            pronos_par_joueur = {}
                            for p in all_pronos:
                                uid = p['user_id']
                                if uid not in pronos_par_joueur:
                                    pronos_par_joueur[uid] = []
                                if p.get('matches'):
                                    pronos_par_joueur[uid].append((p['matches']['equipe_home'], p['matches']['equipe_away'], p['score_prono_home'], p['score_prono_away'], p['mise_points'], p.get('mise_bonus_gc') or 0, p.get('points_gagnes'), p['matches'].get('score_final_home'), p['matches'].get('score_final_away'), p['matches'].get('cote_home', 2.0), p['matches'].get('cote_draw', 3.0), p['matches'].get('cote_away', 2.0)))

                            # Detecter les joueurs avec bonus GC actif (au moins 1 mise_bonus_gc > 0)
                            joueurs_avec_gc = set()
                            for uid, pronos_list in pronos_par_joueur.items():
                                if any(p[5] > 0 for p in pronos_list):
                                    joueurs_avec_gc.add(uid)

                            for joueur_id, pseudo, total_pts in joueurs_journee:
                                joker_type = jokers_map.get(joueur_id)
                                joker_icon = "⚡" if joker_type == "DOUBLE" else "🃏" if joker_type == "VOL" else "-"
                                pronos_joueur = pronos_par_joueur.get(joueur_id, [])
                                has_gc = joueur_id in joueurs_avec_gc

                                total_color = "#00FF00" if total_pts >= 0 else "#FF4444"
                                gc_badge = ' <span style="background:#FFD700;color:#000;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:bold;">🏆 GC</span>' if has_gc else ''
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #001529 0%, #002040 100%); border: 1px solid {'#FFD700' if has_gc else '#D4AF37'}; border-radius: 10px; padding: 12px; margin: 10px 0;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #D4AF37;">
                                        <span style="color: #D4AF37; font-weight: bold;">👤 {pseudo}{gc_badge}</span>
                                        <span style="color: {total_color}; font-weight: bold;">{'+' if total_pts > 0 else ''}{total_pts} pts</span>
                                    </div>
                                """, unsafe_allow_html=True)

                                for home, away, ph, pa, mise, mise_gc, pts_gagnes, score_h, score_a, c_h, c_n, c_a in pronos_joueur:
                                    if score_h is not None:
                                        icon = "🎯" if (ph == score_h and pa == score_a) else "✅" if ((ph > pa and score_h > score_a) or (ph < pa and score_h < score_a) or (ph == pa and score_h == score_a)) else "❌"
                                        score_display = f"{score_h}-{score_a}"
                                    else:
                                        icon, score_display = "⏳", "-"
                                    cote_r = c_h if ph > pa else c_a if ph < pa else c_n
                                    pts = round(pts_gagnes, 2) if pts_gagnes else 0
                                    pts_color = "#00FF00" if pts > 0 else "#FF4444" if pts < 0 else "#888"
                                    joker_display = joker_icon
                                    gc_display = f'🏆{mise_gc}' if mise_gc > 0 else '—'
                                    gc_color = "#FFD700" if mise_gc > 0 else "#444"
                                    st.markdown(f"""<div style="display:flex;padding:4px 0;border-top:1px solid #333;font-size:0.8em;">
                                        <span style="color:#FFFFFF;flex:3;text-align:left;">{home[:12]} - {away[:12]}</span>
                                        <span style="color:#4488FF;flex:1;text-align:center;">{ph}-{pa}</span>
                                        <span style="color:#FFA500;flex:0.8;text-align:center;">{cote_r}</span>
                                        <span style="color:#FFD700;flex:1;text-align:center;">{mise}</span>
                                        <span style="color:{gc_color};flex:0.8;text-align:center;">{gc_display}</span>
                                        <span style="color:#FF00FF;flex:0.5;text-align:center;">{joker_display}</span>
                                        <span style="color:#00FF00;flex:1.5;text-align:center;">{score_display} {icon}</span>
                                        <span style="color:{pts_color};flex:1;text-align:right;">{'+' if pts > 0 else ''}{pts}</span>
                                    </div>""", unsafe_allow_html=True)

                                st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.info("Aucun rival selectionne. Allez dans 'Mes Rivaux' pour en ajouter.")

                # === TAB RECAP ===
                with tab_recap:
                    if pronostics_ouverts:
                        st.info("🔒 Le tableau recap sera visible après la fermeture des pronostics")
                    else:
                        try:
                            import pandas as pd

                            st.subheader(f"📋 Recap J{journee_courante}")

                            # Recuperer donnees pour le tableau (cache 30s - 1 seul appel groupe)
                            match_ids_recap = [m['id'] for m in matchs_journee]
                            match_ids_recap_str = ','.join(map(str, match_ids_recap))

                            _recap = get_recap_data_cached(match_ids_recap_str, journee_courante)
                            all_preds = _recap['preds']
                            all_users = _recap['users']
                            user_map_recap = {u['id']: u['pseudo'] for u in all_users}
                            jokers_recap = _recap['jokers']
                            jokers_map_recap = {j['utilisateur_id']: j['type_joker'].lower() for j in jokers_recap}

                            from modules.classement_st import get_classement_general_complet
                            classement_recap = get_classement_general_complet()
                            rang_map = {j['user_id']: j['place'] for j in classement_recap}

                            pronos_recap = {}
                            for p in all_preds:
                                uid = p['user_id']
                                if uid not in user_map_recap:
                                    continue
                                if uid not in pronos_recap:
                                    pronos_recap[uid] = {}
                                mise = p.get('mise_points', 0) or 0
                                pronos_recap[uid][p['match_id']] = f"{p['score_prono_home']} - {p['score_prono_away']} - {mise}"

                            joueurs_recap = sorted(
                                [(uid, pseudo) for uid, pseudo in user_map_recap.items()],
                                key=lambda x: rang_map.get(x[0], 999)
                            )

                            # Abreviations personnalisees des equipes
                            TEAM_ABBR = {
                                # Ligue 1
                                'paris saint-germain fc': 'PSG', 'paris saint-germain': 'PSG', 'paris sg': 'PSG', 'paris': 'PSG',
                                'olympique de marseille': 'OM', 'marseille': 'OM',
                                'olympique lyonnais': 'OL', 'lyon': 'OL',
                                'rc lens': 'LENS', 'lens': 'LENS',
                                'fc nantes': 'FCN', 'nantes': 'FCN',
                                'losc lille': 'LILLE', 'losc': 'LILLE', 'lille': 'LILLE', 'fc lille': 'LILLE',
                                'rc strasbourg alsace': 'STRAS', 'rc strasbourg': 'STRAS', 'strasbourg': 'STRAS',
                                'as monaco fc': 'ASM', 'as monaco': 'ASM', 'monaco': 'ASM',
                                'aj auxerre': 'AUX', 'auxerre': 'AUX',
                                'stade rennais fc 1901': 'RENNE', 'stade rennais fc': 'RENNE', 'stade rennais': 'RENNE', 'rennes': 'RENNE',
                                'stade brestois 29': 'BREST', 'brest': 'BREST',
                                'toulouse fc': 'TFC', 'toulouse': 'TFC',
                                'ogc nice': 'NICE', 'nice': 'NICE',
                                'montpellier hsc': 'MHSC', 'montpellier': 'MHSC',
                                'angers sco': 'SCO', 'angers': 'SCO',
                                'as saint-etienne': 'ASSE', 'saint-etienne': 'ASSE', 'st etienne': 'ASSE',
                                'le havre ac': 'HAC', 'le havre': 'HAC',
                                'fc nantes': 'FCN', 'nantes': 'FCN',
                                'stade de reims': 'REIMS', 'reims': 'REIMS',
                                # Etranger
                                'manchester united fc': 'MU', 'manchester united': 'MU', 'man united': 'MU',
                                'manchester city fc': 'MC', 'manchester city': 'MC', 'man city': 'MC',
                                'fc barcelona': 'BARCA', 'barcelona': 'BARCA',
                                'real madrid cf': 'REAL', 'real madrid': 'REAL',
                                'fc bayern münchen': 'BAYER', 'bayern munich': 'BAYER', 'bayern münchen': 'BAYER',
                                'arsenal fc': 'ARSNL', 'arsenal': 'ARSNL',
                                'liverpool fc': 'LIVER', 'liverpool': 'LIVER',
                                'chelsea fc': 'CHELS', 'chelsea': 'CHELS',
                                'tottenham hotspur fc': 'TOTTE', 'tottenham': 'TOTTE',
                                'juventus fc': 'JUVE', 'juventus': 'JUVE',
                                'ac milan': 'MILAN', 'milan': 'MILAN',
                                'inter milan': 'INTER', 'fc internazionale milano': 'INTER',
                                'ssc napoli': 'NAPOL', 'napoli': 'NAPOL',
                                'borussia dortmund': 'BVB', 'dortmund': 'BVB',
                                'atlético de madrid': 'ATM', 'atletico madrid': 'ATM',
                            }

                            # Construire les en-tetes de matchs
                            match_headers = []
                            for m in matchs_journee:
                                h = TEAM_ABBR.get(m['equipe_home'].lower(), m['equipe_home'][:5].upper())
                                a = TEAM_ABBR.get(m['equipe_away'].lower(), m['equipe_away'][:5].upper())
                                match_headers.append((m['id'], f"{h}-{a}"))

                            # Construire le tableau HTML (scrollable sur mobile)
                            html = '<div class="ep-table-scroll">'
                            html += '<table style="width:100%;border-collapse:collapse;font-size:0.7rem;text-align:center;background:#001529;min-width:500px;">'
                            # En-tete doree
                            html += '<thead><tr style="background:linear-gradient(135deg,#D4AF37,#B8960C);color:#001529;font-weight:bold;">'
                            html += '<th style="padding:6px 4px;border:1px solid #003060;">#</th>'
                            html += '<th style="padding:6px 4px;text-align:left;border:1px solid #003060;">Pseudo</th>'
                            html += '<th style="padding:6px 4px;border:1px solid #003060;">🃏</th>'
                            for _, header in match_headers:
                                html += f'<th style="padding:6px 4px;border:1px solid #003060;">{header}</th>'
                            html += '</tr></thead>'

                            # Lignes joueurs avec alternance de couleurs
                            html += '<tbody>'
                            for idx, (uid, pseudo) in enumerate(joueurs_recap):
                                rang = rang_map.get(uid, '-')
                                if rang == 1:
                                    r = '🥇'
                                elif rang == 2:
                                    r = '🥈'
                                elif rang == 3:
                                    r = '🥉'
                                else:
                                    r = str(rang).rjust(3)

                                jt = jokers_map_recap.get(uid, '')
                                j = '⚡' if jt == 'double' else '🃏' if jt == 'vol' else '-'

                                bg = '#002040' if idx % 2 == 0 else '#001a35'
                                html += f'<tr style="background:{bg};color:#FFF;">'
                                html += f'<td style="padding:5px 4px;border:1px solid #003060;">{r}</td>'
                                html += f'<td style="padding:5px 4px;text-align:left;border:1px solid #003060;">{pseudo[:10]}</td>'
                                html += f'<td style="padding:5px 4px;border:1px solid #003060;">{j}</td>'
                                for mid, _ in match_headers:
                                    raw = pronos_recap.get(uid, {}).get(mid, None)
                                    if raw:
                                        parts = raw.split(' - ')
                                        score = f"{parts[0]}-{parts[1]}"
                                        mise = parts[2] if len(parts) > 2 else '0'
                                        html += f'<td style="padding:5px 4px;border:1px solid #003060;">{score} <span style="color:#FF4444;">({mise})</span></td>'
                                    else:
                                        html += '<td style="padding:5px 4px;border:1px solid #003060;color:#555;">-</td>'
                                html += '</tr>'
                            html += '</tbody></table></div>'

                            st.markdown(html, unsafe_allow_html=True)

                        except Exception as e:
                            st.warning(f"Erreur chargement recap: {e}")

        except Exception as e:
            st.error(f"Erreur de lecture Supabase: {e}")

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
