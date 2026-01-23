"""
Module d'inscription Streamlit pour Elite Pronos
Avec restriction J1-30 et integration emails
"""
import streamlit as st
import sqlite3
import os
from PIL import Image
import io
from datetime import datetime

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')

# Import fonctions database_manager
try:
    from modules.database_manager import (
        inscriptions_ouvertes,
        get_date_ouverture_inscriptions,
        get_countdown_j1,
        ajouter_jokers_nouvel_utilisateur
    )
    from modules.notifier_st import envoyer_email_bienvenue, envoyer_alerte_nouvel_inscrit
    HAS_MANAGER = True
except ImportError:
    HAS_MANAGER = False
    def envoyer_alerte_nouvel_inscrit(*args):
        pass


def valider_email(email):
    """Verifie que l'email contient un @"""
    return '@' in email if email else False


def valider_pseudo(pseudo):
    """Verifie que le pseudo a au moins 3 caracteres"""
    return len(pseudo) >= 3 if pseudo else False


def valider_pin(pin):
    """Verifie que le PIN a au moins 4 caracteres"""
    return len(pin) >= 4 if pin else False


def pseudo_existe(pseudo):
    """Verifie si le pseudo existe deja dans la base"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE pseudo = ?", (pseudo,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def sauvegarder_avatar(image_file, pseudo):
    """Redimensionne et sauvegarde l'avatar"""
    if image_file is not None:
        # Ouvrir l'image avec Pillow
        image = Image.open(image_file)

        # Redimensionner en 240x240
        image = image.resize((240, 240), Image.Resampling.LANCZOS)

        # Convertir en RGB si necessaire (pour PNG avec transparence)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Sauvegarder
        avatar_path = os.path.join(AVATARS_PATH, f"{pseudo}.png")
        image.save(avatar_path, 'PNG')
        return avatar_path
    return None


def enregistrer_utilisateur(prenom, pseudo, email, telephone, pin, parrain, avatar_path=None):
    """Enregistre l'utilisateur dans la base de donnees"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Verifier si c'est le premier utilisateur (sera admin)
        cursor.execute("SELECT COUNT(*) FROM utilisateurs")
        nb_users = cursor.fetchone()[0]

        # Premier utilisateur = admin automatiquement actif
        statut = 'Actif' if nb_users == 0 else 'en_attente'
        is_first_user = (nb_users == 0)

        cursor.execute('''
            INSERT INTO utilisateurs (prenom, pseudo, email, telephone, pin, statut, parrain)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (prenom, pseudo, email, telephone, pin, statut, parrain))
        conn.commit()

        # Recuperer l'ID du nouvel utilisateur
        user_id = cursor.lastrowid
        conn.close()

        # Ajouter le stock de jokers initial
        if HAS_MANAGER:
            ajouter_jokers_nouvel_utilisateur(user_id)

            # Envoyer email de bienvenue au joueur
            if email:
                user_data = {'id': user_id, 'pseudo': pseudo, 'prenom': prenom, 'email': email}
                envoyer_email_bienvenue(user_data)

            # Envoyer email alerte admin (nouvel inscrit)
            envoyer_alerte_nouvel_inscrit(pseudo, prenom, parrain, email)

        # Message adapte selon le statut
        if is_first_user:
            return True, "Inscription reussie ! Vous etes le premier utilisateur et avez ete designe ADMIN."
        return True, "Inscription reussie ! En attente de validation par un admin."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Ce pseudo est deja utilise."
    except Exception as e:
        conn.close()
        return False, f"Erreur: {str(e)}"


def afficher_formulaire_inscription():
    """Affiche le formulaire d'inscription"""

    # Message de bienvenue
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: #D4AF37; margin-bottom: 5px;">Elite Pronos</h2>
        <p style="color: #FFFFFF;">Votre plateforme de pronostics football entre amis !</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Inscription")
    st.markdown("---")

    # Verification J1-30 : inscriptions ouvertes ?
    if HAS_MANAGER and not inscriptions_ouvertes():
        date_ouverture = get_date_ouverture_inscriptions()
        countdown = get_countdown_j1()

        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #FFD700;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            margin: 20px 0;
        ">
            <h2 style="color: #FFD700; margin-top: 0;">Inscriptions fermees</h2>
            <p style="color: #cccccc;">
                Les inscriptions pour la nouvelle saison ne sont pas encore ouvertes.
            </p>
        """, unsafe_allow_html=True)

        if countdown:
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 20px 0;
            ">
                <div style="text-align: center;">
                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                        {countdown['days']}
                    </div>
                    <div style="color: #AAAAAA;">JOURS</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                        {countdown['hours']}
                    </div>
                    <div style="color: #AAAAAA;">HEURES</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">
                        {countdown['minutes']}
                    </div>
                    <div style="color: #AAAAAA;">MIN</div>
                </div>
            </div>
            <p style="color: #FFD700;">Ouverture: J1 - 30 jours</p>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Bouton retour
        if st.button("Retour a l'accueil", use_container_width=True):
            st.session_state.page = "Connexion"
            st.rerun()
        return

    # Layout en 2 colonnes
    col_avatar, col_form = st.columns([1, 2])

    # === COLONNE GAUCHE : AVATAR ===
    with col_avatar:
        st.markdown("### Avatar")

        # File uploader pour l'image
        uploaded_file = st.file_uploader(
            "Choisir une photo",
            type=['png', 'jpg', 'jpeg'],
            help="Format accepte: PNG, JPG (sera redimensionne en 240x240)"
        )

        # Afficher l'apercu de l'avatar
        if uploaded_file is not None:
            # Charger et redimensionner pour l'apercu
            image = Image.open(uploaded_file)
            image_preview = image.resize((240, 240), Image.Resampling.LANCZOS)
            st.image(image_preview, caption="Apercu de l'avatar", use_container_width=True)
            # Remettre le curseur au debut pour la sauvegarde ulterieure
            uploaded_file.seek(0)
        else:
            # Afficher un placeholder
            st.markdown(
                """
                <div style="
                    width: 100%;
                    aspect-ratio: 1;
                    background-color: #1a1a2e;
                    border: 2px dashed #D4AF37;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #666;
                    font-size: 14px;
                ">
                    Aucune image
                </div>
                """,
                unsafe_allow_html=True
            )

    # === COLONNE DROITE : FORMULAIRE ===
    with col_form:
        st.markdown("### Informations")

        # Champs du formulaire
        prenom = st.text_input("Prenom", placeholder="Votre prenom")
        pseudo = st.text_input("Pseudo *", placeholder="Minimum 3 caracteres")
        email = st.text_input("Email *", placeholder="votre@email.com")
        telephone = st.text_input("Telephone", placeholder="06 12 34 56 78")
        pin = st.text_input("Code PIN *", type="password", placeholder="Minimum 4 caracteres")
        parrain = st.text_input("Qui vous a recommande ? *", placeholder="Nom ou pseudo de votre parrain")

        st.markdown("<small>* Champs obligatoires</small>", unsafe_allow_html=True)

        # Bouton de validation
        st.markdown("---")

        if st.button("VALIDER MON INSCRIPTION", type="primary", use_container_width=True):
            # Validations
            erreurs = []

            if not valider_pseudo(pseudo):
                erreurs.append("Le pseudo doit contenir au moins 3 caracteres")

            if not valider_email(email):
                erreurs.append("L'email doit contenir un '@'")

            if not valider_pin(pin):
                erreurs.append("Le PIN doit contenir au moins 4 caracteres")

            if not parrain or len(parrain.strip()) < 2:
                erreurs.append("Veuillez indiquer qui vous a recommande")

            if pseudo_existe(pseudo):
                erreurs.append("Ce pseudo est deja pris")

            # Afficher les erreurs ou enregistrer
            if erreurs:
                for err in erreurs:
                    st.error(err)
            else:
                # Sauvegarder l'avatar si present
                avatar_path = None
                if uploaded_file is not None:
                    avatar_path = sauvegarder_avatar(uploaded_file, pseudo)

                # Enregistrer l'utilisateur
                success, message = enregistrer_utilisateur(
                    prenom, pseudo, email, telephone, pin, parrain.strip(), avatar_path
                )

                if success:
                    st.success(f"Bienvenue {pseudo}! Votre inscription est en attente de validation.")
                    st.balloons()
                else:
                    st.error(message)
