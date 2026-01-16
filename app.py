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

# Initialiser la base de donnees (cree les tables si elles n'existent pas)
create_database()
init_database()

# Initialiser la session
init_session()

# Style CSS personnalise
st.markdown("""
<style>
    .stApp {
        background-color: #0a0a1a;
    }
    h1, h2, h3 {
        color: #D4AF37 !important;
    }
    .stButton>button {
        background-color: #D4AF37;
        color: #0a0a1a;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #FFD700;
        color: #0a0a1a;
    }
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
    pages = ["Accueil", "Tableau de bord", "Admin"]

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
                cursor.execute("SELECT COUNT(*) FROM matches")
                nb_matchs = cursor.fetchone()[0]
                conn.close()

                col1, col2, col3 = st.columns(3)
                col1.metric("Joueurs actifs", nb_users)
                col2.metric("Matchs en cours", nb_matchs)
                col3.metric("Saison", "2024-2025")

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

    # === PAGE ADMIN ===
    elif menu == "Admin":
        afficher_panel_admin()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("<small>Elite Pronos v1.0</small>", unsafe_allow_html=True)
