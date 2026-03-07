"""
Module d'inscription Streamlit pour Elite Pronos
Avec restriction J1-30 et integration emails
Version Supabase
"""
import streamlit as st
import os
from PIL import Image
import io
from datetime import datetime

# Import Supabase
from modules.supabase_db import get_supabase

# Chemin vers les avatars
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')

# Import fonctions database_manager
try:
    from modules.database_manager import (
        inscriptions_ouvertes,
        get_date_ouverture_inscriptions,
        get_countdown_j1,
        get_saison_actuelle
    )
    from modules.notifier_st import envoyer_alerte_nouvel_inscrit, email_confirmation_code
    HAS_MANAGER = True
except ImportError:
    HAS_MANAGER = False
    def envoyer_alerte_nouvel_inscrit(*args):
        pass
    def email_confirmation_code(*args):
        return False, "Notifier indisponible"
    def get_saison_actuelle():
        return 2025


def valider_email(email):
    """Verifie que l'email contient un @"""
    return '@' in email if email else False


def valider_pseudo(pseudo):
    """Verifie que le pseudo a au moins 3 caracteres"""
    return len(pseudo) >= 3 if pseudo else False


def valider_pin(pin):
    """
    Verifie que le PIN respecte les regles de securite :
    - Au moins 6 chiffres
    - Au moins 2 lettres
    - Au moins 1 symbole (!@#$%^&*...)
    Retourne (valide: bool, criteres: dict)
    """
    import re
    if not pin:
        return False, {
            'longueur': False,
            'chiffres': False,
            'lettres': False,
            'symbole': False
        }
    criteres = {
        'longueur': len(pin) >= 9,
        'chiffres': len(re.findall(r'\d', pin)) >= 6,
        'lettres': len(re.findall(r'[a-zA-Z]', pin)) >= 2,
        'symbole': bool(re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', pin))
    }
    return all(criteres.values()), criteres


def pseudo_existe(pseudo):
    """Verifie si le pseudo existe deja dans Supabase"""
    try:
        supabase = get_supabase()
        result = supabase._request('GET', f'utilisateurs?pseudo=eq.{pseudo}&select=id')
        return result and len(result) > 0
    except Exception as e:
        print(f"Erreur pseudo_existe: {e}")
        return False


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
    """Enregistre l'utilisateur dans Supabase"""
    try:
        supabase = get_supabase()

        # Verifier si c'est le premier utilisateur (sera admin)
        all_users = supabase._request('GET', 'utilisateurs?select=id')
        nb_users = len(all_users) if all_users else 0

        # Premier utilisateur = admin automatiquement actif
        statut = 'Actif' if nb_users == 0 else 'en_attente'
        is_first_user = (nb_users == 0)

        # Creer l'utilisateur dans Supabase
        user_data = {
            'prenom': prenom,
            'pseudo': pseudo,
            'email': email,
            'telephone': telephone,
            'pin': pin,
            'statut': statut,
            'parrain': parrain
        }

        result = supabase._request('POST', 'utilisateurs', user_data)

        if not result or len(result) == 0:
            return False, "Erreur lors de la creation du compte."

        # Recuperer l'ID du nouvel utilisateur
        user_id = result[0].get('id')

        # Ajouter le stock de jokers initial
        saison_id = get_saison_actuelle() if HAS_MANAGER else 2025
        supabase.init_stock_jokers(user_id, saison_id)

        # Envoyer alerte admin (nouvel inscrit)
        # L'email de bienvenue est envoye quand l'admin valide l'inscription
        if HAS_MANAGER:
            try:
                envoyer_alerte_nouvel_inscrit(pseudo, prenom, parrain, email)
            except Exception as e:
                print(f"Erreur envoi alerte admin: {e}")

        # Message adapte selon le statut
        if is_first_user:
            return True, "Inscription reussie ! Vous etes le premier utilisateur et avez ete designe ADMIN."
        return True, "Inscription reussie ! En attente de validation par un admin."

    except Exception as e:
        print(f"Erreur enregistrer_utilisateur: {e}")
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, "Ce pseudo est deja utilise."
        return False, f"Erreur: {str(e)}"


def afficher_formulaire_inscription():
    """Affiche le formulaire d'inscription"""

    # Si inscription reussie, afficher video plein ecran
    if st.session_state.get('inscription_reussie'):
        pseudo = st.session_state.get('inscription_pseudo', '')

        # CSS pour plein ecran
        st.markdown("""
        <style>
            .main .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }
            header, footer, .stDeployButton {
                display: none !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # Message de bienvenue
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 100%);
        ">
            <h1 style="color: #FFD700; margin: 0;">🎉 Bienvenue {pseudo} !</h1>
            <p style="color: #FFFFFF; font-size: 1.2em;">Ton inscription est en attente de validation</p>
        </div>
        """, unsafe_allow_html=True)

        # Video plein ecran
        video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'Remplacement_Voix_Thierry_Roland_Vidéo.mp4')
        if os.path.exists(video_path):
            st.video(video_path, autoplay=True)

        st.markdown("")
        if st.button("CONTINUER", type="primary", use_container_width=True):
            st.session_state.inscription_reussie = False
            st.session_state.inscription_pseudo = None
            st.rerun()
        return

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

        # --- ETAPE 2 : Saisie du code de confirmation email ---
        if st.session_state.get('inscription_attente_code'):
            st.markdown("### Verification email")
            st.info(f"Un code a 6 caracteres a ete envoye a **{st.session_state.get('inscription_email_tmp', '')}**. Saisissez-le ci-dessous.")

            # En mode test : afficher le code directement
            try:
                from modules.database_manager import is_mode_officiel
                if not is_mode_officiel():
                    st.warning(f"[MODE TEST] Code de verification : **{st.session_state.get('inscription_code_email', '')}**")
            except Exception:
                pass

            code_saisi = st.text_input("Code de verification *", placeholder="Ex: A3F7K2", max_chars=6)

            col_val, col_annuler = st.columns([2, 1])
            with col_val:
                if st.button("CONFIRMER LE CODE", type="primary", use_container_width=True):
                    code_attendu = st.session_state.get('inscription_code_email', '')
                    import time
                    code_expire = (time.time() - st.session_state.get('inscription_code_ts', 0)) > 600

                    if code_expire:
                        st.error("Le code a expire (10 minutes). Recommencez l'inscription.")
                        st.session_state.inscription_attente_code = False
                    elif not code_saisi or code_saisi.upper() != code_attendu:
                        st.error("Code incorrect. Verifiez votre email et reessayez.")
                    else:
                        # Code correct → creer le compte
                        avatar_path = None
                        if st.session_state.get('inscription_avatar_tmp') is not None:
                            avatar_path = sauvegarder_avatar(
                                st.session_state.inscription_avatar_tmp,
                                st.session_state.inscription_pseudo_tmp
                            )

                        success, message = enregistrer_utilisateur(
                            st.session_state.inscription_prenom_tmp,
                            st.session_state.inscription_pseudo_tmp,
                            st.session_state.inscription_email_tmp,
                            st.session_state.inscription_telephone_tmp,
                            st.session_state.inscription_pin_tmp,
                            st.session_state.inscription_parrain_tmp,
                            avatar_path
                        )

                        # Nettoyer session
                        for k in ['inscription_attente_code', 'inscription_code_email',
                                  'inscription_code_ts', 'inscription_prenom_tmp',
                                  'inscription_pseudo_tmp', 'inscription_email_tmp',
                                  'inscription_telephone_tmp', 'inscription_pin_tmp',
                                  'inscription_parrain_tmp', 'inscription_avatar_tmp']:
                            st.session_state.pop(k, None)

                        if success:
                            st.session_state.inscription_reussie = True
                            st.session_state.inscription_pseudo = st.session_state.get('inscription_pseudo_tmp', '')
                            st.rerun()
                        else:
                            st.error(message)

            with col_annuler:
                if st.button("Annuler", use_container_width=True):
                    for k in ['inscription_attente_code', 'inscription_code_email',
                              'inscription_code_ts', 'inscription_prenom_tmp',
                              'inscription_pseudo_tmp', 'inscription_email_tmp',
                              'inscription_telephone_tmp', 'inscription_pin_tmp',
                              'inscription_parrain_tmp', 'inscription_avatar_tmp']:
                        st.session_state.pop(k, None)
                    st.rerun()
            return

        # --- ETAPE 1 : Formulaire principal ---
        st.markdown("### Informations")

        # Champs du formulaire
        prenom = st.text_input("Prenom", placeholder="Votre prenom")
        pseudo = st.text_input("Pseudo *", placeholder="Minimum 3 caracteres")
        email = st.text_input("Email *", placeholder="votre@email.com")
        telephone = st.text_input("Telephone", placeholder="06 12 34 56 78")
        pin = st.text_input("Code PIN *", type="password", placeholder="Min 9 car. : 6 chiffres, 2 lettres, 1 symbole")
        parrain = st.text_input("Qui vous a recommande ? *", placeholder="Nom ou pseudo de votre parrain")

        # Affichage criteres PIN en temps reel
        if pin:
            _, criteres = valider_pin(pin)
            labels = {
                'longueur': 'Longueur >= 9 caracteres',
                'chiffres': 'Au moins 6 chiffres',
                'lettres': 'Au moins 2 lettres',
                'symbole': 'Au moins 1 symbole (!@#$%...)'
            }
            criteres_html = ''.join(
                f'<div style="color: {"#4CAF50" if ok else "#FF5252"}; font-size: 0.85em;">'
                f'{"✓" if ok else "✗"} {labels[k]}</div>'
                for k, ok in criteres.items()
            )
            st.markdown(
                f'<div style="background:#0a0a1a; border-radius:8px; padding:10px; margin-bottom:8px;">'
                f'{criteres_html}</div>',
                unsafe_allow_html=True
            )

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

            pin_ok, _ = valider_pin(pin)
            if not pin_ok:
                erreurs.append("Le PIN ne respecte pas les regles : 9 caracteres min., 6 chiffres, 2 lettres, 1 symbole")

            if not parrain or len(parrain.strip()) < 2:
                erreurs.append("Veuillez indiquer qui vous a recommande")

            if pseudo_existe(pseudo):
                erreurs.append("Ce pseudo est deja pris")

            # Afficher les erreurs ou envoyer le code
            if erreurs:
                for err in erreurs:
                    st.error(err)
            else:
                # Generer un code a 6 caracteres alphanumeriques
                import random
                import string
                import time
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

                # Envoyer l'email de verification
                ok, msg_email = email_confirmation_code(email, pseudo, code)

                if not ok:
                    st.error(f"Impossible d'envoyer l'email de verification : {msg_email}")
                else:
                    # Stocker en session pour l'etape 2
                    st.session_state.inscription_attente_code = True
                    st.session_state.inscription_code_email = code
                    st.session_state.inscription_code_ts = time.time()
                    st.session_state.inscription_prenom_tmp = prenom
                    st.session_state.inscription_pseudo_tmp = pseudo
                    st.session_state.inscription_email_tmp = email
                    st.session_state.inscription_telephone_tmp = telephone
                    st.session_state.inscription_pin_tmp = pin
                    st.session_state.inscription_parrain_tmp = parrain.strip()
                    st.session_state.inscription_avatar_tmp = uploaded_file
                    st.rerun()
