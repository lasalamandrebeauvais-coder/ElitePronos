"""
Module de Connexion Streamlit pour Elite Pronos
Avec option de recuperation de PIN et countdown J1
"""
import streamlit as st
import os

# Import Supabase
from modules.supabase_db import get_supabase

# Import countdown
try:
    from modules.database_manager import get_countdown_j1, get_saison_label, get_saison_actuelle
    HAS_COUNTDOWN = True
except ImportError:
    HAS_COUNTDOWN = False


def verifier_identifiants(pseudo, pin):
    """
    Verifie les identifiants dans Supabase
    Retourne: (success, message, user_data)
    """
    try:
        client = get_supabase()

        # Chercher l'utilisateur avec ce pseudo et pin
        user = client._request('GET',
            f'utilisateurs?pseudo=eq.{pseudo}&pin=eq.{pin}&select=id,pseudo,prenom,email,statut,is_admin,reglement_accepte'
        )

        if not user or len(user) == 0:
            return False, "Pseudo ou PIN incorrect.", None

        user = user[0]
        statut = user.get('statut', '')

        if statut == 'en_attente':
            return False, "Votre compte est en attente de validation par un administrateur.", None

        if statut == 'En pause':
            return False, "Votre compte est suspendu. Contactez un administrateur.", None

        # Connexion reussie
        user_data = {
            'id': user.get('id'),
            'pseudo': user.get('pseudo'),
            'prenom': user.get('prenom'),
            'email': user.get('email'),
            'statut': statut,
            'is_admin': bool(user.get('is_admin', False)),
            'reglement_accepte': bool(user.get('reglement_accepte', False))
        }

        return True, "Connexion reussie!", user_data

    except Exception as e:
        print(f"Erreur login Supabase: {e}")
        return False, "Erreur de connexion au serveur.", None


def recuperer_pin_par_email(email):
    """
    Recupere le PIN associe a un email depuis Supabase
    Retourne: (success, message, pin)
    """
    try:
        client = get_supabase()

        user = client._request('GET',
            f'utilisateurs?email=eq.{email}&select=pseudo,pin,email'
        )

        if not user or len(user) == 0:
            return False, "Aucun compte associe a cet email.", None

        user = user[0]
        pseudo, pin, user_email = user.get('pseudo'), user.get('pin'), user.get('email')

        return True, f"Un email de recuperation a ete envoye a {user_email}", pin

    except Exception as e:
        print(f"Erreur recuperation PIN Supabase: {e}")
        return False, "Erreur de connexion au serveur.", None


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
                        from modules.supabase_db import get_supabase
                        from datetime import datetime, timezone, timedelta

                        client = get_supabase()
                        MAX_ATTEMPTS = 5
                        WINDOW_MINUTES = 30

                        nb_tentatives = client.count_recent_attempts(pseudo, WINDOW_MINUTES)

                        if nb_tentatives >= MAX_ATTEMPTS:
                            # Calculer le temps restant avant deblocage
                            since = (datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)).isoformat()
                            attempts_data = client._request('GET',
                                f'login_attempts?pseudo=eq.{pseudo}&tentative_at=gte.{since}&select=tentative_at&order=tentative_at.asc&limit=1'
                            )
                            if attempts_data:
                                from datetime import datetime as dt
                                premiere = dt.fromisoformat(attempts_data[0]['tentative_at'].replace('Z', '+00:00'))
                                deblocage = premiere + timedelta(minutes=WINDOW_MINUTES)
                                restant = int((deblocage - datetime.now(timezone.utc)).total_seconds() / 60) + 1
                                st.error(
                                    f"Compte temporairement bloque apres {MAX_ATTEMPTS} tentatives echouees. "
                                    f"Reessayez dans {restant} minute(s)."
                                )
                            else:
                                st.error(f"Compte temporairement bloque. Reessayez dans {WINDOW_MINUTES} minutes.")
                        else:
                            success, message, user_data = verifier_identifiants(pseudo, pin)

                            if success:
                                client.clear_attempts(pseudo)
                                client.update_derniere_connexion(user_data['id'])
                                st.session_state.logged_in = True
                                st.session_state.user = user_data
                                st.session_state.page = "Accueil"
                                st.success(message)
                                st.rerun()
                            else:
                                client.log_login_attempt(pseudo)
                                restantes = MAX_ATTEMPTS - nb_tentatives - 1
                                if restantes > 0:
                                    st.error(f"{message} ({restantes} tentative(s) restante(s) avant blocage)")
                                else:
                                    st.error(f"{message} Compte bloque pendant {WINDOW_MINUTES} minutes.")

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
