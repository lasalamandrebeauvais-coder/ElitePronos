"""
Module de Connexion Streamlit pour Elite Pronos
Avec option de recuperation de PIN et countdown J1
"""
import streamlit as st
import sqlite3
import os

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Import countdown
try:
    from modules.database_manager import get_countdown_j1, get_saison_label, get_saison_actuelle
    HAS_COUNTDOWN = True
except ImportError:
    HAS_COUNTDOWN = False


def verifier_identifiants(pseudo, pin):
    """
    Verifie les identifiants dans la base de donnees
    Retourne: (success, message, user_data)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, pseudo, prenom, email, statut
        FROM utilisateurs
        WHERE pseudo = ? AND pin = ?
    """, (pseudo, pin))

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return False, "Pseudo ou PIN incorrect.", None

    user_id, user_pseudo, prenom, email, statut = user

    if statut == 'en_attente':
        return False, "Votre compte est en attente de validation par un administrateur.", None

    if statut == 'En pause':
        return False, "Votre compte est suspendu. Contactez un administrateur.", None

    # Connexion reussie
    user_data = {
        'id': user_id,
        'pseudo': user_pseudo,
        'prenom': prenom,
        'email': email,
        'statut': statut
    }

    return True, "Connexion reussie!", user_data


def recuperer_pin_par_email(email):
    """
    Recupere le PIN associe a un email
    Retourne: (success, message, pin)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pseudo, pin, email
        FROM utilisateurs
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return False, "Aucun compte associe a cet email.", None

    pseudo, pin, user_email = user
    return True, f"Un email de recuperation a ete envoye a {user_email}", pin


def init_session():
    """Initialise les variables de session"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'show_pin_recovery' not in st.session_state:
        st.session_state.show_pin_recovery = False


def logout():
    """Deconnecte l'utilisateur"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.show_pin_recovery = False


def is_logged_in():
    """Verifie si l'utilisateur est connecte"""
    init_session()
    return st.session_state.logged_in and st.session_state.user is not None


def get_current_user():
    """Retourne les infos de l'utilisateur connecte"""
    if is_logged_in():
        return st.session_state.user
    return None


def afficher_formulaire_login():
    """Affiche le formulaire de connexion centre"""

    # Centrer le formulaire avec colonnes
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Style du container
        st.markdown("""
        <style>
        .login-box {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 30px;
            border-radius: 15px;
            border: 2px solid #D4AF37;
            max-width: 600px;
            margin: auto;
        }
        </style>
        """, unsafe_allow_html=True)

        # Message de bienvenue
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #D4AF37; margin-bottom: 5px;">Elite Pronos</h2>
            <p style="color: #FFFFFF;">Votre plateforme de pronostics football entre amis !</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("## Connexion")
        st.markdown("---")

        # === FORMULAIRE DE CONNEXION ===
        if not st.session_state.get('show_pin_recovery', False):

            with st.form("login_form"):
                pseudo = st.text_input(
                    "Pseudo",
                    placeholder="Votre pseudo",
                    help="Le pseudo choisi lors de l'inscription"
                )

                pin = st.text_input(
                    "Code PIN",
                    type="password",
                    placeholder="Votre code secret",
                    help="Minimum 4 caracteres"
                )

                st.markdown("")

                submitted = st.form_submit_button(
                    "SE CONNECTER",
                    type="primary",
                    use_container_width=True
                )

                if submitted:
                    if not pseudo or not pin:
                        st.error("Veuillez remplir tous les champs.")
                    else:
                        success, message, user_data = verifier_identifiants(pseudo, pin)

                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user = user_data
                            st.session_state.page = "Accueil"
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            # Lien PIN oublie
            st.markdown("---")
            col_a, col_b = st.columns([2, 1])
            with col_b:
                if st.button("PIN oublie ?", type="secondary"):
                    st.session_state.show_pin_recovery = True
                    st.rerun()

            # Lien vers inscription
            st.markdown("---")
            st.markdown("Pas encore inscrit?")
            if st.button("Creer un compte", use_container_width=True):
                st.session_state.page = "S'inscrire"
                st.rerun()

            # Countdown J1
            if HAS_COUNTDOWN:
                countdown = get_countdown_j1()
                if countdown and not countdown.get('passed', True):
                    st.markdown("---")
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        border: 1px solid #FFD700;
                        border-radius: 10px;
                        padding: 15px;
                        text-align: center;
                        margin-top: 10px;
                    ">
                        <div style="color: #FFD700; font-size: 0.9em; margin-bottom: 5px;">
                            SAISON {get_saison_label(get_saison_actuelle())} - COUP D'ENVOI
                        </div>
                        <div style="display: flex; justify-content: center; gap: 15px;">
                            <div>
                                <span style="font-size: 1.8em; color: #FFD700; font-weight: bold;">
                                    {countdown['days']}
                                </span>
                                <span style="color: #AAAAAA; font-size: 0.7em;">J</span>
                            </div>
                            <div>
                                <span style="font-size: 1.8em; color: #FFD700; font-weight: bold;">
                                    {countdown['hours']}
                                </span>
                                <span style="color: #AAAAAA; font-size: 0.7em;">H</span>
                            </div>
                            <div>
                                <span style="font-size: 1.8em; color: #FFD700; font-weight: bold;">
                                    {countdown['minutes']}
                                </span>
                                <span style="color: #AAAAAA; font-size: 0.7em;">M</span>
                            </div>
                        </div>
                        <div style="color: #AAAAAA; font-size: 0.8em; margin-top: 5px;">
                            {countdown.get('date_j1', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # === FORMULAIRE DE RECUPERATION DE PIN ===
        else:
            st.markdown("### Recuperation de PIN")
            st.markdown("Entrez l'email associe a votre compte")

            with st.form("recovery_form"):
                email = st.text_input(
                    "Email",
                    placeholder="votre@email.com",
                    help="L'email utilise lors de l'inscription"
                )

                st.markdown("")

                submitted = st.form_submit_button(
                    "RECUPERER MON PIN",
                    type="primary",
                    use_container_width=True
                )

                if submitted:
                    if not email or '@' not in email:
                        st.error("Veuillez entrer un email valide.")
                    else:
                        success, message, pin = recuperer_pin_par_email(email)

                        if success:
                            st.success(message)
                            # Mode test : afficher le PIN recupere
                            st.info(f"[MODE TEST] Votre PIN est : **{pin}**")
                        else:
                            st.error(message)

            # Bouton retour
            st.markdown("---")
            if st.button("Retour a la connexion", use_container_width=True):
                st.session_state.show_pin_recovery = False
                st.rerun()


def afficher_header_utilisateur():
    """Affiche le header avec info utilisateur et bouton deconnexion"""
    user = get_current_user()

    if user:
        col1, col2 = st.columns([4, 1])

        with col1:
            prenom = user.get('prenom') or user.get('pseudo')
            st.markdown(f"### Bienvenue, **{prenom}** !")

        with col2:
            if st.button("Deconnexion", type="secondary"):
                logout()
                st.rerun()

        st.markdown("---")
