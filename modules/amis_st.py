"""
Module Amis/Rivaux Streamlit pour Elite Pronos
Gestion des relations entre joueurs - Version Supabase avec checkboxes
"""
import streamlit as st
import os
from datetime import datetime

# Import Supabase
from modules.supabase_db import get_supabase
from modules.database_manager import get_saison_actuelle, get_journee_courante

# Chemin avatars
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')


def get_avatar_path(pseudo):
    """Retourne le chemin de l'avatar du joueur"""
    avatar_file = os.path.join(AVATARS_PATH, f"{pseudo}.png")
    if os.path.exists(avatar_file):
        return avatar_file
    return None


def afficher_amis(user):
    """Affiche le module de gestion des amis/rivaux avec checkboxes"""

    # Header avec bouton retour
    col_back, col_title = st.columns([0.6, 5])
    with col_back:
        if st.button("◀", help="Retour", use_container_width=True):
            st.session_state.dashboard_section = None
            st.rerun()

    with col_title:
        st.markdown("## Mes Rivaux")

    st.markdown("---")

    current_user_id = user['id']
    supabase = get_supabase()
    saison_id = get_saison_actuelle()

    # Recuperer tous les joueurs avec stats
    tous_joueurs = supabase.get_joueurs_avec_stats(current_user_id, saison_id)
    rivaux_ids = supabase.get_rivaux_ids(current_user_id)

    # === SELECTION AVEC CHECKBOXES VERTS ===
    st.markdown("### Selectionner mes rivaux")
    st.markdown('<p style="color: #AAAAAA; font-size: 0.85em;">Cochez les joueurs que vous souhaitez suivre</p>', unsafe_allow_html=True)

    # Style pour les checkboxes verts
    st.markdown("""
    <style>
        .rival-row {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            margin: 3px 0;
            background: linear-gradient(135deg, #001529 0%, #002040 100%);
            border-radius: 8px;
            border-left: 3px solid #333;
        }
        .rival-row.selected {
            border-left: 3px solid #00FF00;
            background: linear-gradient(135deg, #002520 0%, #003530 100%);
        }
        .rival-rang {
            width: 35px;
            font-weight: bold;
            text-align: center;
        }
        .rival-pseudo {
            flex: 1;
            color: #FFFFFF;
            font-weight: bold;
        }
        .rival-points {
            color: #D4AF37;
            font-size: 0.9em;
            margin-right: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialiser les selections dans session_state
    if 'rivaux_selection' not in st.session_state:
        st.session_state.rivaux_selection = {rid: True for rid in rivaux_ids}

    # Liste des joueurs avec checkboxes
    selections_modifiees = {}

    for joueur in tous_joueurs:
        jid = joueur['id']
        is_selected = jid in rivaux_ids

        # Couleur du rang
        if joueur['rang'] == 1:
            rang_color = "#FFD700"
        elif joueur['rang'] == 2:
            rang_color = "#C0C0C0"
        elif joueur['rang'] == 3:
            rang_color = "#CD7F32"
        else:
            rang_color = "#FFFFFF"

        # Creer une ligne avec checkbox
        col_check, col_rang, col_pseudo, col_pts = st.columns([0.5, 0.5, 3, 1.5])

        with col_check:
            # Checkbox vert si selectionne
            checkbox_label = "🟢" if is_selected else "⚪"
            new_value = st.checkbox(
                checkbox_label,
                value=is_selected,
                key=f"rival_{jid}",
                label_visibility="collapsed"
            )
            selections_modifiees[jid] = new_value

        with col_rang:
            st.markdown(f'<span style="color: {rang_color}; font-weight: bold;">#{joueur["rang"]}</span>', unsafe_allow_html=True)

        with col_pseudo:
            st.markdown(f'<span style="color: #FFFFFF;">{joueur["pseudo"]}</span>', unsafe_allow_html=True)

        with col_pts:
            pts_color = "#00FF00" if joueur['points'] >= 0 else "#FF4444"
            st.markdown(f'<span style="color: {pts_color}; font-weight: bold;">{joueur["points"]} pts</span>', unsafe_allow_html=True)

    # Bouton de validation
    st.markdown("---")
    if st.button("VALIDER MES RIVAUX", type="primary", use_container_width=True):
        # Appliquer les changements
        for jid, is_now_selected in selections_modifiees.items():
            was_selected = jid in rivaux_ids

            if is_now_selected and not was_selected:
                # Ajouter le rival
                supabase.ajouter_rival(current_user_id, jid)
            elif not is_now_selected and was_selected:
                # Supprimer le rival
                supabase.supprimer_rival(current_user_id, jid)

        st.success("Rivaux mis a jour!")
        st.rerun()

    st.markdown("---")

    # === AFFICHAGE DES RIVAUX SELECTIONNES ===
    st.markdown("### Mes rivaux suivis")

    # Rafraichir la liste des rivaux
    rivaux_ids = supabase.get_rivaux_ids(current_user_id)
    rivaux_affiches = [j for j in tous_joueurs if j['id'] in rivaux_ids]

    if not rivaux_affiches:
        st.info("Aucun rival selectionne. Cochez les joueurs ci-dessus pour les suivre.")
    else:
        # Trier par rang
        rivaux_affiches.sort(key=lambda x: x['rang'])

        # Header du tableau
        st.markdown("""
        <div style="
            display: flex;
            justify-content: space-between;
            padding: 10px 15px;
            background: #D4AF37;
            border-radius: 10px 10px 0 0;
            font-weight: bold;
            color: #001529;
            font-size: 0.85em;
        ">
            <span style="width: 40px; text-align: center;">#</span>
            <span style="flex: 2;">Pseudo</span>
            <span style="flex: 1; text-align: center;">Points</span>
            <span style="flex: 1; text-align: center;">Bons Pronos</span>
            <span style="flex: 1; text-align: center;">Exacts</span>
        </div>
        """, unsafe_allow_html=True)

        # Lignes du tableau
        for rival in rivaux_affiches:
            # Couleur selon le rang
            if rival['rang'] == 1:
                rang_color = "#FFD700"
                rang_icon = "🥇"
            elif rival['rang'] == 2:
                rang_color = "#C0C0C0"
                rang_icon = "🥈"
            elif rival['rang'] == 3:
                rang_color = "#CD7F32"
                rang_icon = "🥉"
            else:
                rang_color = "#FFFFFF"
                rang_icon = str(rival['rang'])

            pts_color = "#00FF00" if rival['points'] >= 0 else "#FF4444"

            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 15px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-left: 3px solid {rang_color};
                border-bottom: 1px solid #333;
                font-size: 0.9em;
            ">
                <span style="width: 40px; text-align: center; color: {rang_color}; font-weight: bold;">
                    {rang_icon}
                </span>
                <span style="flex: 2; color: #FFFFFF; font-weight: bold;">
                    {rival['pseudo']}
                </span>
                <span style="flex: 1; text-align: center; color: {pts_color}; font-weight: bold;">
                    {rival['points']}
                </span>
                <span style="flex: 1; text-align: center; color: #00FF00;">
                    {rival['bons_pronos']}
                </span>
                <span style="flex: 1; text-align: center; color: #FFD700;">
                    {rival['scores_exacts']}
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Fermer le tableau
        st.markdown("""
        <div style="
            height: 10px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 0 0 10px 10px;
        "></div>
        """, unsafe_allow_html=True)

    # Legende
    st.markdown("")
    st.caption("Bons Pronos = resultats 1N2 corrects | Exacts = scores parfaitement predits")
