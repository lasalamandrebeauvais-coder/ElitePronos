"""
Module Pronostics Streamlit pour Elite Pronos
Saisie des pronostics de la semaine - Version Supabase
"""
import streamlit as st
import os
from datetime import datetime, timedelta

# Import Supabase
from modules.supabase_db import get_supabase
from modules.database_manager import get_saison_actuelle

# Chemins
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

# Budget hebdomadaire
BUDGET_TOTAL = 100
MISE_MIN = 10
MISE_MAX = 60


def get_matchs_semaine():
    """
    Recupere les 4 matchs de la semaine en cours depuis Supabase
    """
    supabase = get_supabase()
    saison_id = get_saison_actuelle()

    try:
        # Recuperer la journee courante depuis la table saisons
        saisons = supabase._request('GET', 'saisons?is_active=eq.true&select=journee_courante')
        if saisons and len(saisons) > 0:
            journee_courante = saisons[0].get('journee_courante', 1)
        else:
            journee_courante = 1

        # Recuperer les matchs de cette journee
        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{journee_courante}&select=id,championnat,equipe_home,equipe_away,cote_home,cote_draw,cote_away,date_match,score_final_home&order=id&limit=4'
        ) or []

        # Convertir au format tuple pour compatibilite
        result = []
        for m in matchs:
            result.append((
                m['id'],
                m.get('championnat', 'FL1'),
                m['equipe_home'],
                m['equipe_away'],
                m.get('cote_home', 2.0),
                m.get('cote_draw', 3.0),
                m.get('cote_away', 2.0),
                m.get('date_match', '')
            ))

        return result

    except Exception as e:
        print(f"Erreur get_matchs_semaine: {e}")
        return []


def get_pronos_existants(user_id):
    """Recupere les pronostics deja saisis par l'utilisateur depuis Supabase"""
    supabase = get_supabase()
    saison_id = get_saison_actuelle()

    try:
        # Recuperer la journee courante
        saisons = supabase._request('GET', 'saisons?is_active=eq.true&select=journee_courante')
        if saisons and len(saisons) > 0:
            journee_courante = saisons[0].get('journee_courante', 1)
        else:
            return {}

        # Recuperer les match_ids de cette journee
        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{journee_courante}&select=id'
        ) or []

        if not matchs:
            return {}

        match_ids = [m['id'] for m in matchs]
        match_ids_str = ','.join(map(str, match_ids))

        # Recuperer les predictions
        predictions = supabase._request('GET',
            f'predictions?user_id=eq.{user_id}&match_id=in.({match_ids_str})&select=match_id,score_prono_home,score_prono_away,mise_points'
        ) or []

        pronos = {}
        for p in predictions:
            pronos[p['match_id']] = {
                'home': p['score_prono_home'],
                'away': p['score_prono_away'],
                'mise': p['mise_points']
            }

        return pronos

    except Exception as e:
        print(f"Erreur get_pronos_existants: {e}")
        return {}


def get_joker_semaine(user_id):
    """Recupere le joker utilise cette semaine depuis Supabase
    Retourne un dict avec type_joker, id, cible_vol_id ou None
    """
    supabase = get_supabase()

    try:
        saisons = supabase._request('GET', 'saisons?is_active=eq.true&select=journee_courante')
        if saisons and len(saisons) > 0:
            journee_courante = saisons[0].get('journee_courante', 1)
        else:
            return None

        joker = supabase._request('GET',
            f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{journee_courante}&select=id,type_joker,cible_vol_id&limit=1'
        )

        if joker and len(joker) > 0:
            return {
                'id': joker[0].get('id'),
                'type': joker[0].get('type_joker'),
                'cible_id': joker[0].get('cible_vol_id')
            }
        return None

    except Exception as e:
        print(f"Erreur get_joker_semaine: {e}")
        return None


def sauvegarder_pronostics(user_id, pronos_data, joker_type, cible_vol_id=None, joker_ancien=None):
    """
    Sauvegarde les pronostics dans Supabase
    pronos_data: dict {match_id: {'home': int, 'away': int, 'mise': int}}
    cible_vol_id: ID du joueur cible pour le joker VOL
    joker_ancien: dict avec l'ancien joker {'id', 'type', 'cible_id'} ou None
    """
    supabase = get_supabase()
    saison_id = get_saison_actuelle()

    try:
        # Recuperer la journee courante
        saisons = supabase._request('GET', 'saisons?is_active=eq.true&select=journee_courante')
        if saisons and len(saisons) > 0:
            journee_courante = saisons[0].get('journee_courante', 1)
        else:
            return False, "Erreur: journee courante non trouvee"

        # Supprimer les anciens pronostics de cet utilisateur pour ces matchs
        match_ids = list(pronos_data.keys())
        for match_id in match_ids:
            supabase._request('DELETE',
                f'predictions?user_id=eq.{user_id}&match_id=eq.{match_id}'
            )

        # Inserer les nouveaux pronostics
        for match_id, data in pronos_data.items():
            pred_data = {
                'user_id': user_id,
                'match_id': match_id,
                'saison_id': saison_id,
                'score_prono_home': data['home'],
                'score_prono_away': data['away'],
                'mise_points': data['mise'],
                'points_gagnes': 0
            }
            result = supabase._request('POST', 'predictions', pred_data)
            if not result:
                return False, f"Erreur lors de l'enregistrement du match {match_id}"

        # Gestion des jokers avec mise a jour du stock
        stock = supabase.get_stock_jokers(user_id, saison_id)
        if not stock:
            stock = {'joker_double': 3, 'joker_vol': 2}

        # Convertir le type du nouveau joker pour comparaison
        nouveau_type = None
        if joker_type == "DOUBLE":
            nouveau_type = "DOUBLE"
        elif joker_type == "VOLE":
            nouveau_type = "VOL"

        ancien_type = joker_ancien['type'] if joker_ancien else None

        # Si le joker a change
        if ancien_type != nouveau_type:
            # Restituer l'ancien joker au stock et supprimer l'historique
            if joker_ancien:
                if ancien_type == "DOUBLE":
                    supabase._request('PATCH',
                        f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}',
                        {'joker_double': stock['joker_double'] + 1}
                    )
                    stock['joker_double'] += 1
                elif ancien_type == "VOL":
                    supabase._request('PATCH',
                        f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}',
                        {'joker_vol': stock['joker_vol'] + 1}
                    )
                    stock['joker_vol'] += 1
                # Supprimer l'ancien historique
                supabase._request('DELETE', f'jokers_historique?id=eq.{joker_ancien["id"]}')

            # Appliquer le nouveau joker
            if nouveau_type == "DOUBLE" and stock.get('joker_double', 0) > 0:
                supabase._request('PATCH',
                    f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}',
                    {'joker_double': stock['joker_double'] - 1}
                )
                supabase._request('POST', 'jokers_historique', {
                    'utilisateur_id': user_id,
                    'semaine_id': journee_courante,
                    'saison_id': saison_id,
                    'type_joker': 'DOUBLE'
                })
            elif nouveau_type == "VOL" and stock.get('joker_vol', 0) > 0 and cible_vol_id:
                supabase._request('PATCH',
                    f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}',
                    {'joker_vol': stock['joker_vol'] - 1}
                )
                supabase._request('POST', 'jokers_historique', {
                    'utilisateur_id': user_id,
                    'semaine_id': journee_courante,
                    'saison_id': saison_id,
                    'type_joker': 'VOL',
                    'cible_vol_id': cible_vol_id
                })

        # Si meme type VOL mais cible differente, juste mettre a jour la cible
        elif ancien_type == "VOL" and nouveau_type == "VOL" and joker_ancien and cible_vol_id:
            if joker_ancien.get('cible_id') != cible_vol_id:
                supabase._request('PATCH',
                    f'jokers_historique?id=eq.{joker_ancien["id"]}',
                    {'cible_vol_id': cible_vol_id}
                )

        return True, "Pronostics enregistres avec succes!"

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def get_championnat_nom(code):
    """Retourne le nom complet du championnat"""
    championnats = {
        'FL1': 'Ligue 1',
        'PL': 'Premier League',
        'PD': 'La Liga',
        'SA': 'Serie A',
        'BL1': 'Bundesliga'
    }
    return championnats.get(code, code)


def get_deadline_pronostics():
    """
    Retourne la date limite pour soumettre les pronostics
    = date du premier match de la semaine - 1 heure
    """
    supabase = get_supabase()
    saison_id = get_saison_actuelle()

    try:
        saisons = supabase._request('GET', 'saisons?is_active=eq.true&select=journee_courante')
        if saisons and len(saisons) > 0:
            journee_courante = saisons[0].get('journee_courante', 1)
        else:
            return None

        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{journee_courante}&select=date_match&order=date_match&limit=1'
        )

        if matchs and len(matchs) > 0 and matchs[0].get('date_match'):
            date_str = matchs[0]['date_match']
            try:
                # Format ISO
                first_match = datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
            except:
                try:
                    first_match = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                except:
                    return None
            return first_match - timedelta(hours=1)
        return None

    except Exception as e:
        print(f"Erreur get_deadline: {e}")
        return None


def get_countdown_pronostics():
    """
    Retourne le temps restant avant la deadline
    """
    deadline = get_deadline_pronostics()
    if not deadline:
        return None

    now = datetime.now()
    diff = deadline - now

    if diff.total_seconds() <= 0:
        return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0, 'expired': True}

    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'expired': False
    }


def afficher_pronostics(user):
    """Affiche l'interface de saisie des pronostics - Version Supabase"""

    pronos_existants = get_pronos_existants(user['id'])
    mode_edition = st.session_state.get('mode_edition_pronos', False)

    # Header
    col_back, col_title, col_mascot, col_countdown = st.columns([0.6, 2.5, 0.8, 2])
    with col_back:
        if st.button("◀", help="Retour", use_container_width=True):
            st.session_state.dashboard_section = None
            st.session_state.mode_edition_pronos = False
            st.rerun()
    with col_title:
        st.markdown("### Pronostics")
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo pronostics.png")
        if os.path.exists(mascot_path):
            from PIL import Image
            mascot_img = Image.open(mascot_path)
            st.image(mascot_img, width=70)

    countdown = get_countdown_pronostics()
    with col_countdown:
        if countdown and not countdown.get('expired'):
            st.markdown(f"""
            <div style="text-align: right; color: #FFD700; font-size: 0.9em;">
                <b>{countdown['days']}j {countdown['hours']}h {countdown['minutes']}m</b>
            </div>
            """, unsafe_allow_html=True)
        elif countdown and countdown.get('expired'):
            st.markdown("<div style='text-align: right; color: #FF4444;'>CLOS</div>", unsafe_allow_html=True)

    matchs = get_matchs_semaine()
    if not matchs:
        st.warning("Aucun match disponible pour cette journee.")
        return

    # SI PRONOS VALIDES
    if pronos_existants and not mode_edition:
        st.markdown("### Vos pronostics valides")

        for match in matchs:
            match_id, championnat, home, away, cote_h, cote_n, cote_a, date_match = match
            if match_id in pronos_existants:
                p = pronos_existants[match_id]
                st.markdown(f"""
                <div style="
                    background: #0A183D;
                    border: 1px solid #00FF00;
                    border-radius: 8px;
                    padding: 10px;
                    margin: 5px 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <span style="color: #FFFFFF;">{home}</span>
                    <span style="color: #4488FF; font-weight: bold; font-size: 1.2em;">{p['home']} - {p['away']}</span>
                    <span style="color: #FFFFFF;">{away}</span>
                    <span style="color: #00FF00; font-weight: bold;">{p['mise']} pts</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")
        if st.button("MODIFIER MES PRONOSTICS", type="secondary", use_container_width=True):
            st.session_state.mode_edition_pronos = True
            st.session_state.pronos = pronos_existants.copy()
            st.rerun()
        return

    # MODE SAISIE
    if 'pronos' not in st.session_state or not st.session_state.pronos:
        st.session_state.pronos = pronos_existants if pronos_existants else {}
    if 'joker_selected' not in st.session_state:
        st.session_state.joker_selected = "AUCUN"
    if 'joker_cible_id' not in st.session_state:
        st.session_state.joker_cible_id = None

    total_mise = 0
    pronos_valides = True

    for i in range(0, len(matchs), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            if i + j < len(matchs):
                match = matchs[i + j]
                match_id, championnat, home, away, cote_h, cote_n, cote_a, date_match = match

                if match_id not in st.session_state.pronos:
                    st.session_state.pronos[match_id] = {'home': 0, 'away': 0, 'mise': 25}

                with col:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #0A183D 0%, #001529 100%);
                        border: 1px solid #D4AF37;
                        border-radius: 10px;
                        padding: 10px;
                        margin-bottom: 5px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1; text-align: center;">
                                <div style="color: #FFFFFF; font-weight: bold; font-size: 0.9em;">{home}</div>
                                <div style="color: #FF0000; font-size: 0.9em; font-weight: bold;">{cote_h:.2f}</div>
                            </div>
                            <div style="color: #D4AF37; font-weight: bold; padding: 0 5px;">VS</div>
                            <div style="flex: 1; text-align: center;">
                                <div style="color: #FFFFFF; font-weight: bold; font-size: 0.9em;">{away}</div>
                                <div style="color: #FF0000; font-size: 0.9em; font-weight: bold;">{cote_a:.2f}</div>
                            </div>
                        </div>
                        <div style="text-align: center; color: #FF0000; font-size: 0.8em; margin-top: 3px;">
                            N: {cote_n:.2f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    sc1, sc2, sc3 = st.columns([1, 0.5, 1])
                    with sc1:
                        score_home = st.number_input(
                            f"H{match_id}", min_value=0, max_value=9,
                            value=st.session_state.pronos[match_id]['home'],
                            key=f"h_{match_id}", label_visibility="collapsed"
                        )
                        st.session_state.pronos[match_id]['home'] = score_home
                    with sc2:
                        st.markdown("<div style='text-align:center; padding-top:5px; color:#0066FF; font-size:1.5em; font-weight:bold;'>-</div>", unsafe_allow_html=True)
                    with sc3:
                        score_away = st.number_input(
                            f"A{match_id}", min_value=0, max_value=9,
                            value=st.session_state.pronos[match_id]['away'],
                            key=f"a_{match_id}", label_visibility="collapsed"
                        )
                        st.session_state.pronos[match_id]['away'] = score_away

                    mise = st.number_input(
                        f"M{match_id}", min_value=MISE_MIN, max_value=MISE_MAX,
                        value=st.session_state.pronos[match_id]['mise'],
                        step=5, key=f"m_{match_id}", label_visibility="collapsed"
                    )
                    st.session_state.pronos[match_id]['mise'] = mise
                    st.markdown(f"<div style='text-align:center; color:#00FF00; font-size: 1em; font-weight: bold;'>{mise} pts</div>", unsafe_allow_html=True)

                    total_mise += st.session_state.pronos[match_id]['mise']

    # BUDGET
    st.markdown("---")
    budget_ok = total_mise == BUDGET_TOTAL
    budget_color = "#00FF00" if budget_ok else ("#FFD700" if total_mise < BUDGET_TOTAL else "#FF4444")

    st.markdown(f"""
    <div style="background: #1a1a2e; border-radius: 8px; padding: 2px; margin: 5px 0;">
        <div style="background: {budget_color}; width: {min(total_mise/BUDGET_TOTAL*100, 100)}%; height: 18px; border-radius: 6px;"></div>
    </div>
    <div style="text-align: center; color: {budget_color}; font-size: 0.9em;">
        <b>{total_mise} / {BUDGET_TOTAL} pts</b> {' OK' if budget_ok else ''}
    </div>
    """, unsafe_allow_html=True)

    if not budget_ok:
        pronos_valides = False

    # JOKERS
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

    # Recuperer le stock de jokers et verifier si deja utilise cette semaine
    supabase = get_supabase()
    saison_id = get_saison_actuelle()
    stock = supabase.get_stock_jokers(user['id'], saison_id)
    if not stock:
        stock = supabase.init_stock_jokers(user['id'], saison_id)

    stock_doubles = stock.get('joker_double', 0) if stock else 0
    stock_voles = stock.get('joker_vol', 0) if stock else 0

    # Verifier si un joker a deja ete utilise cette semaine
    joker_actuel = get_joker_semaine(user['id'])

    # Si joker deja utilise, initialiser le state avec le joker actuel
    if joker_actuel and 'joker_init_done' not in st.session_state:
        if joker_actuel['type'] == 'DOUBLE':
            st.session_state.joker_selected = "DOUBLE"
            stock_doubles += 1  # Ajouter 1 car on peut le reutiliser
        elif joker_actuel['type'] == 'VOL':
            st.session_state.joker_selected = "VOLE"
            st.session_state.joker_cible_id = joker_actuel['cible_id']
            stock_voles += 1  # Ajouter 1 car on peut le reutiliser
        st.session_state.joker_init_done = True
    elif joker_actuel:
        # Ajuster le stock pour l'affichage (le joker actuel peut etre change)
        if joker_actuel['type'] == 'DOUBLE':
            stock_doubles += 1
        elif joker_actuel['type'] == 'VOL':
            stock_voles += 1

    # Stocker l'ancien joker pour la mise a jour
    st.session_state.joker_ancien = joker_actuel

    st.markdown("<div style='text-align:center; color:#AAAAAA; font-size:0.8em;'>Joker (optionnel)</div>", unsafe_allow_html=True)

    if joker_actuel:
        joker_label = "Points Doubles" if joker_actuel['type'] == 'DOUBLE' else "Points Voles"
        st.markdown(f"<div style='text-align:center; color:#FFD700; font-size:0.75em; margin-bottom:5px;'>Joker actuel: {joker_label} (modifiable)</div>", unsafe_allow_html=True)

    jk1, jk2 = st.columns(2)
    with jk1:
        can_use_double = stock_doubles > 0
        joker_double = st.checkbox(
            f"⚡ Points Doubles ({stock_doubles}/3)",
            value=(st.session_state.joker_selected == "DOUBLE"),
            key="chk_joker_double",
            disabled=not can_use_double
        )
        if joker_double and can_use_double:
            st.session_state.joker_selected = "DOUBLE"
        elif st.session_state.joker_selected == "DOUBLE" and not joker_double:
            st.session_state.joker_selected = "AUCUN"

    with jk2:
        can_use_vole = stock_voles > 0
        joker_vole = st.checkbox(
            f"🎯 Points Voles ({stock_voles}/2)",
            value=(st.session_state.joker_selected == "VOLE"),
            key="chk_joker_vole",
            disabled=not can_use_vole
        )
        if joker_vole and can_use_vole:
            st.session_state.joker_selected = "VOLE"
        elif st.session_state.joker_selected == "VOLE" and not joker_vole:
            st.session_state.joker_selected = "AUCUN"
            st.session_state.joker_cible_id = None

    if joker_double and joker_vole:
        st.warning("Un seul joker a la fois!")
        pronos_valides = False

    # Selection de la cible pour le joker VOLE
    if st.session_state.joker_selected == "VOLE":
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#FF6B6B; font-size:0.85em;'>🎯 Choisissez le joueur a voler :</div>", unsafe_allow_html=True)

        # Recuperer les autres joueurs actifs
        autres_joueurs = supabase.get_all_utilisateurs(statut='Actif')
        autres_joueurs = [j for j in autres_joueurs if j['id'] != user['id']]

        if autres_joueurs:
            options = {j['id']: j['pseudo'] for j in autres_joueurs}
            joueur_ids = list(options.keys())
            joueur_pseudos = list(options.values())

            # Trouver l'index actuel
            current_index = 0
            if st.session_state.joker_cible_id in joueur_ids:
                current_index = joueur_ids.index(st.session_state.joker_cible_id)

            cible_pseudo = st.selectbox(
                "Joueur cible",
                joueur_pseudos,
                index=current_index,
                key="select_cible_vol",
                label_visibility="collapsed"
            )
            st.session_state.joker_cible_id = joueur_ids[joueur_pseudos.index(cible_pseudo)]
        else:
                st.warning("Aucun autre joueur disponible")
                pronos_valides = False

    # VALIDATION
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

    if st.session_state.joker_selected != "AUCUN":
        joker_label = "Points Doubles" if st.session_state.joker_selected == "DOUBLE" else "Points Voles"
        st.markdown(f"<div style='text-align:center; color:#FFD700; font-size:0.9em;'>Joker actif: <b>{joker_label}</b></div>", unsafe_allow_html=True)

    if st.button("VALIDER MES PRONOSTICS", type="primary", use_container_width=True, disabled=not pronos_valides):
        if pronos_valides:
            pronos_data = {mid: {'home': d['home'], 'away': d['away'], 'mise': d['mise']}
                          for mid, d in st.session_state.pronos.items()}
            cible_id = st.session_state.joker_cible_id if st.session_state.joker_selected == "VOLE" else None
            joker_ancien = st.session_state.get('joker_ancien', None)
            success, message = sauvegarder_pronostics(user['id'], pronos_data, st.session_state.joker_selected, cible_id, joker_ancien)
            if success:
                st.success(message)
                st.balloons()
                st.session_state.pronos = {}
                st.session_state.joker_selected = "AUCUN"
                st.session_state.joker_cible_id = None
                st.session_state.joker_ancien = None
                st.session_state.joker_init_done = False
                st.session_state.mode_edition_pronos = False
            else:
                st.error(message)
