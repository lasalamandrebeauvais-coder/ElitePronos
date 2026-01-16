"""
Module Admin Streamlit pour Elite Pronos
Gestion des validations d'inscriptions, resultats et communications
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Imports pour la gestion des journees
from modules.database_manager import (
    get_saison_actuelle,
    get_saison_label,
    get_journee_courante,
    valider_resultats_journee,
    mettre_a_jour_calendrier_reports
)
from modules.notifier_st import (
    envoyer_synthese_paris,
    envoyer_resultats_ironiques
)
from modules.calcul_gains import calculer_tous_gains_semaine, sauvegarder_resultats_semaine


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
    tab1, tab2, tab3 = st.tabs(["Inscriptions en attente", "Tous les utilisateurs", "Gestion Journee"])

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

    # === ONGLET 3 : GESTION JOURNEE ===
    with tab3:
        st.markdown("### Gestion de la Journee")

        saison = get_saison_actuelle()
        journee = get_journee_courante(saison)

        st.info(f"**Saison:** {get_saison_label(saison)} | **Journee courante:** J{journee}")

        # Selection de la journee
        semaine_selectionnee = st.number_input(
            "Journee a traiter",
            min_value=1,
            max_value=38,
            value=journee,
            step=1
        )

        st.markdown("---")

        # === SECTION 1: VALIDATION DES RESULTATS ===
        st.markdown("#### 1. Valider les Resultats")
        st.caption("Recupere les scores officiels depuis l'API et fige les resultats de la journee.")

        col_val1, col_val2 = st.columns(2)

        with col_val1:
            if st.button("VALIDER LES RESULTATS", type="primary", use_container_width=True):
                with st.spinner("Recuperation des scores..."):
                    success, message = valider_resultats_journee(semaine_selectionnee, saison)

                if success:
                    st.success(f"✅ {message}")

                    # Calculer automatiquement les gains
                    with st.spinner("Calcul des points..."):
                        resultats, msg_calc = calculer_tous_gains_semaine(semaine_selectionnee)
                        if resultats:
                            sauvegarder_resultats_semaine(semaine_selectionnee, resultats)
                            st.success(f"✅ Points calcules et sauvegardes!")
                        else:
                            st.warning(f"Points: {msg_calc}")
                else:
                    st.error(f"❌ {message}")

        with col_val2:
            if st.button("Mettre a jour calendrier (reports)", use_container_width=True):
                with st.spinner("Verification des reports..."):
                    success, message = mettre_a_jour_calendrier_reports(saison)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")

        st.markdown("---")

        # === SECTION 2: ENVOI RESUME & DEBRIEF ===
        st.markdown("#### 2. Envoyer le Resume & Debrief")
        st.caption("Envoie l'email de synthese des paris et le compte-rendu ironique a tous les joueurs.")

        col_email1, col_email2 = st.columns(2)

        with col_email1:
            if st.button("ENVOYER SYNTHESE PARIS", type="secondary", use_container_width=True):
                with st.spinner("Envoi des emails de synthese..."):
                    try:
                        resultats = envoyer_synthese_paris(semaine_selectionnee)
                        nb_envoyes = sum(1 for r in resultats if r['success'])
                        st.success(f"✅ {nb_envoyes}/{len(resultats)} email(s) de synthese envoye(s)")

                        # Afficher les details
                        with st.expander("Details des envois"):
                            for r in resultats:
                                if r['success']:
                                    st.write(f"✓ {r['user']}: {r['message']}")
                                else:
                                    st.write(f"✗ {r['user']}: {r['message']}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        with col_email2:
            if st.button("ENVOYER DEBRIEF IRONIQUE", type="secondary", use_container_width=True):
                with st.spinner("Envoi du debrief ironique..."):
                    try:
                        resultats = envoyer_resultats_ironiques(semaine_selectionnee)
                        nb_envoyes = sum(1 for r in resultats if r['success'])
                        st.success(f"✅ {nb_envoyes}/{len(resultats)} email(s) de debrief envoye(s)")

                        # Afficher les details
                        with st.expander("Details des envois"):
                            for r in resultats:
                                if r['success']:
                                    st.write(f"✓ {r['user']}: {r['message']}")
                                else:
                                    st.write(f"✗ {r['user']}: {r['message']}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        st.markdown("---")

        # === SECTION 3: BOT DEBRIEF SUR ACCUEIL ===
        st.markdown("#### 3. Debrief Bot sur Accueil")
        st.caption("Genere et affiche le compte-rendu ironique du Bot sur la page d'accueil.")

        if st.button("GENERER DEBRIEF ACCUEIL", use_container_width=True):
            # Generer le debrief et le sauvegarder pour l'accueil
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Recuperer le classement de la journee
                cursor.execute('''
                    SELECT u.pseudo, COALESCE(SUM(p.points_gagnes), 0) as total
                    FROM utilisateurs u
                    LEFT JOIN predictions p ON p.user_id = u.id
                    LEFT JOIN matches m ON p.match_id = m.id AND m.semaine_id = ?
                    WHERE u.statut = 'Actif'
                    GROUP BY u.id
                    ORDER BY total DESC
                    LIMIT 5
                ''', (semaine_selectionnee,))

                top5 = cursor.fetchall()

                # Generer le texte ironique
                import random
                phrases_intro = [
                    "Encore une semaine de drama footballistique !",
                    "Accrochez-vous, les resultats sont tombes...",
                    "Le verdict est sans appel cette semaine !",
                    "Qui a brille ? Qui s'est plante ? Voyons ca..."
                ]

                debrief_text = f"### Debrief J{semaine_selectionnee}\\n\\n"
                debrief_text += f"*{random.choice(phrases_intro)}*\\n\\n"

                if top5:
                    debrief_text += f"**Champion de la semaine:** @{top5[0][0]} avec {top5[0][1]} pts !\\n\\n"
                    if len(top5) > 1:
                        debrief_text += f"Mention speciale a @{top5[1][0]} ({top5[1][1]} pts) qui n'etait pas loin...\\n"
                    if len(top5) >= 5:
                        debrief_text += f"\\nEt une pensee emue pour @{top5[-1][0]} ({top5[-1][1]} pts). Courage, ca ira mieux la semaine prochaine ! 😅"

                # Sauvegarder dans app_settings
                cursor.execute('''
                    INSERT OR REPLACE INTO app_settings (cle, valeur, description)
                    VALUES ('debrief_accueil', ?, 'Debrief Bot affiche sur accueil')
                ''', (debrief_text,))

                conn.commit()
                conn.close()

                st.success("✅ Debrief genere et publie sur l'accueil!")
                st.markdown("**Apercu:**")
                st.markdown(debrief_text.replace('\\n', '\n'))

            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

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
