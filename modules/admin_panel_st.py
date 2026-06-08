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
    envoyer_lancement_journee,
    email_recap_reglement_admins,
    envoyer_relance_non_regles
)


@st.cache_data(ttl=60)
def get_utilisateurs_en_attente():
    """Recupere tous les utilisateurs en attente de validation"""
    supabase = get_supabase()
    users = supabase._request('GET', 'utilisateurs?statut=eq.en_attente&select=id,pseudo,email,prenom,telephone&order=id.desc') or []
    return [(u['id'], u['pseudo'], u.get('email'), u.get('prenom'), u.get('telephone')) for u in users]


@st.cache_data(ttl=120)
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
    is_admin.clear()
    get_nombre_admins.clear()
    get_tous_utilisateurs.clear()
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
    is_admin.clear()
    get_nombre_admins.clear()
    get_tous_utilisateurs.clear()
    try:
        from modules.database_manager import _fetch_is_admin
        _fetch_is_admin.clear()
    except Exception:
        pass
    return True


@st.cache_data(ttl=120)
def get_nombre_admins():
    """Retourne le nombre d'administrateurs"""
    supabase = get_supabase()
    result = supabase._request('GET', 'utilisateurs?is_admin=eq.true&select=id') or []
    return len(result)


@st.cache_data(ttl=60)
def get_tous_utilisateurs():
    """Recupere tous les utilisateurs avec statut admin"""
    supabase = get_supabase()
    users = supabase._request('GET', 'utilisateurs?select=id,pseudo,email,prenom,statut,is_admin,reglement_accepte&order=is_admin.desc,id.desc') or []
    return [(u['id'], u['pseudo'], u.get('email'), u.get('prenom'), u.get('statut'), u.get('is_admin', False), u.get('reglement_accepte', False)) for u in users]


def activer_compte(user_id):
    """Active le compte d'un utilisateur et envoie l'email de bienvenue"""
    from modules.database_manager import get_saison_actuelle
    get_utilisateurs_en_attente.clear()
    get_tous_utilisateurs.clear()
    supabase = get_supabase()
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'statut': 'Actif'})

    # Initialiser le stock de jokers si pas encore existant (3 DOUBLE + 2 VOL)
    saison_id = get_saison_actuelle()
    stock_existant = supabase._request('GET',
        f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}&select=id'
    ) or []
    if not stock_existant:
        supabase._request('POST', 'stock_jokers', {
            'utilisateur_id': user_id,
            'saison_id': saison_id,
            'joker_double': 3,
            'joker_vol': 2
        })

    # Envoyer l'email de bienvenue
    user_data = supabase._request('GET', f'utilisateurs?id=eq.{user_id}&select=pseudo,prenom,email')
    if user_data and user_data[0].get('email'):
        envoyer_email_bienvenue(user_data[0])

    return True


def suspendre_compte(user_id):
    """Suspend le compte d'un utilisateur"""
    supabase = get_supabase()
    supabase._request('PATCH', f'utilisateurs?id=eq.{user_id}', {'statut': 'En pause'})
    get_tous_utilisateurs.clear()
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
        get_tous_utilisateurs.clear()
        get_utilisateurs_en_attente.clear()
        is_admin.clear()
        get_nombre_admins.clear()
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
    tab3, tab1, tab2, tab4, tab5 = st.tabs(["Gestion Journee", "Inscriptions en attente", "Tous les utilisateurs", "Prospection", "🏆 Fin de Saison"])

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
    with tab1:
        st.markdown("---")
        st.markdown("### Relance reglement")

        # Calcul des non-regles actifs
        from modules.supabase_db import get_supabase as _get_sb
        _users_actifs = _get_sb()._request(
            'GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo,reglement_accepte'
        ) or []
        _non_regles = [u for u in _users_actifs if not u.get('reglement_accepte')]
        _regles = [u for u in _users_actifs if u.get('reglement_accepte')]

        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Reglement valide", len(_regles), help="Joueurs actifs avec reglement accepte")
        with col_stat2:
            st.metric("En attente", len(_non_regles), help="Joueurs actifs sans reglement valide")

        if _non_regles:
            # Calcul du countdown J1
            try:
                from modules.database_manager import get_countdown_j1
                countdown_j1 = get_countdown_j1()
                jours_avant_j1 = countdown_j1.get('days', 99) if countdown_j1 else 99
            except Exception:
                jours_avant_j1 = 99

            if jours_avant_j1 <= 7:
                alerte_j1 = f"⚠️ J1 dans **{jours_avant_j1} jour(s)** — relance recommandee !"
                st.warning(alerte_j1)
            else:
                st.info(f"J1 dans {jours_avant_j1} jour(s). La relance est prevue a J-7.")

            noms_non_regles = ', '.join(u['pseudo'] for u in _non_regles)
            st.caption(f"Non regles : {noms_non_regles}")

            if st.button(
                f"ENVOYER RELANCE ({len(_non_regles)} joueur(s))",
                type="primary",
                use_container_width=True,
                key="btn_relance_reglement"
            ):
                with st.spinner("Envoi des emails de relance..."):
                    nb_ok, nb_err, details = envoyer_relance_non_regles()
                if nb_err == 0:
                    st.success(f"✅ {nb_ok} email(s) de relance envoye(s) avec succes.")
                else:
                    st.warning(f"✅ {nb_ok} envoye(s), ⚠️ {nb_err} echec(s).")
        else:
            st.success("✅ Tous les joueurs actifs ont valide leur reglement !")

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

            # En-tête aligné avec st.columns (memes proportions que les lignes)
            COLS = [0.4, 1.3, 2.2, 0.4, 0.4, 0.4, 0.4]
            h = st.columns(COLS)
            labels = ["#", "Pseudo", "Email", "Actif", "Regle", "Admin", "Suppr"]
            colors = ["#D4AF37"] * 6 + ["#FF4444"]
            for col, lbl, col_color in zip(h, labels, colors):
                col.markdown(f"<span style='color:{col_color};font-size:0.7em;font-weight:bold;'>{lbl}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0 6px 0;border-color:#D4AF37;'>", unsafe_allow_html=True)

            # Liste des utilisateurs
            for user in all_users:
                user_id, pseudo, email, prenom, statut, user_is_admin, regle = user

                is_actif = statut == "Actif"
                is_admin_user = user_is_admin or False
                is_super = is_super_admin(pseudo)

                cols = st.columns(COLS)

                with cols[0]:
                    st.markdown(f"<span style='color:#FFF;font-size:0.75em;'>{user_id}</span>", unsafe_allow_html=True)

                with cols[1]:
                    st.markdown(f"<span style='color:#FFF;font-size:0.75em;'>{pseudo}</span>", unsafe_allow_html=True)

                with cols[2]:
                    st.markdown(f"<span style='color:#888;font-size:0.7em;'>{email or '-'}</span>", unsafe_allow_html=True)

                with cols[3]:
                    bg = "🟢" if is_actif else "🔴"
                    new_actif = st.checkbox(bg, value=is_actif, key=f"actif_{user_id}", label_visibility="collapsed")
                    if new_actif != is_actif:
                        activer_compte(user_id) if new_actif else suspendre_compte(user_id)
                        st.rerun()

                with cols[4]:
                    new_regle = st.checkbox("R", value=bool(regle), key=f"regle_{user_id}", label_visibility="collapsed")
                    if new_regle != bool(regle):
                        get_supabase().set_reglement_accepte(user_id, new_regle)
                        try:
                            email_recap_reglement_admins()
                        except Exception as e:
                            print(f"Erreur envoi recap reglement: {e}")
                        st.rerun()

                with cols[5]:
                    if is_admin_user:
                        st.markdown("👑", unsafe_allow_html=True)
                    current_user = get_current_user()
                    is_current_super = current_user and is_super_admin(current_user.get('pseudo', ''))
                    if is_current_super and not is_super:
                        new_admin = st.checkbox("Admin", value=is_admin_user, key=f"admin_{user_id}", label_visibility="collapsed")
                        if new_admin != is_admin_user:
                            promouvoir_admin(user_id) if new_admin else revoquer_admin(user_id)
                            st.rerun()

                with cols[6]:
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

            # === GROUPEMENT PAR CHAMPIONNAT ===
            def _balance_ratio(m):
                c_h = m.get('cote_home') or 3.0
                c_a = m.get('cote_away') or 3.0
                if c_h <= 0 or c_a <= 0:
                    return 99.0
                p_h, p_a = 1 / c_h, 1 / c_a
                return max(p_h, p_a) / min(p_h, p_a) if min(p_h, p_a) > 0 else 99.0

            # Ordre des championnats : Ligue 1 toujours en tete
            CHAMP_ORDRE = {
                'Ligue 1': 0, 'FL1': 0,
                'Premier League': 1,
                'La Liga': 2,
                'Serie A': 3,
                'Bundesliga': 4,
            }
            CHAMP_FLAGS = {
                'Ligue 1': '🇫🇷', 'FL1': '🇫🇷',
                'Premier League': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
                'La Liga': '🇪🇸',
                'Serie A': '🇮🇹',
                'Bundesliga': '🇩🇪',
            }

            # Grouper par championnat
            from collections import defaultdict
            groupes = defaultdict(list)
            for m in tous_matchs:
                groupes[m.get('championnat', 'Autre')].append(m)

            # Trier les championnats (Ligue 1 en premier)
            championnats_tries = sorted(
                groupes.keys(),
                key=lambda c: (CHAMP_ORDRE.get(c, 9), c)
            )

            # Legende
            st.markdown(
                "<div style='font-size:0.75em;color:#888;margin-bottom:8px;'>"
                "🟢 Équilibré &nbsp;|&nbsp; 🟡 Correct &nbsp;|&nbsp; 🔴 Favori marqué</div>",
                unsafe_allow_html=True
            )

            for champ in championnats_tries:
                matchs_champ = sorted(groupes[champ], key=_balance_ratio)
                flag = CHAMP_FLAGS.get(champ, '🌍')
                nb_champ = len(matchs_champ)
                nb_actifs_champ = sum(1 for m in matchs_champ if m.get('is_active'))

                # En-tete du championnat
                st.markdown(
                    f"<div style='background:#001f3d;border-left:4px solid #D4AF37;"
                    f"padding:6px 12px;margin:12px 0 4px 0;border-radius:4px;"
                    f"display:flex;justify-content:space-between;align-items:center;'>"
                    f"<span style='color:#D4AF37;font-weight:bold;font-size:0.9em;'>"
                    f"{flag} {champ}</span>"
                    f"<span style='color:#888;font-size:0.75em;'>"
                    f"{nb_actifs_champ} actif(s) / {nb_champ} match(s)</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                for m in matchs_champ:
                    is_actif = m.get('is_active', False)
                    border_color = "#00FF00" if is_actif else "#444"
                    bg = "#002040" if is_actif else "#001529"

                    # Date
                    date_info = ""
                    if m.get('date_match'):
                        try:
                            dt = datetime.fromisoformat(m['date_match'].replace('Z', '+00:00'))
                            jours = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
                            date_info = f"{jours[dt.weekday()]} {dt.day}/{dt.month} {dt.hour}h{dt.minute:02d}"
                        except:
                            date_info = ""

                    # Cotes et equilibre
                    c_h = m.get('cote_home') or 0
                    c_n = m.get('cote_draw') or 0
                    c_a = m.get('cote_away') or 0
                    ratio = _balance_ratio(m)
                    if ratio < 1.5:
                        eq_icon, eq_color = "🟢", "#4CAF50"
                    elif ratio < 2.5:
                        eq_icon, eq_color = "🟡", "#FFD700"
                    else:
                        eq_icon, eq_color = "🔴", "#FF4444"

                    col_m1, col_m2 = st.columns([4, 0.5])
                    with col_m1:
                        st.markdown(
                            f"<div style='background:{bg};border-left:4px solid {border_color};"
                            f"padding:7px 10px;margin:2px 0;border-radius:5px;font-size:0.8em;'>"
                            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                            f"<span style='color:#FFF;font-weight:bold;'>{eq_icon} {m['equipe_home']} vs {m['equipe_away']}</span>"
                            f"<span style='color:#888;font-size:0.8em;'>{date_info}</span>"
                            f"</div>"
                            f"<div style='display:flex;gap:12px;margin-top:3px;font-size:0.85em;'>"
                            f"<span style='color:#D4AF37;'>1: {c_h:.2f}</span>"
                            f"<span style='color:#D4AF37;'>N: {c_n:.2f}</span>"
                            f"<span style='color:#D4AF37;'>2: {c_a:.2f}</span>"
                            f"<span style='color:{eq_color};margin-left:6px;'>ratio {ratio:.1f}</span>"
                            f"</div></div>",
                            unsafe_allow_html=True
                        )
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
                    st.session_state['kingo_a_pronostique'] = True
                else:
                    st.warning("Kingo n'a pas pu pronostiquer.")
                st.rerun()

            # Bouton email nouvelle journee — uniquement apres que Kingo a pronostique
            if st.session_state.get('kingo_a_pronostique'):
                st.info("✅ Kingo a pronostiqué. Vérifiez la sélection puis envoyez l'email de lancement.")
                if st.button("📧 ENVOYER EMAIL NOUVELLE JOURNÉE", use_container_width=True):
                    with st.spinner("Envoi des emails nouvelle journee..."):
                        try:
                            resultats, _ = envoyer_lancement_journee(semaine_selectionnee)
                            nb_ok = sum(1 for r in resultats if r['success'])
                            st.success(f"📧 Email nouvelle journee envoye a {nb_ok}/{len(resultats)} joueur(s)")
                            st.session_state['kingo_a_pronostique'] = False
                        except Exception as e:
                            st.warning(f"⚠️ Erreur envoi email: {str(e)}")
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

        # === VERIFICATION AUTOMATIQUE DES SCORES ===
        if st.button("🔍 VERIFIER LES SCORES (double controle)", use_container_width=True):
            with st.spinner("Verification des scores en cours..."):
                from modules.database_manager import verifier_scores_vs_api
                resultats, msg_verif = verifier_scores_vs_api(semaine_selectionnee, saison)

            if not resultats:
                st.warning(f"Verification impossible : {msg_verif}")
            else:
                nb_anomalies = sum(1 for r in resultats if r['statut'] == 'anomalie')
                nb_ok = sum(1 for r in resultats if r['statut'] == 'ok')
                nb_inconnus = sum(1 for r in resultats if r['statut'] == 'non_trouve')

                if nb_anomalies == 0:
                    st.success(f"✅ Tous les scores sont corrects ({nb_ok} matchs verifies)")
                else:
                    st.error(f"⚠️ {nb_anomalies} anomalie(s) detectee(s) sur {len(resultats)} matchs")

                for r in resultats:
                    home = r['equipe_home']
                    away = r['equipe_away']
                    s_db = r['score_db']
                    s_api = r['score_api']
                    statut = r['statut']

                    if statut == 'ok':
                        st.markdown(
                            f"✅ **{home} {s_db[0]}-{s_db[1]} {away}** — score confirme par l'API",
                        )
                    elif statut == 'anomalie':
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.markdown(
                                f"⚠️ **{home} vs {away}**  \n"
                                f"&nbsp;&nbsp;• En base : **{s_db[0]}-{s_db[1]}**  \n"
                                f"&nbsp;&nbsp;• API officielle : **{s_api[0]}-{s_api[1]}**",
                                unsafe_allow_html=True
                            )
                        with col_b:
                            if st.button(f"Corriger", key=f"fix_{r['match_id']}"):
                                supabase = get_supabase()
                                supabase._request('PATCH', f"matches?id=eq.{r['match_id']}", {
                                    'score_final_home': s_api[0],
                                    'score_final_away': s_api[1],
                                    'status': 'FINISHED'
                                })
                                supabase._request('PATCH', f"predictions?match_id=eq.{r['match_id']}", {
                                    'points_gagnes': None,
                                    'is_score_exact': None
                                })
                                from modules.database_manager import calculer_gains_supabase
                                calculer_gains_supabase(semaine_selectionnee, saison)
                                st.cache_data.clear()
                                st.success(f"Score corrige : {s_api[0]}-{s_api[1]} — points recalcules")
                                st.rerun()
                    else:
                        eurosport_url = f"https://www.eurosport.fr/football/ligue-1/{saison}-{saison+1}/calendrier-resultats.shtml"
                        st.markdown(
                            f"❓ **{home} vs {away}** — non trouve dans l'API  \n"
                            f"[Verifier sur Eurosport ↗]({eurosport_url})",
                            unsafe_allow_html=False
                        )

        st.markdown("---")

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

        # === SECTION 3b: ANNULER UN MATCH REPORTE ===
        st.markdown("#### 3b. Annuler un Match Reporte")
        st.caption("Marque un match comme ANNULE. Les joueurs ne gagnent ni ne perdent de points sur ce match. 0 pts pour tous les pronos.")

        matchs_annulables = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_selectionnee}&saison_id=eq.{saison}&is_active=eq.true&status=neq.FINISHED&select=id,equipe_home,equipe_away,status&order=id'
        ) or []
        # Exclure ceux déjà CANCELLED
        matchs_annulables = [m for m in matchs_annulables if m.get('status') != 'CANCELLED']

        # Afficher les matchs déjà annulés
        matchs_annules_existants = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_selectionnee}&saison_id=eq.{saison}&status=eq.CANCELLED&select=id,equipe_home,equipe_away&order=id'
        ) or []
        if matchs_annules_existants:
            st.warning(f"**{len(matchs_annules_existants)} match(s) deja annule(s) cette journee :**")
            for ma in matchs_annules_existants:
                col_ma1, col_ma2 = st.columns([4, 1])
                with col_ma1:
                    st.markdown(f"❌ ~~{ma['equipe_home']} vs {ma['equipe_away']}~~ — ANNULE (0 pts)")
                with col_ma2:
                    if st.button("Restaurer", key=f"restore_{ma['id']}"):
                        supabase._request('PATCH', f'matches?id=eq.{ma["id"]}', {
                            'status': 'SCHEDULED',
                            'is_active': True
                        })
                        supabase._request('PATCH', f'predictions?match_id=eq.{ma["id"]}', {
                            'points_gagnes': None,
                            'is_score_exact': None
                        })
                        st.cache_data.clear()
                        st.success("Match restaure. Recalcule les points si necessaire.")
                        st.rerun()

        if not matchs_annulables:
            if not matchs_annules_existants:
                st.info("Aucun match annulable pour cette journee (tous termines ou deja annules).")
        else:
            options_annul = {f"{m['equipe_home']} vs {m['equipe_away']}  (id={m['id']})": m['id'] for m in matchs_annulables}
            match_annul_label = st.selectbox("Choisir le match a annuler", list(options_annul.keys()), key="select_annul")
            match_annul_id = options_annul[match_annul_label]

            col_annul1, col_annul2 = st.columns([3, 1])
            with col_annul1:
                st.caption("Cette action est reversible via le bouton 'Restaurer'.")
            with col_annul2:
                if st.button("ANNULER CE MATCH", type="secondary", use_container_width=True, key="btn_annuler_match"):
                    # Marquer CANCELLED + desactiver
                    supabase._request('PATCH', f'matches?id=eq.{match_annul_id}', {
                        'status': 'CANCELLED',
                        'is_active': False
                    })
                    # 0 pts sur toutes les predictions
                    supabase._request('PATCH', f'predictions?match_id=eq.{match_annul_id}', {
                        'points_gagnes': 0,
                        'is_score_exact': False
                    })
                    st.cache_data.clear()
                    st.success(f"Match annule : {match_annul_label}. Tous les pronos -> 0 pts.")
                    st.rerun()

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

    # === ONGLET 5 : FIN DE SAISON ===
    with tab5:
        st.markdown("### Clôturer la Saison")
        st.caption("Fige le classement final, enregistre le palmarès et archive la saison.")

        saison_id = get_saison_actuelle()
        saison_label = get_saison_label(saison_id)
        supabase_cloture = get_supabase()

        st.info(f"Saison active : **{saison_label}** (id: {saison_id})")

        # Calculer le classement final
        all_predictions = supabase_cloture._request('GET',
            f'predictions?saison_id=eq.{saison_id}&select=user_id,points_gagnes,is_score_exact'
        ) or []

        utilisateurs_actifs = supabase_cloture.get_all_utilisateurs(statut='Actif')
        user_map = {u['id']: u['pseudo'] for u in utilisateurs_actifs}

        # Agréger stats par joueur
        user_stats_final = {}
        for p in all_predictions:
            uid = p['user_id']
            if uid not in user_stats_final:
                user_stats_final[uid] = {'points': 0, 'bons': 0, 'exacts': 0}
            pts = p.get('points_gagnes') or 0
            user_stats_final[uid]['points'] += pts
            if pts > 0:
                user_stats_final[uid]['bons'] += 1
            if p.get('is_score_exact'):
                user_stats_final[uid]['exacts'] += 1

        # Compter les Grand Chelem par joueur (semaines MVP)
        from modules.database_manager import get_all_mvp_saison
        mvps = get_all_mvp_saison(saison_id) or {}
        grand_chelem_par_user = {}
        for semaine, mvp_data in mvps.items():
            if mvp_data and mvp_data.get('user_id'):
                uid = mvp_data['user_id']
                grand_chelem_par_user[uid] = grand_chelem_par_user.get(uid, 0) + 1

        # Construire classement final trié
        classement_final = []
        for uid, stats in user_stats_final.items():
            if uid in user_map:
                classement_final.append({
                    'user_id': uid,
                    'pseudo': user_map[uid],
                    'points_total': round(stats['points'], 2),
                    'bonnes_predictions': stats['bons'],
                    'scores_exacts': stats['exacts'],
                    'grand_chelem': grand_chelem_par_user.get(uid, 0)
                })
        classement_final.sort(key=lambda x: x['points_total'], reverse=True)

        if not classement_final:
            st.warning("Aucune donnée de prédiction trouvée pour cette saison.")
        else:
            st.markdown(f"**Classement final — {saison_label}** ({len(classement_final)} joueurs)")

            # Aperçu podium
            cols = st.columns(min(3, len(classement_final)))
            medailles = ["🥇", "🥈", "🥉"]
            for i, col in enumerate(cols):
                if i < len(classement_final):
                    j = classement_final[i]
                    col.metric(
                        label=f"{medailles[i]} {j['pseudo']}",
                        value=f"{j['points_total']} pts",
                        delta=f"{j['scores_exacts']} exacts · {j['grand_chelem']} GC"
                    )

            # Tableau complet
            with st.expander("Voir le classement complet"):
                for idx, j in enumerate(classement_final, 1):
                    st.write(f"**{idx}.** {j['pseudo']} — {j['points_total']} pts | {j['bonnes_predictions']} bons | {j['scores_exacts']} exacts | {j['grand_chelem']} Grand Chelem")

            st.markdown("---")
            st.warning("⚠️ Cette action est irréversible : elle archive la saison et enregistre le palmarès définitif.")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                confirmer = st.checkbox(f"Je confirme la clôture de la saison {saison_label}")
            with col_btn2:
                if confirmer and st.button("🏆 Clôturer la saison", type="primary"):
                    with st.spinner("Enregistrement du palmarès..."):
                        erreurs = []
                        for place, joueur in enumerate(classement_final, 1):
                            payload = {
                                'saison_id': saison_id,
                                'user_id': joueur['user_id'],
                                'place': place,
                                'points_total': joueur['points_total'],
                                'bonnes_predictions': joueur['bonnes_predictions'],
                                'scores_exacts': joueur['scores_exacts'],
                                'grand_chelem': joueur['grand_chelem']
                            }
                            res = supabase_cloture._request('POST', 'palmares', payload)
                            if res is None:
                                erreurs.append(joueur['pseudo'])

                        # Archiver la saison
                        supabase_cloture._request('PATCH',
                            f'saisons?annee_debut=eq.{saison_id}',
                            {'is_active': False}
                        )

                    if erreurs:
                        st.error(f"Erreurs sur : {', '.join(erreurs)}")
                    else:
                        st.success(f"✅ Saison {saison_label} clôturée ! Palmarès enregistré pour {len(classement_final)} joueurs.")
                        st.balloons()

        st.markdown("---")

        # === LANCEMENT NOUVELLE SAISON ===
        st.markdown("### Lancer la nouvelle saison")
        st.caption("Remet tous les joueurs en attente de validation et envoie l'email d'annonce.")

        nouvelle_saison_id = saison_id + 1
        nouvelle_saison_label = get_saison_label(nouvelle_saison_id)

        # Récupérer le champion de la saison clôturée (place 1 dans palmares)
        palmares_data = supabase_cloture._request('GET',
            f'palmares?saison_id=eq.{saison_id}&place=eq.1&select=user_id'
        ) or []
        champion_pseudo = None
        if palmares_data:
            champion_user = supabase_cloture._request('GET',
                f'utilisateurs?id=eq.{palmares_data[0]["user_id"]}&select=pseudo'
            ) or []
            if champion_user:
                champion_pseudo = champion_user[0]['pseudo']

        st.info(f"Nouvelle saison : **{nouvelle_saison_label}**")
        if champion_pseudo:
            st.success(f"Champion sortant : 🏆 **{champion_pseudo}**")

        col_nl1, col_nl2 = st.columns(2)
        with col_nl1:
            confirmer_nl = st.checkbox(f"Je lance officiellement la saison {nouvelle_saison_label}")
        with col_nl2:
            if confirmer_nl and st.button("🚀 Lancer la nouvelle saison", type="primary"):
                with st.spinner("Remise à zéro des joueurs et envoi des emails..."):

                    # Remettre tous les joueurs non-admin en en_attente
                    tous_joueurs = supabase_cloture._request('GET',
                        'utilisateurs?select=id,pseudo,is_admin&statut=eq.Actif'
                    ) or []

                    nb_reset = 0
                    for joueur in tous_joueurs:
                        if not joueur.get('is_admin'):
                            supabase_cloture._request('PATCH',
                                f'utilisateurs?id=eq.{joueur["id"]}',
                                {'statut': 'en_attente', 'reglement_accepte': False}
                            )
                            nb_reset += 1

                    # Activer la nouvelle saison
                    supabase_cloture._request('PATCH',
                        f'saisons?annee_debut=eq.{nouvelle_saison_id}',
                        {'is_active': True}
                    )

                    # Envoyer les emails
                    from modules.notifier_st import envoyer_email_nouvelle_saison
                    nb_ok, nb_err, details_emails = envoyer_email_nouvelle_saison(
                        champion_pseudo=champion_pseudo,
                        saison_label_precedente=saison_label,
                        nouvelle_saison_label=nouvelle_saison_label
                    )

                st.success(f"✅ {nb_reset} joueurs remis en attente · {nb_ok} emails envoyés · {nb_err} erreurs")
                st.info("⚠️ Dernière étape : demande à Claude Code de basculer SAISON_FORCEE = 2026 dans database_manager.py")

                with st.expander("Détail des emails"):
                    for d in details_emails:
                        icon = "✓" if d['success'] else "✗"
                        st.write(f"{icon} {d['pseudo']} ({d['email']})")

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
