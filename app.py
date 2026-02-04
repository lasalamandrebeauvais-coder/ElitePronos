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

    # Liste des pages pour utilisateur connecte (Admin visible uniquement pour les admins)
    is_admin = user.get('is_admin', False) or user.get('pseudo', '').lower() == 'baggio'
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
            from modules.database_manager import get_saison_actuelle, get_saison_label, get_journee_courante, get_countdown_pronostics_journee

            supabase = get_supabase()
            saison_id = get_saison_actuelle()
            saison_label = get_saison_label(saison_id)
            journee_courante = get_journee_courante(saison_id)

            # Recuperer le countdown pour les pronostics
            countdown = get_countdown_pronostics_journee(journee_courante, saison_id)

            # Compter uniquement les matchs de la journee courante (Supabase)
            matchs_journee = supabase.get_matches_journee(saison_id, journee_courante)
            nb_matchs_journee = len(matchs_journee)

            # === SYNTHESE KINGO (en haut) ===
            from modules.synthese_st import get_synthese_accueil

            # Generer la synthese dynamique
            synthese = get_synthese_accueil(saison_id, journee_courante)
            message_kingo = synthese['commentaire']

            # Afficher Kingo avec mascotte (message a gauche, Kingo a droite plus grand)
            kingo_col1, kingo_col2 = st.columns([4, 1])
            with kingo_col1:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        border: 2px solid #D4AF37;
                        border-radius: 10px;
                        padding: 15px;
                    ">
                        <div style="color: #D4AF37; font-size: 1em; font-weight: bold; margin-bottom: 3px;">
                            👑 KINGO - Synthese J{journee_courante}
                        </div>
                        <div style="color: #AAAAAA; font-size: 0.75em; font-style: italic; margin-bottom: 8px;">
                            Le roi des pronostics, celui que tout le monde veut detroner
                        </div>
                        <div style="color: #FFFFFF; font-size: 0.9em;">{message_kingo}</div>
                    </div>
                    """, unsafe_allow_html=True)

            with kingo_col2:
                kingo_path = os.path.join(os.path.dirname(__file__), 'assets', 'kingo accueil.png')
                if os.path.exists(kingo_path):
                    from PIL import Image
                    kingo_img = Image.open(kingo_path)
                    st.image(kingo_img, width=120)

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
                        <div style="display: flex; justify-content: center; gap: 15px;">
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
                # PRONOSTICS OUVERTS: Afficher les pronostics du joueur (Supabase)
                predictions_data = supabase._request('GET',
                    f'predictions?user_id=eq.{user_id}&select=match_id,score_prono_home,score_prono_away,mise_points,matches(id,equipe_home,equipe_away,semaine_id,saison_id)&matches.saison_id=eq.{saison_id}&matches.semaine_id=eq.{journee_courante}'
                ) or []
                mes_pronos_accueil = [(p['matches']['id'], p['matches']['equipe_home'], p['matches']['equipe_away'], p['score_prono_home'], p['score_prono_away'], p['mise_points']) for p in predictions_data if p.get('matches') and p['matches'].get('semaine_id') == journee_courante]

                if mes_pronos_accueil:
                    st.markdown(f"""<div style="background: linear-gradient(135deg, #001529 0%, #002040 100%); border: 1px solid #4488FF; border-radius: 10px; padding: 12px; margin: 10px 0;">
                        <div style="color: #4488FF; font-size: 0.85em; margin-bottom: 8px; text-align: center; font-weight: bold;">⚽ MES PRONOSTICS DE LA JOURNÉE</div>
                    """, unsafe_allow_html=True)

                    for match_id, home, away, score_h, score_a, mise in mes_pronos_accueil:
                        st.markdown(f"""<div style="display: grid; grid-template-columns: 2fr 50px 2fr 45px; align-items: center; padding: 6px 8px; margin: 3px 0; background: #002040; border-radius: 5px; font-size: 0.8em;">
                            <span style="color: #FFFFFF; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{home}</span>
                            <span style="color: #4488FF; font-weight: bold; text-align: center;">{score_h}-{score_a}</span>
                            <span style="color: #FFFFFF; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{away}</span>
                            <span style="color: #00FF00; font-weight: bold; text-align: center;">{mise}pt</span>
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
                        <div style="
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
                            <span style="color: {score_color}; text-align: center; font-size: 0.75em;">{status_text}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

            # === BLOC 3: SYNTHESE TENDANCES (% votes, jokers, grosses mises) ===
            # Afficher seulement apres la deadline
            if synthese['nb_joueurs'] > 0 and not pronostics_ouverts:
                # Section jokers
                jokers_html = ""
                if synthese.get('jokers'):
                    jokers_html = '<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #444;">'
                    jokers_html += '<span style="color: #FFD700; font-size: 0.8em;">⚡ JOKERS: </span>'
                    for j in synthese['jokers']:
                        icon = "⚡" if j['type'] == "DOUBLE" else "🎯"
                        jokers_html += f'<span style="color: #00BFFF; font-size: 0.8em;">{icon} {j["pseudo"]} </span>'
                    jokers_html += '</div>'

                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #002040 0%, #001529 100%);
                    border: 1px solid #D4AF37;
                    border-radius: 10px;
                    padding: 12px;
                    margin: 10px 0;
                ">
                    <div style="color: #D4AF37; font-size: 0.85em; margin-bottom: 8px; text-align: center; font-weight: bold;">
                        📊 TENDANCES ({synthese['nb_joueurs']} joueur{'s' if synthese['nb_joueurs'] > 1 else ''})
                    </div>
                    {synthese['stats_html']}
                    {jokers_html}
                </div>
                """, unsafe_allow_html=True)

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
                # === TUNNEL DE TRANSITION TEMPOREL ===
                from modules.database_manager import get_date_premiere_journee
                from datetime import datetime, timedelta

                date_journee = get_date_premiere_journee(journee_courante, saison_id)

                # Verifier si des scores sont disponibles pour cette journee (Supabase)
                nb_matchs_avec_score = sum(1 for m in matchs_journee if m.get('score_final_home') is not None)

                now = datetime.now()
                date_fermeture = date_journee - timedelta(hours=1) if date_journee else now

                # Determiner l'etat du tunnel
                if countdown and not countdown.get('expired', False):
                    # Si l'utilisateur n'a pas encore fait ses pronostics, afficher les matchs
                    if not mes_pronos_accueil:
                        # === MATCHS DE LA SEMAINE AVEC COTES (Supabase) ===
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

                elif nb_matchs_avec_score > 0:
                    # ETAT 4: Des scores sont disponibles
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3c 100%); border: 2px solid #00FF00; border-radius: 15px; padding: 20px; text-align: center; margin: 20px 0;">
                        <h4 style="color: #00FF00; margin: 0;">📊 RESULTATS J{journee_courante}</h4>
                        <p style="color: #FFFFFF; margin: 10px 0 0 0;">{nb_matchs_avec_score}/{nb_matchs_journee} match(s) termine(s)</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Recuperer les rivaux du joueur connecte (Supabase)
                    rivaux_ids = supabase.get_rivaux_ids(user_id)

                    # Recuperer les predictions des rivaux uniquement
                    match_ids = [m['id'] for m in matchs_journee]
                    if match_ids and rivaux_ids:
                        match_ids_str = ','.join(map(str, match_ids))
                        rivaux_ids_str = ','.join(map(str, rivaux_ids))
                        all_predictions = supabase._request('GET', f'predictions?match_id=in.({match_ids_str})&user_id=in.({rivaux_ids_str})&select=user_id,points_gagnes,utilisateurs(id,pseudo)') or []
                        joueurs_dict = {}
                        for p in all_predictions:
                            uid = p['user_id']
                            pseudo = p['utilisateurs']['pseudo'] if p.get('utilisateurs') else 'Inconnu'
                            if uid not in joueurs_dict:
                                joueurs_dict[uid] = {'pseudo': pseudo, 'total': 0}
                            joueurs_dict[uid]['total'] += p.get('points_gagnes') or 0
                        joueurs_journee = [(uid, data['pseudo'], data['total']) for uid, data in sorted(joueurs_dict.items(), key=lambda x: x[1]['total'], reverse=True)]

                        # === BLOC KINGO RIVAUX ===
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
                    elif match_ids:
                        # Pas de rivaux selectionnes - message d'info
                        st.info("Aucun rival selectionne. Allez dans 'Mes Rivaux' pour en ajouter et voir leurs pronostics ici.")
                        joueurs_journee = []
                    else:
                        joueurs_journee = []

                    # Batch: recuperer TOUS les jokers et pronos des rivaux en 2 appels (au lieu de N*2)
                    all_rivaux_ids = [j[0] for j in joueurs_journee]
                    all_rivaux_str = ','.join(map(str, all_rivaux_ids))

                    # 1 seul appel pour tous les jokers
                    all_jokers = supabase._request('GET', f'jokers_historique?utilisateur_id=in.({all_rivaux_str})&semaine_id=eq.{journee_courante}&select=utilisateur_id,type_joker') or []
                    jokers_map = {j['utilisateur_id']: j['type_joker'] for j in all_jokers}

                    # 1 seul appel pour tous les pronos
                    all_pronos = supabase._request('GET', f'predictions?user_id=in.({all_rivaux_str})&match_id=in.({match_ids_str})&select=user_id,score_prono_home,score_prono_away,mise_points,points_gagnes,matches(equipe_home,equipe_away,score_final_home,score_final_away,date_match)') or []
                    pronos_par_joueur = {}
                    for p in all_pronos:
                        uid = p['user_id']
                        if uid not in pronos_par_joueur:
                            pronos_par_joueur[uid] = []
                        if p.get('matches'):
                            pronos_par_joueur[uid].append((p['matches']['equipe_home'], p['matches']['equipe_away'], p['score_prono_home'], p['score_prono_away'], p['mise_points'], p.get('points_gagnes'), p['matches'].get('score_final_home'), p['matches'].get('score_final_away')))

                    for joueur_id, pseudo, total_pts in joueurs_journee:
                        joker_type = jokers_map.get(joueur_id)
                        joker_icon = "⚡" if joker_type == "DOUBLE" else "🎯" if joker_type == "VOL" else "-"
                        pronos_joueur = pronos_par_joueur.get(joueur_id, [])

                        total_color = "#00FF00" if total_pts >= 0 else "#FF4444"
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #001529 0%, #002040 100%); border: 1px solid #D4AF37; border-radius: 10px; padding: 12px; margin: 10px 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #D4AF37;">
                                <span style="color: #D4AF37; font-weight: bold;">👤 {pseudo}</span>
                                <span style="color: {total_color}; font-weight: bold;">{'+' if total_pts > 0 else ''}{total_pts} pts</span>
                            </div>
                        """, unsafe_allow_html=True)

                        first_row = True
                        for home, away, ph, pa, mise, pts_gagnes, score_h, score_a in pronos_joueur:
                            if score_h is not None:
                                icon = "🎯" if (ph == score_h and pa == score_a) else "✅" if ((ph > pa and score_h > score_a) or (ph < pa and score_h < score_a) or (ph == pa and score_h == score_a)) else "❌"
                                score_display = f"{score_h}-{score_a}"
                            else:
                                icon, score_display = "⏳", "-"
                            pts = pts_gagnes if pts_gagnes else 0
                            pts_color = "#00FF00" if pts > 0 else "#FF4444" if pts < 0 else "#888"
                            joker_display = joker_icon if first_row else ""
                            first_row = False
                            st.markdown(f"""<div style="display: flex; justify-content: space-between; padding: 4px 0; border-top: 1px solid #333; font-size: 0.8em;">
                                <span style="color: #FFFFFF;">{home[:12]} - {away[:12]}</span>
                                <span style="color: #4488FF;">{ph}-{pa}</span>
                                <span style="color: #FFD700;">{mise}</span>
                                <span style="color: #FF00FF;">{joker_display}</span>
                                <span style="color: #00FF00;">{score_display} {icon}</span>
                                <span style="color: {pts_color};">{'+' if pts > 0 else ''}{pts}</span>
                            </div>""", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

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
