"""
Module Admin Streamlit pour Elite Pronos
Gestion des validations d'inscriptions, resultats et communications
"""
import streamlit as st
import os
from datetime import datetime

# Supabase
from modules.supabase_db import get_supabase
from modules.login_st import get_current_user

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
    supabase = get_supabase()
    users = supabase._request('GET', 'utilisateurs?statut=eq.en_attente&select=id,pseudo,email,prenom,telephone&order=id.desc') or []
    return [(u['id'], u['pseudo'], u.get('email'), u.get('prenom'), u.get('telephone')) for u in users]


def is_admin(user_id):
    """Verifie si un utilisateur est admin"""
    supabase = get_supabase()
    result = supabase._request('GET', f'utilisateurs?id=eq.{user_id}&select=is_admin')
    return result and len(result) > 0 and result[0].get('is_admin', False)


def is_super_admin(pseudo):
    """Verifie si c'est le super admin (Baggio)"""
    return pseudo.lower() == 'baggio'


def promouvoir_admin(user_id):
    """Promouvoit un utilisateur en admin"""
    supabase = get_supabase()
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'is_admin': True})
    return True


def revoquer_admin(user_id):
    """Revoque les droits admin d'un utilisateur"""
    supabase = get_supabase()
    result = supabase._request('GET', f'utilisateurs?id=eq.{user_id}&select=pseudo')
    if result and result[0].get('pseudo', '').lower() == 'baggio':
        return False
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'is_admin': False})
    return True


def get_nombre_admins():
    """Retourne le nombre d'administrateurs"""
    supabase = get_supabase()
    result = supabase._request('GET', 'utilisateurs?is_admin=eq.true&select=id') or []
    return len(result)


def get_tous_utilisateurs():
    """Recupere tous les utilisateurs avec statut admin"""
    supabase = get_supabase()
    users = supabase._request('GET', 'utilisateurs?select=id,pseudo,email,prenom,statut,is_admin&order=is_admin.desc,id.desc') or []
    return [(u['id'], u['pseudo'], u.get('email'), u.get('prenom'), u.get('statut'), u.get('is_admin', False)) for u in users]


def activer_compte(user_id):
    """Active le compte d'un utilisateur"""
    supabase = get_supabase()
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'statut': 'Actif'})
    return True


def suspendre_compte(user_id):
    """Suspend le compte d'un utilisateur"""
    supabase = get_supabase()
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'statut': 'En pause'})
    return True


def supprimer_compte(user_id):
    """Supprime un utilisateur et toutes ses donnees liees"""
    supabase = get_supabase()

    try:
        # Supprimer les donnees liees (contraintes FK)
        supabase._request('DELETE', f'predictions?user_id=eq.{user_id}')
        supabase._request('DELETE', f'stock_jokers?utilisateur_id=eq.{user_id}')
        supabase._request('DELETE', f'jokers_historique?utilisateur_id=eq.{user_id}')

        # Supprimer l'utilisateur
        result = supabase._request('DELETE', f'utilisateurs?id=eq.{user_id}')
        return True
    except Exception as e:
        print(f"Erreur suppression compte: {e}")
        return False


@st.dialog("Confirmer la suppression")
def confirmer_suppression(user_id, pseudo):
    """Dialog de confirmation pour supprimer un utilisateur"""
    st.warning(f"Voulez-vous vraiment supprimer **{pseudo}** ?")
    st.caption("Cette action est irreversible.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Annuler", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Supprimer", type="primary", use_container_width=True):
            if supprimer_compte(user_id):
                st.session_state.admin_message = f"✅ {pseudo} a ete supprime."
            else:
                st.session_state.admin_message = f"❌ Erreur lors de la suppression de {pseudo}."
            st.rerun()


def afficher_panel_admin():
    """Affiche le panneau d'administration"""

    # Afficher message de confirmation si present
    if st.session_state.get('admin_message'):
        st.success(st.session_state.admin_message)
        st.session_state.admin_message = None

    # Header avec bouton retour et mascotte
    col_back, col_title, col_mascot = st.columns([0.6, 3.5, 1])
    with col_back:
        if st.button("◀", help="Retour", use_container_width=True):
            st.session_state.page = "Accueil"
            st.rerun()
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
                            if supprimer_compte(user_id):
                                st.session_state.admin_message = f"❌ {pseudo} refuse et supprime."
                            else:
                                st.session_state.admin_message = f"⚠️ Erreur lors du refus de {pseudo}."
                            st.rerun()

                    st.markdown("---")

    # === ONGLET 2 : TOUS LES UTILISATEURS ===
    with tab2:
        st.markdown("### Liste complete des utilisateurs")

        # Style CSS pour les boutons d'action - fond bleu, texte blanc
        st.markdown("""
        <style>
            /* Boutons actions admin - fond bleu marine, texte blanc */
            div[data-testid="stHorizontalBlock"] button {
                background-color: #001529 !important;
                color: #FFFFFF !important;
                border: 1px solid #D4AF37 !important;
                border-radius: 5px !important;
            }
            div[data-testid="stHorizontalBlock"] button:hover {
                background-color: #002855 !important;
                border-color: #FFD700 !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # Afficher le nombre d'admins
        nb_admins = get_nombre_admins()
        st.info(f"**{nb_admins} administrateur(s)** dans le systeme")

        all_users = get_tous_utilisateurs()

        if not all_users:
            st.info("Aucun utilisateur dans la base.")
        else:
            # Afficher sous forme de tableau
            st.markdown(f"**{len(all_users)} utilisateur(s) au total**")

            # Style compact
            st.markdown("""<style>
                .compact-row { margin-bottom: -15px !important; }
                .stCheckbox { margin: 0 !important; padding: 0 !important; }
            </style>""", unsafe_allow_html=True)

            # En-tête du tableau
            st.markdown("""
            <div style="display:flex;gap:10px;padding:5px 0;border-bottom:1px solid #D4AF37;margin-bottom:5px;">
                <span style="width:30px;color:#D4AF37;font-size:0.7em;font-weight:bold;">#</span>
                <span style="width:100px;color:#D4AF37;font-size:0.7em;font-weight:bold;">Pseudo</span>
                <span style="flex:1;color:#D4AF37;font-size:0.7em;font-weight:bold;">Email</span>
                <span style="width:40px;color:#D4AF37;font-size:0.7em;font-weight:bold;">Actif</span>
                <span style="width:40px;color:#D4AF37;font-size:0.7em;font-weight:bold;">Admin</span>
                <span style="width:40px;color:#FF4444;font-size:0.7em;font-weight:bold;">Suppr</span>
            </div>
            """, unsafe_allow_html=True)

            # Liste des utilisateurs
            for user in all_users:
                user_id, pseudo, email, prenom, statut, user_is_admin = user

                is_actif = statut == "Actif"
                is_admin_user = user_is_admin or False
                is_super = is_super_admin(pseudo)

                cols = st.columns([0.4, 1.3, 2.2, 0.4, 0.4, 0.4])

                with cols[0]:
                    st.markdown(f"<span style='color:#FFF;font-size:0.75em;'>{user_id}</span>", unsafe_allow_html=True)

                with cols[1]:
                    st.markdown(f"<span style='color:#FFF;font-size:0.75em;'>{pseudo}</span>", unsafe_allow_html=True)

                with cols[2]:
                    st.markdown(f"<span style='color:#888;font-size:0.7em;'>{email or '-'}</span>", unsafe_allow_html=True)

                with cols[3]:
                    # Case Actif: vert si actif, rouge si pause
                    bg = "🟢" if is_actif else "🔴"
                    new_actif = st.checkbox(bg, value=is_actif, key=f"actif_{user_id}", label_visibility="collapsed")
                    if new_actif != is_actif:
                        activer_compte(user_id) if new_actif else suspendre_compte(user_id)
                        st.rerun()

                with cols[4]:
                    # Admin: couronne si admin
                    if is_admin_user:
                        st.markdown("👑", unsafe_allow_html=True)
                    # Seul Baggio peut promouvoir/revoquer les admins
                    current_user = get_current_user()
                    is_current_super = current_user and is_super_admin(current_user.get('pseudo', ''))
                    if is_current_super and not is_super:
                        new_admin = st.checkbox("Admin", value=is_admin_user, key=f"admin_{user_id}", label_visibility="collapsed")
                        if new_admin != is_admin_user:
                            promouvoir_admin(user_id) if new_admin else revoquer_admin(user_id)
                            st.rerun()

                with cols[5]:
                    # Supprimer
                    if not is_super:
                        if st.button("🗑", key=f"del_{user_id}"):
                            confirmer_suppression(user_id, pseudo)

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

    supabase = get_supabase()
    all_users = supabase._request('GET', 'utilisateurs?select=statut') or []
    nb_actifs = sum(1 for u in all_users if u.get('statut') == 'Actif')
    nb_attente = sum(1 for u in all_users if u.get('statut') == 'en_attente')
    nb_total = len(all_users)

    st.sidebar.metric("Actifs", nb_actifs)
    st.sidebar.metric("En attente", nb_attente)
    st.sidebar.metric("Total", nb_total)
