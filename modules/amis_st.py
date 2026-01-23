"""
Module Amis/Rivaux Streamlit pour Elite Pronos
Gestion des relations entre joueurs et comparaison directe
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime

# Chemins
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')


def get_avatar_path(pseudo):
    """Retourne le chemin de l'avatar du joueur"""
    avatar_file = os.path.join(AVATARS_PATH, f"{pseudo}.png")
    if os.path.exists(avatar_file):
        return avatar_file
    return None


def get_tous_les_joueurs_avec_stats(current_user_id):
    """
    Recupere tous les joueurs actifs avec leurs stats:
    - Position au classement general
    - Nombre de bons pronos (1N2 correct)
    - Nombre de scores exacts
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Recuperer tous les joueurs avec leurs stats
    cursor.execute("""
        SELECT
            u.id,
            u.pseudo,
            u.prenom,
            COALESCE(SUM(p.points_gagnes), 0) as total_points,
            COUNT(CASE WHEN p.points_gagnes > 0 THEN 1 END) as bons_pronos,
            COUNT(CASE WHEN p.points_gagnes >= 10 AND
                  p.score_prono_home = m.score_final_home AND
                  p.score_prono_away = m.score_final_away THEN 1 END) as scores_exacts
        FROM utilisateurs u
        LEFT JOIN predictions p ON u.id = p.user_id
        LEFT JOIN matches m ON p.match_id = m.id
        WHERE u.statut = 'Actif' AND u.id != ?
        GROUP BY u.id, u.pseudo, u.prenom
        ORDER BY total_points DESC
    """, (current_user_id,))

    joueurs = cursor.fetchall()
    conn.close()

    # Ajouter le rang
    joueurs_avec_rang = []
    for idx, (uid, pseudo, prenom, points, bons_pronos, scores_exacts) in enumerate(joueurs):
        joueurs_avec_rang.append({
            'id': uid,
            'pseudo': pseudo,
            'prenom': prenom,
            'rang': idx + 1,
            'points': points,
            'bons_pronos': bons_pronos,
            'scores_exacts': scores_exacts
        })

    return joueurs_avec_rang


def get_rivaux_selectionnes(user_id):
    """Recupere les IDs des rivaux selectionnes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CASE
            WHEN r.utilisateur_id = ? THEN r.ami_id
            ELSE r.utilisateur_id
        END as rival_id
        FROM relations r
        WHERE (r.utilisateur_id = ? OR r.ami_id = ?)
          AND r.statut = 'amis'
    """, (user_id, user_id, user_id))

    rivaux_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rivaux_ids


def ajouter_rival(user_id, rival_id):
    """Ajoute un rival directement (pas de demande)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO relations (utilisateur_id, ami_id, statut)
            VALUES (?, ?, 'amis')
        """, (user_id, rival_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def supprimer_rival(user_id, rival_id):
    """Supprime un rival"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM relations
        WHERE (utilisateur_id = ? AND ami_id = ?)
           OR (utilisateur_id = ? AND ami_id = ?)
    """, (user_id, rival_id, rival_id, user_id))

    conn.commit()
    conn.close()
    return True


def afficher_amis(user):
    """Affiche le module de gestion des amis/rivaux"""

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

    # Recuperer tous les joueurs avec stats
    tous_joueurs = get_tous_les_joueurs_avec_stats(current_user_id)
    rivaux_ids = get_rivaux_selectionnes(current_user_id)

    # === RECHERCHE ET SELECTION MULTIPLE ===
    st.markdown("### Ajouter des rivaux")

    # Creer la liste pour le multiselect
    options_joueurs = {f"#{j['rang']} - {j['pseudo']} ({j['points']} pts)": j['id'] for j in tous_joueurs}

    # Multiselect pour choisir les rivaux
    selected_labels = st.multiselect(
        "Rechercher et selectionner des joueurs",
        options=list(options_joueurs.keys()),
        default=[label for label, jid in options_joueurs.items() if jid in rivaux_ids],
        placeholder="Tapez pour rechercher..."
    )

    # Bouton pour valider la selection
    if st.button("Valider ma selection", type="primary"):
        # Recuperer les IDs selectionnes
        selected_ids = [options_joueurs[label] for label in selected_labels]

        # Ajouter les nouveaux rivaux
        for rid in selected_ids:
            if rid not in rivaux_ids:
                ajouter_rival(current_user_id, rid)

        # Supprimer les rivaux deselectionnes
        for rid in rivaux_ids:
            if rid not in selected_ids:
                supprimer_rival(current_user_id, rid)

        st.success("Selection mise a jour!")
        st.rerun()

    st.markdown("---")

    # === AFFICHAGE DES RIVAUX SELECTIONNES ===
    st.markdown("### Classement de mes rivaux")

    # Filtrer les joueurs selectionnes
    rivaux_affiches = [j for j in tous_joueurs if j['id'] in rivaux_ids]

    if not rivaux_affiches:
        st.info("Aucun rival selectionne. Utilisez le menu ci-dessus pour en ajouter.")
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
        ">
            <span style="flex: 0.5; text-align: center;">#</span>
            <span style="flex: 2;">Joueur</span>
            <span style="flex: 1; text-align: center;">Bons Pronos</span>
            <span style="flex: 1; text-align: center;">Scores Exacts</span>
        </div>
        """, unsafe_allow_html=True)

        # Lignes du tableau
        for rival in rivaux_affiches:
            # Couleur selon le rang
            if rival['rang'] == 1:
                rang_color = "#FFD700"  # Or
                rang_icon = "1"
            elif rival['rang'] == 2:
                rang_color = "#C0C0C0"  # Argent
                rang_icon = "2"
            elif rival['rang'] == 3:
                rang_color = "#CD7F32"  # Bronze
                rang_icon = "3"
            else:
                rang_color = "#FFFFFF"
                rang_icon = str(rival['rang'])

            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 15px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-left: 3px solid {rang_color};
                border-bottom: 1px solid #333;
            ">
                <span style="flex: 0.5; text-align: center; color: {rang_color}; font-weight: bold; font-size: 1.2em;">
                    {rang_icon}
                </span>
                <span style="flex: 2; color: #FFFFFF;">
                    <strong>{rival['pseudo']}</strong>
                    <span style="color: #AAAAAA; font-size: 0.85em;"> - {rival['points']} pts</span>
                </span>
                <span style="flex: 1; text-align: center; color: #00FF00; font-weight: bold;">
                    {rival['bons_pronos']}
                </span>
                <span style="flex: 1; text-align: center; color: #FFD700; font-weight: bold;">
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
        st.caption("Bons Pronos = resultats 1N2 corrects | Scores Exacts = scores parfaitement predits")
