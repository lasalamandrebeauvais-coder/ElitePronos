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
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

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


def is_admin(user_id):
    """Verifie si un utilisateur est admin"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM utilisateurs WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1


def is_super_admin(pseudo):
    """Verifie si c'est le super admin (Baggio)"""
    return pseudo.lower() == 'baggio'


def promouvoir_admin(user_id):
    """Promouvoit un utilisateur en admin"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE utilisateurs SET is_admin = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True


def revoquer_admin(user_id):
    """Revoque les droits admin d'un utilisateur"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Verifier que ce n'est pas Baggio (super admin)
    cursor.execute("SELECT pseudo FROM utilisateurs WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    if result and result[0].lower() == 'baggio':
        conn.close()
        return False  # Ne peut pas revoquer le super admin
    cursor.execute("UPDATE utilisateurs SET is_admin = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True


def get_nombre_admins():
    """Retourne le nombre d'administrateurs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE is_admin = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_tous_utilisateurs():
    """Recupere tous les utilisateurs avec statut admin"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, pseudo, email, prenom, statut, COALESCE(is_admin, 0) as is_admin
        FROM utilisateurs
        ORDER BY is_admin DESC, id DESC
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

    # Header avec mascotte
    col_title, col_mascot = st.columns([4, 1])
    with col_title:
        st.markdown("## Panel Administration")
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo administration.png")
        if os.path.exists(mascot_path):
            from PIL import Image
            mascot_img = Image.open(mascot_path)
            st.image(mascot_img, width=80)
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

        # Afficher le nombre d'admins
        nb_admins = get_nombre_admins()
        st.info(f"**{nb_admins} administrateur(s)** dans le systeme")

        all_users = get_tous_utilisateurs()

        if not all_users:
            st.info("Aucun utilisateur dans la base.")
        else:
            # Afficher sous forme de tableau
            st.markdown(f"**{len(all_users)} utilisateur(s) au total**")

            # En-tete du tableau
            header_cols = st.columns([1, 2, 2, 1.5, 1.5, 2])
            header_cols[0].markdown("**ID**")
            header_cols[1].markdown("**Pseudo**")
            header_cols[2].markdown("**Email**")
            header_cols[3].markdown("**Statut**")
            header_cols[4].markdown("**Role**")
            header_cols[5].markdown("**Actions**")

            st.markdown("---")

            for user in all_users:
                user_id, pseudo, email, prenom, statut, user_is_admin = user

                cols = st.columns([1, 2, 2, 1.5, 1.5, 2])

                # ID avec style bloc
                cols[0].markdown(f"""
                <div style="background: #002040; border: 1px solid #D4AF37; border-radius: 5px;
                     padding: 5px 10px; text-align: center; color: #D4AF37; font-weight: bold;">
                    {user_id}
                </div>
                """, unsafe_allow_html=True)

                # Pseudo avec badge admin
                if user_is_admin:
                    cols[1].markdown(f"**{pseudo}** 👑")
                else:
                    cols[1].write(pseudo)

                cols[2].write(email or "N/A")

                # Badge de statut avec couleur
                if statut == "Actif":
                    cols[3].success(statut)
                elif statut == "en_attente":
                    cols[3].warning("Attente")
                elif statut == "En pause":
                    cols[3].error(statut)
                else:
                    cols[3].info(statut or "N/A")

                # Role admin
                if user_is_admin:
                    if is_super_admin(pseudo):
                        cols[4].markdown("**SUPER ADMIN**")
                    else:
                        cols[4].markdown("*Admin*")
                else:
                    cols[4].write("Joueur")

                # Actions avec style bloc (comme ID)
                with cols[5]:
                    action_cols = st.columns(4)

                    # Activer/Suspendre
                    with action_cols[0]:
                        if statut != "Actif":
                            if st.button("✓", key=f"act_{user_id}", help="Activer", use_container_width=True):
                                activer_compte(user_id)
                                st.rerun()
                        else:
                            if st.button("⏸", key=f"pause_{user_id}", help="Suspendre", use_container_width=True):
                                suspendre_compte(user_id)
                                st.rerun()

                    # Bouton Admin toggle (sauf pour super admin)
                    with action_cols[1]:
                        if not is_super_admin(pseudo):
                            if user_is_admin:
                                if st.button("👤", key=f"revoke_{user_id}", help="Retirer Admin", use_container_width=True):
                                    if revoquer_admin(user_id):
                                        st.rerun()
                            else:
                                if st.button("👑", key=f"promote_{user_id}", help="Rendre Admin", use_container_width=True):
                                    promouvoir_admin(user_id)
                                    st.rerun()
                        else:
                            st.markdown('<div style="text-align:center; color:#FFD700;">👑</div>', unsafe_allow_html=True)

                    # Supprimer (sauf super admin)
                    with action_cols[2]:
                        if not is_super_admin(pseudo):
                            if st.button("🗑", key=f"del_{user_id}", help="Supprimer", use_container_width=True):
                                supprimer_compte(user_id)
                                st.rerun()

    # === ONGLET 3 : GESTION JOURNEE ===
    with tab3:
        st.markdown("### Gestion de la Journee")

        saison = get_saison_actuelle()
        journee = get_journee_courante(saison)

        st.info(f"**Saison:** {get_saison_label(saison)} | **Journee courante:** J{journee}")

        # === SECTION 0: IMPORT CALENDRIER ===
        st.markdown("#### 0. Import Calendrier Ligue 1")
        st.caption("Importe le calendrier complet de la saison depuis l'API Football-Data.")

        col_import1, col_import2 = st.columns(2)

        with col_import1:
            if st.button("IMPORTER CALENDRIER COMPLET", type="primary", use_container_width=True):
                with st.spinner("Import du calendrier en cours..."):
                    try:
                        from modules.bot_sourcing import importer_calendrier_complet_l1
                        success, message = importer_calendrier_complet_l1(saison)
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        with col_import2:
            if st.button("IMPORTER SEMAINE COURANTE", use_container_width=True):
                with st.spinner("Import des matchs de la semaine..."):
                    try:
                        from modules.bot_sourcing import sourcing_semaine_courante
                        nb = sourcing_semaine_courante()
                        st.success(f"✅ {nb} match(s) importe(s) pour cette semaine")

                        # Kingo fait ses pronostics automatiquement
                        from modules.kingo_bot import kingo_pronostique_semaine
                        if kingo_pronostique_semaine():
                            st.info("👑 Kingo a fait ses pronostics!")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        # === SECTION KINGO ===
        st.markdown("---")
        st.markdown("#### 👑 Kingo - Le Roi des Pronostics")

        col_kingo1, col_kingo2 = st.columns(2)

        with col_kingo1:
            if st.button("KINGO PRONOSTIQUE", use_container_width=True):
                with st.spinner("Kingo analyse les matchs..."):
                    try:
                        from modules.kingo_bot import kingo_pronostique_semaine
                        if kingo_pronostique_semaine(semaine_selectionnee if 'semaine_selectionnee' in dir() else None, saison):
                            st.success("👑 Kingo a fait ses pronostics pour cette semaine!")
                        else:
                            st.warning("Kingo a deja pronostique ou aucun match disponible.")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        with col_kingo2:
            # Afficher les pronostics de Kingo
            if st.button("VOIR PRONOS KINGO", use_container_width=True):
                try:
                    from modules.kingo_bot import get_or_create_kingo
                    kingo_id = get_or_create_kingo()

                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT m.equipe_home, m.equipe_away, p.score_prono_home, p.score_prono_away, p.mise_points
                        FROM predictions p
                        JOIN matches m ON p.match_id = m.id
                        WHERE p.user_id = ? AND m.semaine_id = ?
                    """, (kingo_id, journee))
                    pronos = cursor.fetchall()
                    conn.close()

                    if pronos:
                        st.markdown("**Pronostics de Kingo:**")
                        for home, away, sh, sa, mise in pronos:
                            st.write(f"• {home} vs {away}: **{sh}-{sa}** ({mise} pts)")
                    else:
                        st.info("Kingo n'a pas encore pronostique cette semaine.")
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

        st.markdown("---")

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
