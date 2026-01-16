"""
Module Admin Streamlit pour Elite Pronos
Gestion des validations d'inscriptions
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')


def get_utilisateurs_en_attente():
    """Recupere tous les utilisateurs en attente de validation"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, pseudo, email, prenom, telephone
        FROM utilisateurs
        WHERE statut = 'en_attente'
        ORDER BY id DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return users


def get_tous_utilisateurs():
    """Recupere tous les utilisateurs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, pseudo, email, prenom, statut
        FROM utilisateurs
        ORDER BY id DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return users


def activer_compte(user_id):
    """Active le compte d'un utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE utilisateurs
        SET statut = 'Actif'
        WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
    return True


def suspendre_compte(user_id):
    """Suspend le compte d'un utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE utilisateurs
        SET statut = 'En pause'
        WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
    return True


def supprimer_compte(user_id):
    """Supprime un utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM utilisateurs WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True


def afficher_panel_admin():
    """Affiche le panneau d'administration"""

    st.markdown("## Panel Administration")
    st.markdown("---")

    # Onglets
    tab1, tab2 = st.tabs(["Inscriptions en attente", "Tous les utilisateurs"])

    # === ONGLET 1 : INSCRIPTIONS EN ATTENTE ===
    with tab1:
        st.markdown("### Nouvelles inscriptions")

        users_attente = get_utilisateurs_en_attente()

        if not users_attente:
            st.info("Aucune inscription en attente de validation.")
        else:
            st.warning(f"{len(users_attente)} inscription(s) en attente")

            for user in users_attente:
                user_id, pseudo, email, prenom, telephone = user

                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.markdown(f"**{pseudo}**")
                        st.caption(f"{email}")

                    with col2:
                        st.caption(f"Prenom: {prenom or 'N/A'}")
                        st.caption(f"Tel: {telephone or 'N/A'}")

                    with col3:
                        if st.button("Activer", key=f"activer_{user_id}", type="primary"):
                            activer_compte(user_id)
                            st.success(f"{pseudo} active!")
                            st.rerun()

                        if st.button("Refuser", key=f"refuser_{user_id}"):
                            supprimer_compte(user_id)
                            st.warning(f"{pseudo} supprime")
                            st.rerun()

                    st.markdown("---")

    # === ONGLET 2 : TOUS LES UTILISATEURS ===
    with tab2:
        st.markdown("### Liste complete des utilisateurs")

        all_users = get_tous_utilisateurs()

        if not all_users:
            st.info("Aucun utilisateur dans la base.")
        else:
            # Afficher sous forme de tableau
            st.markdown(f"**{len(all_users)} utilisateur(s) au total**")

            # En-tete du tableau
            header_cols = st.columns([1, 2, 3, 2, 2])
            header_cols[0].markdown("**ID**")
            header_cols[1].markdown("**Pseudo**")
            header_cols[2].markdown("**Email**")
            header_cols[3].markdown("**Statut**")
            header_cols[4].markdown("**Actions**")

            st.markdown("---")

            for user in all_users:
                user_id, pseudo, email, prenom, statut = user

                cols = st.columns([1, 2, 3, 2, 2])

                cols[0].write(user_id)
                cols[1].write(pseudo)
                cols[2].write(email or "N/A")

                # Badge de statut avec couleur
                if statut == "Actif":
                    cols[3].success(statut)
                elif statut == "en_attente":
                    cols[3].warning("En attente")
                elif statut == "En pause":
                    cols[3].error(statut)
                else:
                    cols[3].info(statut or "N/A")

                # Actions
                with cols[4]:
                    action_cols = st.columns(2)

                    if statut != "Actif":
                        if action_cols[0].button("✓", key=f"act_{user_id}", help="Activer"):
                            activer_compte(user_id)
                            st.rerun()

                    if statut == "Actif":
                        if action_cols[0].button("⏸", key=f"pause_{user_id}", help="Suspendre"):
                            suspendre_compte(user_id)
                            st.rerun()

                    if action_cols[1].button("🗑", key=f"del_{user_id}", help="Supprimer"):
                        supprimer_compte(user_id)
                        st.rerun()

    # Stats rapides
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Stats Admin")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE statut = 'Actif'")
    nb_actifs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE statut = 'en_attente'")
    nb_attente = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM utilisateurs")
    nb_total = cursor.fetchone()[0]

    conn.close()

    st.sidebar.metric("Actifs", nb_actifs)
    st.sidebar.metric("En attente", nb_attente)
    st.sidebar.metric("Total", nb_total)
