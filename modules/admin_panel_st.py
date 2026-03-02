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
    envoyer_resultats_ironiques,
    envoyer_email_bienvenue,
    envoyer_email_prospection,
    envoyer_tableau_pronos_admin,
    envoyer_lancement_journee
)


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


SUPER_ADMIN_PSEUDO = 'baggio'

def is_super_admin(pseudo):
    """Verifie si c'est le super admin"""
    return pseudo.lower() == SUPER_ADMIN_PSEUDO


def promouvoir_admin(user_id):
    """Promouvoit un utilisateur en admin"""
    supabase = get_supabase()
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'is_admin': True})
    # Invalider le cache admin
    try:
        from modules.database_manager import _fetch_is_admin
        _fetch_is_admin.clear()
    except Exception:
        pass
    return True


def revoquer_admin(user_id):
    """Revoque les droits admin d'un utilisateur"""
    supabase = get_supabase()
    result = supabase._request('GET', f'utilisateurs?id=eq.{user_id}&select=pseudo')
    if result and result[0].get('pseudo', '').lower() == SUPER_ADMIN_PSEUDO:
        return False
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'is_admin': False})
    # Invalider le cache admin
    try:
        from modules.database_manager import _fetch_is_admin
        _fetch_is_admin.clear()
    except Exception:
        pass
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
    """Active le compte d'un utilisateur et envoie l'email de bienvenue"""
    supabase = get_supabase()
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'statut': 'Actif'})

    # Envoyer l'email de bienvenue
    user_data = supabase._request('GET', f'utilisateurs?id=eq.{user_id}&select=pseudo,prenom,email')
    if user_data and user_data[0].get('email'):
        envoyer_email_bienvenue(user_data[0])

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
        if st.button("Supprimer definitivement", type="primary", use_container_width=True):
            if supprimer_compte(user_id):
                st.session_state.admin_message = f"@{pseudo} a ete supprime."
                st.session_state.admin_tab = 1  # Rester sur l'onglet Utilisateurs
            else:
                st.session_state.admin_message = f"Erreur lors de la suppression de {pseudo}."
            st.rerun()


def afficher_panel_admin():
    """Affiche le panneau d'administration"""

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
            try:
                from PIL import Image
                mascot_img = Image.open(mascot_path)
                st.image(mascot_img, width=80)
            except Exception:
                pass
    st.markdown("---")

    # Onglets
    tab3, tab1, tab2, tab4 = st.tabs(["Gestion Journee", "Inscriptions en attente", "Tous les utilisateurs", "Prospection"])

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

        # Message de confirmation suppression
        if st.session_state.get('admin_message'):
            st.success(st.session_state.admin_message)
            st.session_state.admin_message = None

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

        # Initialiser Supabase pour cet onglet
        supabase = get_supabase()

        saison = get_saison_actuelle()
        journee = get_journee_courante(saison)

        st.info(f"**Saison:** {get_saison_label(saison)} | **Journee courante:** J{journee}")

        # Selection de la journee EN PREMIER
        col_sel, col_avancer = st.columns([2, 1])
        with col_sel:
            semaine_selectionnee = st.number_input(
                "Journee a traiter",
                min_value=1,
                max_value=38,
                value=journee,
                step=1
            )
        with col_avancer:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("AVANCER JOURNEE →", type="primary", use_container_width=True):
                nouvelle_j = journee + 1
                supabase._request('PATCH', f'saisons?annee_debut=eq.{saison}', {'journee_courante': nouvelle_j})
                st.cache_data.clear()
                st.success(f"Journee courante avancee a J{nouvelle_j}")
                st.rerun()

        st.markdown("---")

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
            if st.button("IMPORTER TOUS LES MATCHS", use_container_width=True):
                with st.spinner(f"Import des matchs J{semaine_selectionnee} depuis l'API..."):
                    try:
                        from modules.database_manager import importer_matchs_journee_supabase
                        success, message, nb = importer_matchs_journee_supabase(semaine_selectionnee, saison)
                        if success:
                            st.success(f"✅ {message}")
                            st.info("👇 Activez les matchs souhaites dans 'Gestion des Matchs' ci-dessous")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        st.markdown("---")

        # === SECTION 1: SELECTION DES MATCHS ===
        st.markdown("#### 1. Selection des Matchs de la Journee")
        st.caption("Activez les matchs sur lesquels les joueurs pourront pronostiquer.")

        # Reinitialiser Supabase pour cette section (evite UnboundLocalError)
        supabase = get_supabase()

        # Afficher les matchs actuels
        matchs_journee = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_selectionnee}&saison_id=eq.{saison}&is_active=eq.true&select=id,equipe_home,equipe_away,cote_home,cote_draw,cote_away,date_match&order=id'
        ) or []

        # Recuperer tous les matchs de la journee (actifs et inactifs) avec cotes
        tous_matchs = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_selectionnee}&saison_id=eq.{saison}&select=id,equipe_home,equipe_away,is_active,date_match,championnat,cote_home,cote_draw,cote_away&order=is_active.desc,date_match'
        ) or []

        nb_actifs = len(matchs_journee)
        nb_total = len(tous_matchs)

        if nb_total > 0:
            st.info(f"**{nb_actifs} matchs actifs** sur {nb_total} disponibles pour J{semaine_selectionnee}")

            # Afficher tous les matchs avec checkboxes
            st.markdown("**Cochez les matchs a activer:**")

            for m in tous_matchs:
                is_actif = m.get('is_active', False)
                border_color = "#00FF00" if is_actif else "#333"
                bg = "#002040" if is_actif else "#001529"
                champ = m.get('championnat', '')

                # Date formatee
                date_info = ""
                if m.get('date_match'):
                    try:
                        dt = datetime.fromisoformat(m['date_match'].replace('Z', '+00:00'))
                        jours = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
                        date_info = f"{jours[dt.weekday()]} {dt.day}/{dt.month} {dt.hour}h{dt.minute:02d}"
                    except:
                        date_info = ""

                # Cotes
                c_h = m.get('cote_home') or 0
                c_n = m.get('cote_draw') or 0
                c_a = m.get('cote_away') or 0

                col_m1, col_m2 = st.columns([4, 0.5])
                with col_m1:
                    st.markdown(f"""<div style="background:{bg}; border-left:4px solid {border_color}; padding:8px 10px; margin:2px 0; border-radius:5px; font-size:0.8em;">
<div style="display:flex; justify-content:space-between; align-items:center;"><span style="color:#FFF; font-weight:bold;">{m['equipe_home']} vs {m['equipe_away']}</span><span style="color:#888; font-size:0.8em;">{champ} | {date_info}</span></div>
<div style="display:flex; gap:15px; margin-top:4px; font-size:0.85em;"><span style="color:#D4AF37;">1: {c_h:.2f}</span><span style="color:#D4AF37;">N: {c_n:.2f}</span><span style="color:#D4AF37;">2: {c_a:.2f}</span></div>
</div>""", unsafe_allow_html=True)
                with col_m2:
                    new_actif = st.checkbox("✓", value=is_actif, key=f"match_actif_{m['id']}", label_visibility="collapsed")
                    if new_actif != is_actif:
                        supabase._request('PATCH', f'matches?id=eq.{m["id"]}', {'is_active': new_actif})
                        st.rerun()

            # Bouton pour faire repronostiquer Kingo apres modification
            if st.button("KINGO REPRONOSTIQUE", type="primary", use_container_width=True):
                from modules.kingo_bot import kingo_pronostique_semaine
                if kingo_pronostique_semaine(semaine_selectionnee, saison, force=True):
                    st.success("👑 Kingo a fait ses pronostics sur les matchs actifs!")
                    # Envoyer l'email nouvelle journee a tous les joueurs
                    with st.spinner("Envoi des emails nouvelle journee..."):
                        try:
                            resultats, _ = envoyer_lancement_journee(semaine_selectionnee)
                            nb_ok = sum(1 for r in resultats if r['success'])
                            st.success(f"📧 Email nouvelle journee envoye a {nb_ok}/{len(resultats)} joueur(s)")
                        except Exception as e:
                            st.warning(f"⚠️ Pronostics OK mais erreur email: {str(e)}")
                else:
                    st.warning("Kingo n'a pas pu pronostiquer.")
                st.rerun()
        else:
            st.warning(f"Aucun match importe pour J{semaine_selectionnee}. Cliquez sur 'IMPORTER TOUS LES MATCHS' ci-dessus.")

        # === MODIFICATION DES COTES ===
        with st.expander("Modifier les cotes des matchs"):
            st.caption("Saisir manuellement les cotes de chaque match (source: Winamax, Betclic...)")

            if matchs_journee:
                cotes_modifiees = False

                for m in matchs_journee:
                    st.markdown(f"**{m['equipe_home']} vs {m['equipe_away']}**")

                    col_c1, col_c2, col_c3 = st.columns(3)

                    with col_c1:
                        new_cote_home = st.number_input(
                            "Cote 1 (Dom)",
                            min_value=1.01,
                            max_value=15.0,
                            value=float(m.get('cote_home') or 2.0),
                            step=0.05,
                            key=f"cote_home_{m['id']}"
                        )

                    with col_c2:
                        new_cote_draw = st.number_input(
                            "Cote N (Nul)",
                            min_value=1.01,
                            max_value=15.0,
                            value=float(m.get('cote_draw') or 3.0),
                            step=0.05,
                            key=f"cote_draw_{m['id']}"
                        )

                    with col_c3:
                        new_cote_away = st.number_input(
                            "Cote 2 (Ext)",
                            min_value=1.01,
                            max_value=15.0,
                            value=float(m.get('cote_away') or 2.5),
                            step=0.05,
                            key=f"cote_away_{m['id']}"
                        )

                    # Stocker les nouvelles valeurs dans session_state
                    if f"cotes_to_save_{m['id']}" not in st.session_state:
                        st.session_state[f"cotes_to_save_{m['id']}"] = {
                            'home': m.get('cote_home'),
                            'draw': m.get('cote_draw'),
                            'away': m.get('cote_away')
                        }

                    st.session_state[f"cotes_to_save_{m['id']}"] = {
                        'home': new_cote_home,
                        'draw': new_cote_draw,
                        'away': new_cote_away
                    }

                    st.markdown("---")

                # Bouton pour sauvegarder toutes les cotes
                if st.button("SAUVEGARDER LES COTES", type="primary", use_container_width=True):
                    nb_updates = 0
                    for m in matchs_journee:
                        cotes = st.session_state.get(f"cotes_to_save_{m['id']}")
                        if cotes:
                            supabase._request('PATCH', f'matches?id=eq.{m["id"]}', {
                                'cote_home': round(cotes['home'], 2),
                                'cote_draw': round(cotes['draw'], 2),
                                'cote_away': round(cotes['away'], 2)
                            })
                            nb_updates += 1

                    st.success(f"Cotes mises a jour pour {nb_updates} matchs!")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.info("Aucun match actif pour modifier les cotes.")

        st.markdown("---")

        # === SECTION 2: EMAILS ===
        st.markdown("#### 2. Gestion des Emails")

        # Verifier le mode
        from modules.database_manager import is_mode_officiel
        mode = is_mode_officiel()
        if mode:
            st.success("**Mode: OFFICIEL** - Les emails sont envoyes reellement")
        else:
            st.warning("**Mode: TEST** - Les emails sont simules (non envoyes)")

        # Tableau descriptif des emails
        st.markdown("""
        | Email | Destinataires | Contenu | Quand l'envoyer |
        |-------|--------------|---------|-----------------|
        | **Nouvelle Journee** | Tous les joueurs | 4 matchs + cotes + analyse Kingo + deadline | Quand les matchs de la semaine sont selectionnes |
        | **Synthese Paris** | Tous les joueurs | Recap des pronos de chacun + tendances 1N2 + jokers actifs | Apres la deadline (avant le 1er match) |
        | **Tableau Pronos** | Admin uniquement | Tableau complet des pronos + cotes + mises + jokers | Apres la deadline |
        | **Debrief Ironique** | Tous les joueurs | Classement de la semaine + commentaires humoristiques | Apres le dernier match (points calcules) |
        | **Bienvenue** | Nouvel inscrit | Message de bienvenue + regles du jeu | Automatique a la validation admin |
        | **Alerte Inscription** | Admin (Baggio) | Notification nouveau joueur inscrit | Automatique a l'inscription |
        """)

        st.markdown("---")

        col_email0, col_email1, col_email2, col_email3 = st.columns(4)

        with col_email0:
            st.markdown("**Nouvelle Journee**")
            st.caption("4 matchs + deadline")
            if st.button("ENVOYER NOUVELLE JOURNEE", type="primary", use_container_width=True):
                with st.spinner("Envoi des emails nouvelle journee..."):
                    try:
                        resultats, msg = envoyer_lancement_journee(semaine_selectionnee)
                        nb_envoyes = sum(1 for r in resultats if r['success'])
                        st.success(f"✅ {nb_envoyes}/{len(resultats)} email(s) envoye(s)")
                        with st.expander("Details"):
                            for r in resultats:
                                st.write(f"{'✓' if r['success'] else '✗'} {r['user']}: {r['message']}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)})")

        with col_email1:
            st.markdown("**Synthese des Paris**")
            st.caption("Recap pronos + tendances 1N2")
            if st.button("ENVOYER SYNTHESE PARIS", type="secondary", use_container_width=True):
                with st.spinner("Envoi des emails de synthese..."):
                    try:
                        resultats = envoyer_synthese_paris(semaine_selectionnee)
                        nb_envoyes = sum(1 for r in resultats if r['success'])
                        st.success(f"✅ {nb_envoyes}/{len(resultats)} email(s) envoye(s)")

                        with st.expander("Details des envois"):
                            for r in resultats:
                                if r['success']:
                                    st.write(f"✓ {r['user']}: {r['message']}")
                                else:
                                    st.write(f"✗ {r['user']}: {r['message']}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        with col_email2:
            st.markdown("**Tableau Pronos**")
            st.caption("Tous les pronos (admin)")
            if st.button("ENVOYER TABLEAU PRONOS", type="secondary", use_container_width=True):
                with st.spinner("Envoi du tableau des pronos..."):
                    try:
                        resultats = envoyer_tableau_pronos_admin(semaine_selectionnee)
                        nb_envoyes = sum(1 for r in resultats if r['success'])
                        st.success(f"✅ {nb_envoyes} email(s) envoye(s) aux admins")

                        for r in resultats:
                            if r['success']:
                                st.write(f"✓ {r['user']}: {r['message']}")
                            else:
                                st.write(f"✗ {r['user']}: {r['message']}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        with col_email3:
            st.markdown("**Debrief Ironique**")
            st.caption("Classement + commentaires")
            if st.button("ENVOYER DEBRIEF IRONIQUE", type="secondary", use_container_width=True):
                with st.spinner("Envoi du debrief ironique..."):
                    try:
                        resultats = envoyer_resultats_ironiques(semaine_selectionnee)
                        nb_envoyes = sum(1 for r in resultats if r['success'])
                        st.success(f"✅ {nb_envoyes}/{len(resultats)} email(s) envoye(s)")

                        with st.expander("Details des envois"):
                            for r in resultats:
                                if r['success']:
                                    st.write(f"✓ {r['user']}: {r['message']}")
                                else:
                                    st.write(f"✗ {r['user']}: {r['message']}")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")

        # Bouton test email
        st.markdown("---")
        if st.button("TESTER ENVOI EMAIL (admin)", use_container_width=True):
            with st.spinner("Test d'envoi..."):
                try:
                    from modules.notifier_st import send_email, get_base_template
                    test_html = get_base_template(
                        "<h2>Test Email</h2><p>Si vous recevez cet email, la configuration SMTP fonctionne.</p>",
                        "Test"
                    )
                    success, msg = send_email("elite.pronos.2@gmail.com", "Elite Pronos - Test Email", test_html)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

        st.markdown("---")

        # === SECTION 2b : ATTRIBUTION JOKERS DEFIS ===
        st.markdown("#### Attribution Jokers — Defis hebdomadaires")
        st.caption("A lancer apres le calcul des points. Attribue +1 joker VOL par defi reussi (sans doublon).")
        if st.button("🃏 ATTRIBUER JOKERS DEFIS", use_container_width=True):
            with st.spinner("Calcul des defis et attribution des jokers..."):
                try:
                    from modules.database_manager import attribuer_jokers_defis
                    attributions, msg = attribuer_jokers_defis(semaine_selectionnee, saison)
                    if attributions:
                        st.success(f"✅ {msg}")
                        for a in attributions:
                            st.write(f"🃏 {a['pseudo']} — Defi '{a['defi']}' → +1 joker VOL (stock : {a['jokers_vol_nouveau']})")
                    else:
                        st.info(f"Aucun nouveau joker a attribuer ({msg})")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

        st.markdown("---")

        # === SECTION 3: VALIDATION DES RESULTATS ===
        st.markdown("#### 3. Valider les Resultats")
        st.caption("Recupere les scores officiels depuis l'API et fige les resultats de la journee.")

        col_val1, col_val2, col_val3 = st.columns(3)

        with col_val1:
            if st.button("ACTUALISER SCORES", type="primary", use_container_width=True):
                with st.spinner("Mise a jour des scores..."):
                    from modules.database_manager import update_scores_from_api
                    success, message = update_scores_from_api(semaine_selectionnee, saison)
                    # Invalider le cache
                    st.cache_data.clear()

                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

        with col_val2:
            if st.button("VALIDER JOURNEE", use_container_width=True):
                with st.spinner("Recuperation des scores..."):
                    from modules.database_manager import valider_resultats_journee_supabase, calculer_gains_supabase
                    success, message = valider_resultats_journee_supabase(semaine_selectionnee, saison)

                if success:
                    st.success(f"✅ {message}")
                    with st.spinner("Calcul des points..."):
                        success_calc, msg_calc = calculer_gains_supabase(semaine_selectionnee, saison)
                        if success_calc:
                            st.success(f"✅ {msg_calc}")
                        else:
                            st.warning(f"Points: {msg_calc}")
                else:
                    st.error(f"❌ {message}")

        with col_val3:
            if st.button("Calendrier (reports)", use_container_width=True):
                with st.spinner("Verification des reports..."):
                    success, message = mettre_a_jour_calendrier_reports(saison)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")

        # Bouton FORCER RECALCUL (reset + recalcul complet)
        if st.button("FORCER RECALCUL POINTS", type="secondary", use_container_width=True):
            with st.spinner("Reset et recalcul de tous les points..."):
                try:
                    supabase = get_supabase()

                    # Recuperer les matchs termines de cette journee
                    matchs = supabase._request('GET',
                        f'matches?semaine_id=eq.{semaine_selectionnee}&saison_id=eq.{saison}&score_final_home=not.is.null&select=id'
                    ) or []

                    if not matchs:
                        st.warning("Aucun match termine pour cette journee")
                    else:
                        # Reset les points de toutes les predictions de ces matchs
                        match_ids = [m['id'] for m in matchs]
                        for mid in match_ids:
                            supabase._request('PATCH', f'predictions?match_id=eq.{mid}', {
                                'points_gagnes': None,
                                'is_score_exact': None
                            })

                        # Recalculer
                        from modules.database_manager import calculer_gains_supabase
                        success, msg = calculer_gains_supabase(semaine_selectionnee, saison)

                        st.cache_data.clear()

                        if success:
                            st.success(f"✅ Points recalcules: {msg}")
                        else:
                            st.error(f"❌ Erreur: {msg}")

                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

        # === MODIFICATION MANUELLE DES SCORES ===
        with st.expander("Modifier les scores des matchs (Manuel)"):
            st.caption("Saisir manuellement les scores finaux si l'API est incorrecte")

            # Recuperer matchs avec scores actuels
            matchs_scores = supabase._request('GET',
                f'matches?semaine_id=eq.{semaine_selectionnee}&saison_id=eq.{saison}&is_active=eq.true&select=id,equipe_home,equipe_away,score_final_home,score_final_away&order=id'
            ) or []

            if matchs_scores:
                for m in matchs_scores:
                    st.markdown(f"**{m['equipe_home']} vs {m['equipe_away']}**")

                    col_s1, col_s2, col_s3 = st.columns([2, 1, 2])

                    with col_s1:
                        score_home = st.number_input(
                            f"Score {m['equipe_home'][:10]}",
                            min_value=0,
                            max_value=15,
                            value=int(m.get('score_final_home') or 0),
                            step=1,
                            key=f"score_home_{m['id']}"
                        )

                    with col_s2:
                        st.markdown("<div style='text-align:center; padding-top:25px;'>-</div>", unsafe_allow_html=True)

                    with col_s3:
                        score_away = st.number_input(
                            f"Score {m['equipe_away'][:10]}",
                            min_value=0,
                            max_value=15,
                            value=int(m.get('score_final_away') or 0),
                            step=1,
                            key=f"score_away_{m['id']}"
                        )

                    # Stocker dans session_state
                    st.session_state[f"scores_to_save_{m['id']}"] = {
                        'home': score_home,
                        'away': score_away
                    }

                    st.markdown("---")

                # Bouton pour sauvegarder tous les scores
                if st.button("SAUVEGARDER LES SCORES", type="primary", use_container_width=True, key="btn_save_scores"):
                    nb_updates = 0
                    match_ids_updated = []

                    for m in matchs_scores:
                        scores = st.session_state.get(f"scores_to_save_{m['id']}")
                        if scores:
                            old_home = m.get('score_final_home')
                            old_away = m.get('score_final_away')

                            # Verifier si le score a change ou est nouveau
                            if scores['home'] > 0 or scores['away'] > 0:
                                if old_home != scores['home'] or old_away != scores['away']:
                                    supabase._request('PATCH', f'matches?id=eq.{m["id"]}', {
                                        'score_final_home': scores['home'],
                                        'score_final_away': scores['away'],
                                        'status': 'FINISHED'
                                    })
                                    nb_updates += 1
                                    match_ids_updated.append(m['id'])

                    if nb_updates > 0:
                        # Reset les points pour ces matchs
                        for mid in match_ids_updated:
                            supabase._request('PATCH', f'predictions?match_id=eq.{mid}', {
                                'points_gagnes': None,
                                'is_score_exact': None
                            })

                        # Recalculer les gains
                        from modules.database_manager import calculer_gains_supabase
                        calculer_gains_supabase(semaine_selectionnee, saison)

                        st.success(f"Scores mis a jour pour {nb_updates} matchs + points recalcules!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.info("Aucun score modifie.")
            else:
                st.info("Aucun match actif pour cette journee.")

        st.markdown("---")

        # === SECTION 4: BOT DEBRIEF SUR ACCUEIL ===
        st.markdown("#### 4. Debrief Bot sur Accueil")
        st.caption("Genere et affiche le compte-rendu ironique du Bot sur la page d'accueil.")

        if st.button("GENERER DEBRIEF ACCUEIL", use_container_width=True):
            try:
                import random

                # Recuperer le classement de la journee via Supabase
                # On recupere les predictions avec points_gagnes pour cette journee
                predictions = supabase._request('GET',
                    f'predictions?saison_id=eq.{saison}&select=user_id,points_gagnes'
                ) or []

                # Recuperer les utilisateurs actifs
                utilisateurs = supabase._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo') or []
                users_dict = {u['id']: u['pseudo'] for u in utilisateurs}

                # Calculer les totaux par joueur
                totaux = {}
                for p in predictions:
                    uid = p['user_id']
                    if uid in users_dict:
                        totaux[uid] = totaux.get(uid, 0) + (p.get('points_gagnes', 0) or 0)

                # Trier et prendre le top 5
                top5 = sorted([(users_dict[uid], total) for uid, total in totaux.items()], key=lambda x: x[1], reverse=True)[:5]

                # Generer le texte ironique
                phrases_intro = [
                    "Encore une semaine de drama footballistique !",
                    "Accrochez-vous, les resultats sont tombes...",
                    "Le verdict est sans appel cette semaine !",
                    "Qui a brille ? Qui s'est plante ? Voyons ca..."
                ]

                debrief_text = f"### Debrief J{semaine_selectionnee}\n\n"
                debrief_text += f"*{random.choice(phrases_intro)}*\n\n"

                if top5:
                    debrief_text += f"**Champion de la semaine:** @{top5[0][0]} avec {top5[0][1]} pts !\n\n"
                    if len(top5) > 1:
                        debrief_text += f"Mention speciale a @{top5[1][0]} ({top5[1][1]} pts) qui n'etait pas loin...\n"
                    if len(top5) >= 5:
                        debrief_text += f"\nEt une pensee emue pour @{top5[-1][0]} ({top5[-1][1]} pts). Courage, ca ira mieux la semaine prochaine !"

                # Sauvegarder dans app_settings (table Supabase)
                # Verifier si la cle existe
                existing = supabase._request('GET', 'app_settings?cle=eq.debrief_accueil')
                if existing and len(existing) > 0:
                    supabase._request('PATCH', 'app_settings?cle=eq.debrief_accueil', {'valeur': debrief_text})
                else:
                    supabase._request('POST', 'app_settings', {
                        'cle': 'debrief_accueil',
                        'valeur': debrief_text,
                        'description': 'Debrief Bot affiche sur accueil'
                    })

                st.success("✅ Debrief genere et publie sur l'accueil!")
                st.markdown("**Apercu:**")
                st.markdown(debrief_text)

            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

    # === ONGLET 4 : PROSPECTION ===
    with tab4:
        st.markdown("### Email de Prospection")
        st.caption("Envoyez l'email de lancement pour inviter de nouveaux joueurs.")

        st.markdown("""
        **Contenu de l'email :**
        - L'heritage de Gillou et la communaute
        - Presentation de la nouvelle application Elite Pronos
        - Les nouveautes (automatisation, classements en direct, esprit de groupe)
        - Lien d'inscription vers l'application
        """)

        st.markdown("---")

        # Zone de saisie des emails
        st.markdown("#### Destinataires")
        emails_text = st.text_area(
            "Saisissez les adresses email (une par ligne)",
            height=150,
            placeholder="ami1@gmail.com\nami2@gmail.com\nami3@gmail.com",
            key="prospection_emails"
        )

        # Option: envoyer aussi a tous les inscrits actifs
        envoyer_aux_actifs = st.checkbox(
            "Envoyer egalement a tous les joueurs actifs",
            value=False,
            key="prospection_actifs"
        )

        st.markdown("---")

        # Apercu
        with st.expander("Apercu de l'email"):
            from modules.notifier_st import email_prospection
            st.components.v1.html(email_prospection(), height=800, scrolling=True)

        # Bouton envoi
        col_send, col_test = st.columns(2)

        with col_test:
            if st.button("TEST (admin seul)", use_container_width=True):
                with st.spinner("Envoi test..."):
                    nb_ok, nb_err, details = envoyer_email_prospection(["elite.pronos.2@gmail.com"])
                    if nb_ok > 0:
                        st.success(f"Email test envoye a l'admin!")
                    else:
                        st.error(f"Echec: {details[0][2] if details else 'erreur inconnue'}")

        with col_send:
            if st.button("ENVOYER LA CAMPAGNE", type="primary", use_container_width=True):
                # Collecter les emails
                liste_emails = []

                # Emails saisis manuellement
                if emails_text:
                    liste_emails.extend([e.strip() for e in emails_text.strip().split('\n') if e.strip()])

                # Emails des joueurs actifs si coche
                if envoyer_aux_actifs:
                    from modules.database_manager import get_utilisateurs_emails
                    actifs = get_utilisateurs_emails()
                    for u in actifs:
                        if u.get('email') and u['email'] not in liste_emails:
                            liste_emails.append(u['email'])

                if not liste_emails:
                    st.warning("Aucun destinataire. Saisissez des emails ou cochez 'joueurs actifs'.")
                else:
                    with st.spinner(f"Envoi a {len(liste_emails)} destinataire(s)..."):
                        nb_ok, nb_err, details = envoyer_email_prospection(liste_emails)

                    st.success(f"Campagne terminee: {nb_ok} envoye(s), {nb_err} erreur(s)")

                    with st.expander("Details des envois"):
                        for email_addr, success, msg in details:
                            if success:
                                st.write(f"✓ {email_addr}: {msg}")
                            else:
                                st.write(f"✗ {email_addr}: {msg}")

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
