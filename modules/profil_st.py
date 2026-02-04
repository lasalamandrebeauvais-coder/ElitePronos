"""
Module Profil pour Elite Pronos
Affichage et modification des informations utilisateur
"""
import streamlit as st
import os
from datetime import datetime
from PIL import Image

from modules.supabase_db import get_supabase

ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
AVATARS_PATH = os.path.join(ASSETS_PATH, 'avatars')

# Liste des equipes Ligue 1
EQUIPES_L1 = [
    "",
    "AJ Auxerre",
    "Angers SCO",
    "AS Monaco",
    "AS Saint-Etienne",
    "FC Nantes",
    "Havre AC",
    "LOSC Lille",
    "Montpellier HSC",
    "OGC Nice",
    "Olympique de Marseille",
    "Olympique Lyonnais",
    "Paris Saint-Germain",
    "Racing Club de Lens",
    "Stade Brestois 29",
    "Stade de Reims",
    "Stade Rennais FC",
    "RC Strasbourg",
    "Toulouse FC"
]


def get_user_profile(user_id):
    """Recupere le profil complet de l'utilisateur"""
    supabase = get_supabase()
    result = supabase._request('GET',
        f'utilisateurs?id=eq.{user_id}&select=*'
    )
    return result[0] if result else None


def update_user_profile(user_id, data):
    """Met a jour le profil utilisateur"""
    supabase = get_supabase()
    try:
        supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', data)
        return True
    except Exception as e:
        print(f"Erreur update_user_profile: {e}")
        return False


def afficher_profil(user):
    """Affiche la page profil"""

    # Header avec bouton retour
    col_back, col_home, col_title, col_mascot = st.columns([0.5, 0.5, 3, 1])
    with col_back:
        if st.button("◀", help="Retour", use_container_width=True):
            st.session_state.dashboard_section = None
            st.rerun()
    with col_home:
        if st.button("🏠", help="Accueil", use_container_width=True):
            st.session_state.dashboard_section = None
            st.session_state.page = "Accueil"
            st.rerun()
    with col_title:
        st.markdown("## Mon Profil")
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo profil.png")
        if os.path.exists(mascot_path):
            st.image(mascot_path, width=80)

    st.markdown("---")

    # Recuperer le profil complet
    profil = get_user_profile(user['id'])
    if not profil:
        st.error("Impossible de charger le profil")
        return

    # === SECTION AVATAR ET INFOS PRINCIPALES ===
    col_avatar, col_info = st.columns([1, 3])

    with col_avatar:
        avatar_path = os.path.join(AVATARS_PATH, f"{profil['pseudo']}.png")
        if os.path.exists(avatar_path):
            avatar_img = Image.open(avatar_path)
            st.image(avatar_img, width=120)
        else:
            st.markdown(f"""
            <div style="
                width: 120px;
                height: 120px;
                background: linear-gradient(135deg, #FFD700, #FFA500);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 3em;
                color: #0a0a1a;
                font-weight: bold;
            ">{profil['pseudo'][0].upper()}</div>
            """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"### {profil.get('prenom') or profil['pseudo']}")
        st.markdown(f"**@{profil['pseudo']}**")

        # Date d'inscription
        created_at = profil.get('created_at')
        if created_at:
            try:
                date_inscription = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                st.caption(f"Membre depuis le {date_inscription.strftime('%d/%m/%Y')}")
            except:
                pass

    st.markdown("---")

    # === INFORMATIONS D'INSCRIPTION ===
    st.markdown("### Informations d'inscription")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Prenom:** {profil.get('prenom') or '-'}")
        st.markdown(f"**Pseudo:** {profil.get('pseudo')}")
        st.markdown(f"**Email:** {profil.get('email') or '-'}")

    with col2:
        st.markdown(f"**Telephone:** {profil.get('telephone') or '-'}")
        st.markdown(f"**Parrain:** {profil.get('parrain') or '-'}")
        st.markdown(f"**Statut:** {profil.get('statut')}")

    st.markdown("---")

    # === INFORMATIONS PERSONNELLES (modifiables) ===
    st.markdown("### Informations personnelles")

    with st.form("form_profil"):
        col_a, col_b = st.columns(2)

        with col_a:
            # Date d'anniversaire
            date_anniversaire = profil.get('date_anniversaire')
            if date_anniversaire:
                try:
                    date_val = datetime.strptime(date_anniversaire, '%Y-%m-%d').date()
                except:
                    date_val = None
            else:
                date_val = None

            new_date = st.date_input(
                "Date d'anniversaire",
                value=date_val,
                min_value=datetime(1950, 1, 1).date(),
                max_value=datetime.now().date(),
                format="DD/MM/YYYY"
            )

        with col_b:
            # Equipe preferee
            equipe_actuelle = profil.get('equipe_preferee') or ""
            try:
                equipe_index = EQUIPES_L1.index(equipe_actuelle)
            except ValueError:
                equipe_index = 0

            new_equipe = st.selectbox(
                "Equipe preferee",
                options=EQUIPES_L1,
                index=equipe_index
            )

        submitted = st.form_submit_button("Enregistrer", type="primary", use_container_width=True)

        if submitted:
            update_data = {}

            if new_date:
                update_data['date_anniversaire'] = new_date.strftime('%Y-%m-%d')

            if new_equipe:
                update_data['equipe_preferee'] = new_equipe

            if update_data:
                if update_user_profile(user['id'], update_data):
                    st.success("Profil mis a jour !")
                    st.rerun()
                else:
                    st.error("Erreur lors de la mise a jour")

    # === STATISTIQUES ===
    st.markdown("---")
    st.markdown("### Mes statistiques")

    # Recuperer quelques stats
    supabase = get_supabase()
    from modules.database_manager import get_saison_actuelle
    saison_id = get_saison_actuelle()

    predictions = supabase._request('GET',
        f'predictions?user_id=eq.{user["id"]}&saison_id=eq.{saison_id}&select=points_gagnes,is_score_exact'
    ) or []

    total_points = sum(p.get('points_gagnes', 0) or 0 for p in predictions)
    scores_exacts = sum(1 for p in predictions if p.get('is_score_exact'))
    nb_pronos = len(predictions)

    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        st.metric("Total Points", f"{total_points:.0f}")

    with col_s2:
        st.metric("Scores Exacts", scores_exacts)

    with col_s3:
        st.metric("Pronostics", nb_pronos)
