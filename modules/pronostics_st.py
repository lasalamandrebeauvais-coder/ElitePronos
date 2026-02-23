"""
Module Pronostics Streamlit pour Elite Pronos
Saisie des pronostics de la semaine - Version Supabase
"""
import streamlit as st
import os
from datetime import datetime, timedelta

# Import Supabase
from modules.supabase_db import get_supabase
from modules.database_manager import get_saison_actuelle, get_users_grand_chelem_semaine_precedente, get_journee_courante

# Chemins
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

# Budget hebdomadaire
BUDGET_BASE = 100
BONUS_GRAND_CHELEM = 40
MISE_MIN = 10
MISE_MAX = 60


def has_grand_chelem(user_id):
    """Verifie si le joueur a fait un Grand Chelem la semaine precedente."""
    try:
        saison_id = get_saison_actuelle()
        journee_courante = get_journee_courante(saison_id)
        users_gc = get_users_grand_chelem_semaine_precedente(journee_courante, saison_id)
        return user_id in users_gc
    except Exception as e:
        print(f"Erreur has_grand_chelem: {e}")
        return False


def get_budget_joueur(user_id):
    """
    Retourne le budget principal du joueur (toujours 100).
    Utiliser has_grand_chelem() pour savoir s'il a le bonus 40.
    """
    return BUDGET_BASE


def get_matchs_semaine():
    """
    Recupere les 4 matchs de la semaine en cours depuis Supabase
    """
    supabase = get_supabase()
    saison_id = get_saison_actuelle()

    try:
        journee_courante = get_journee_courante(saison_id)

        # Recuperer les matchs de cette journee
        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{journee_courante}&is_active=eq.true&select=id,championnat,equipe_home,equipe_away,cote_home,cote_draw,cote_away,date_match,score_final_home&order=id&limit=4'
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
        journee_courante = get_journee_courante(saison_id)

        # Recuperer les match_ids de cette journee
        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{journee_courante}&is_active=eq.true&select=id'
        ) or []

        if not matchs:
            return {}

        match_ids = [m['id'] for m in matchs]
        match_ids_str = ','.join(map(str, match_ids))

        # Recuperer les predictions
        predictions = supabase._request('GET',
            f'predictions?user_id=eq.{user_id}&match_id=in.({match_ids_str})&select=match_id,score_prono_home,score_prono_away,mise_points,mise_bonus_gc'
        ) or []

        pronos = {}
        for p in predictions:
            pronos[p['match_id']] = {
                'home': p['score_prono_home'],
                'away': p['score_prono_away'],
                'mise': p['mise_points'],
                'mise_bonus': p.get('mise_bonus_gc', 0) or 0
            }

        return pronos

    except Exception as e:
        print(f"Erreur get_pronos_existants: {e}")
        return {}


def get_joker_semaine(user_id):
    """Recupere le joker utilise cette semaine depuis Supabase
    Retourne un dict avec type_joker, id, cible_vol_id, cible_pseudo ou None
    """
    supabase = get_supabase()

    try:
        journee_courante = get_journee_courante()

        joker = supabase._request('GET',
            f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{journee_courante}&select=id,type_joker,cible_vol_id&limit=1'
        )

        if joker and len(joker) > 0:
            joker_data = {
                'id': joker[0].get('id'),
                'type': joker[0].get('type_joker'),
                'cible_id': joker[0].get('cible_vol_id'),
                'cible_pseudo': None
            }
            # Recuperer le pseudo de la cible si joker VOL
            if joker_data['cible_id']:
                cible = supabase._request('GET',
                    f'utilisateurs?id=eq.{joker_data["cible_id"]}&select=pseudo'
                )
                if cible and len(cible) > 0:
                    joker_data['cible_pseudo'] = cible[0].get('pseudo')
            return joker_data
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
        journee_courante = get_journee_courante(saison_id)

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
                'mise_bonus_gc': data.get('mise_bonus', 0),
                'points_gagnes': 0
            }
            result = supabase._request('POST', 'predictions', pred_data)
            if not result:
                return False, f"Erreur lors de l'enregistrement du match {match_id}"

        # Gestion des jokers - logique simplifiee:
        # 1. Toujours annuler l'ancien joker (restituer stock + supprimer historique)
        # 2. Appliquer le nouveau joker si selectionne

        stock = supabase.get_stock_jokers(user_id, saison_id)
        if not stock:
            stock = {'joker_double': 3, 'joker_vol': 2}

        # ETAPE 1: Annuler l'ancien joker s'il existe
        if joker_ancien and joker_ancien.get('id'):
            ancien_type = joker_ancien.get('type')
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

        # ETAPE 2: Appliquer le nouveau joker si selectionne
        if joker_type == "DOUBLE" and stock.get('joker_double', 0) > 0:
            supabase._request('PATCH',
                f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}',
                {'joker_double': stock['joker_double'] - 1}
            )
            # Supprimer tout doublon eventuel avant insertion
            supabase._request('DELETE', f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{journee_courante}')
            supabase._request('POST', 'jokers_historique', {
                'utilisateur_id': user_id,
                'semaine_id': journee_courante,
                'saison_id': saison_id,
                'type_joker': 'DOUBLE'
            })
        elif joker_type == "VOLE" and stock.get('joker_vol', 0) > 0 and cible_vol_id:
            supabase._request('PATCH',
                f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}',
                {'joker_vol': stock['joker_vol'] - 1}
            )
            # Supprimer tout doublon eventuel avant insertion
            supabase._request('DELETE', f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{journee_courante}')
            supabase._request('POST', 'jokers_historique', {
                'utilisateur_id': user_id,
                'semaine_id': journee_courante,
                'saison_id': saison_id,
                'type_joker': 'VOL',
                'cible_vol_id': cible_vol_id
            })

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
        journee_courante = get_journee_courante(saison_id)

        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{journee_courante}&is_active=eq.true&select=date_match&order=date_match&limit=1'
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
    col_back, col_home, col_title, col_mascot, col_countdown = st.columns([0.5, 0.5, 2.5, 0.8, 2])
    with col_back:
        if st.button("◀", help="Retour", use_container_width=True):
            st.session_state.dashboard_section = None
            st.session_state.mode_edition_pronos = False
            st.rerun()
    with col_home:
        if st.button("🏠", help="Accueil", use_container_width=True):
            st.session_state.dashboard_section = None
            st.session_state.page = "Accueil"
            st.rerun()
    with col_title:
        st.markdown("### Pronostics")
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo pronostics.png")
        if os.path.exists(mascot_path):
            try:
                from PIL import Image
                mascot_img = Image.open(mascot_path)
                st.image(mascot_img, width=70)
            except Exception:
                pass

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

    # Verifier Grand Chelem
    joueur_gc = has_grand_chelem(user['id'])
    budget_total = BUDGET_BASE

    if joueur_gc:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #1a2e1a 100%);
            border: 2px solid #00FF00;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            text-align: center;
        ">
            <span style="color: #00FF00; font-size: 1.1em;">🏆 <b>GRAND CHELEM !</b> Budget: <b>100 pts</b> + <b>40 pts bonus</b></span>
        </div>
        """, unsafe_allow_html=True)

    # SI PRONOS VALIDES
    if pronos_existants and not mode_edition:
        st.markdown("### Vos pronostics valides")

        for match in matchs:
            match_id, championnat, home, away, cote_h, cote_n, cote_a, date_match = match
            if match_id in pronos_existants:
                p = pronos_existants[match_id]
                mise_bonus = p.get('mise_bonus', 0)
                bonus_txt = f' <span style="color: #FFD700;">+{mise_bonus}🏆</span>' if mise_bonus > 0 else ''
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
                    <span style="color: #00FF00; font-weight: bold;">{p['mise']} pts{bonus_txt}</span>
                </div>
                """, unsafe_allow_html=True)

        # Afficher le joker utilise cette semaine
        joker_semaine = get_joker_semaine(user['id'])
        if joker_semaine:
            if joker_semaine['type'] == 'DOUBLE':
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    border: 2px solid #FFD700;
                    border-radius: 10px;
                    padding: 12px;
                    margin: 10px 0;
                    text-align: center;
                ">
                    <span style="color: #FFD700; font-size: 1.1em;">⚡ Joker actif: <b>Points Doubles</b></span>
                </div>
                """, unsafe_allow_html=True)
            elif joker_semaine['type'] == 'VOL':
                cible_pseudo = joker_semaine.get('cible_pseudo', 'Inconnu')
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #1a1a2e 0%, #2d1a3e 100%);
                    border: 2px solid #FF6B6B;
                    border-radius: 10px;
                    padding: 12px;
                    margin: 10px 0;
                    text-align: center;
                ">
                    <span style="color: #FF6B6B; font-size: 1.1em;">🎯 Joker actif: <b>Points Voles</b></span><br>
                    <span style="color: #FFFFFF; font-size: 0.9em;">Cible: <b>{cible_pseudo}</b></span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("")
        if st.button("MODIFIER MES PRONOSTICS", type="secondary", use_container_width=True):
            st.session_state.mode_edition_pronos = True
            st.session_state.pronos = pronos_existants.copy()
            st.rerun()
        return

    # MODE SAISIE (st.form - aucun rerun tant que le joueur n'a pas clique Valider)

    # --- Chargement des donnees AVANT le form ---
    supabase = get_supabase()
    saison_id = get_saison_actuelle()
    stock = supabase.get_stock_jokers(user['id'], saison_id)
    if not stock:
        stock = supabase.init_stock_jokers(user['id'], saison_id)

    stock_doubles = stock.get('joker_double', 0) if stock else 0
    stock_voles = stock.get('joker_vol', 0) if stock else 0

    joker_actuel = get_joker_semaine(user['id'])

    # Ajuster le stock : le joker actuel peut etre change/retire
    if joker_actuel:
        if joker_actuel['type'] == 'DOUBLE':
            stock_doubles += 1
        elif joker_actuel['type'] == 'VOL':
            stock_voles += 1

    # Autres joueurs pour cible VOL
    autres_joueurs = supabase.get_all_utilisateurs(statut='Actif')
    autres_joueurs = [j for j in autres_joueurs if j['id'] != user['id']]
    joueur_pseudos = [j['pseudo'] for j in autres_joueurs]
    joueur_ids = [j['id'] for j in autres_joueurs]

    # Defaults jokers
    default_double = bool(joker_actuel and joker_actuel['type'] == 'DOUBLE')
    default_vole = bool(joker_actuel and joker_actuel['type'] == 'VOL')
    default_cible_index = 0
    if default_vole and joker_actuel.get('cible_id') in joueur_ids:
        default_cible_index = joueur_ids.index(joker_actuel['cible_id'])

    # --- FORMULAIRE ---
    with st.form("form_pronostics"):

        # Rappel budget statique
        budget_txt = f"Budget : **{BUDGET_BASE} pts** a repartir (min {MISE_MIN}, max {MISE_MAX} par match)"
        if joueur_gc:
            budget_txt += f" + **{BONUS_GRAND_CHELEM} pts bonus** Grand Chelem"
        st.markdown(budget_txt)

        # Boucle matchs (scores + mises)
        for i in range(0, len(matchs), 2):
            cols = st.columns(2)

            for j, col in enumerate(cols):
                if i + j < len(matchs):
                    match = matchs[i + j]
                    match_id, championnat, home, away, cote_h, cote_n, cote_a, date_match = match

                    existing = pronos_existants.get(match_id, {})
                    default_home = existing.get('home', 0)
                    default_away = existing.get('away', 0)
                    default_mise = existing.get('mise', 25)

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
                            st.number_input(
                                f"H{match_id}", min_value=0, max_value=9,
                                value=default_home,
                                key=f"h_{match_id}", label_visibility="collapsed"
                            )
                        with sc2:
                            st.markdown("<div style='text-align:center; padding-top:5px; color:#0066FF; font-size:1.5em; font-weight:bold;'>-</div>", unsafe_allow_html=True)
                        with sc3:
                            st.number_input(
                                f"A{match_id}", min_value=0, max_value=9,
                                value=default_away,
                                key=f"a_{match_id}", label_visibility="collapsed"
                            )

                        st.number_input(
                            f"M{match_id}", min_value=MISE_MIN, max_value=MISE_MAX,
                            value=default_mise,
                            step=5, key=f"m_{match_id}", label_visibility="collapsed"
                        )

        # BUDGET BONUS GC (40 pts)
        if joueur_gc:
            st.markdown("---")
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #1a1a2e 0%, #1a2e1a 100%);
                border: 1px solid #FFD700;
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0;
            ">
                <div style="text-align: center; color: #FFD700; font-size: 0.95em;">
                    🏆 <b>BONUS GRAND CHELEM</b> - 40 pts a repartir (pas de perte si mauvais prono)
                </div>
            </div>
            """, unsafe_allow_html=True)

            gc_cols = st.columns(len(matchs))
            for idx, match in enumerate(matchs):
                match_id = match[0]
                home, away = match[2], match[3]
                existing_gc = pronos_existants.get(match_id, {}).get('mise_bonus', 10)
                with gc_cols[idx]:
                    short_home = home[:8]
                    short_away = away[:8]
                    st.markdown(f"<div style='text-align:center; color:#AAA; font-size:0.65em;'>{short_home} v {short_away}</div>", unsafe_allow_html=True)
                    st.number_input(
                        f"GC{match_id}", min_value=0, max_value=40,
                        value=existing_gc,
                        step=5, key=f"gc_{match_id}", label_visibility="collapsed"
                    )

        # JOKERS
        st.markdown("---")
        st.markdown("<div style='text-align:center; color:#AAAAAA; font-size:0.8em;'>Joker (optionnel)</div>", unsafe_allow_html=True)

        if joker_actuel:
            joker_label = "Points Doubles" if joker_actuel['type'] == 'DOUBLE' else "Points Voles"
            st.markdown(f"<div style='text-align:center; color:#FFD700; font-size:0.75em; margin-bottom:5px;'>Joker actuel: {joker_label} (modifiable)</div>", unsafe_allow_html=True)

        jk1, jk2 = st.columns(2)
        with jk1:
            st.checkbox(
                f"⚡ Points Doubles ({stock_doubles}/3)",
                value=default_double,
                key="chk_joker_double",
                disabled=(stock_doubles <= 0)
            )
        with jk2:
            st.checkbox(
                f"🎯 Points Voles ({stock_voles}/2)",
                value=default_vole,
                key="chk_joker_vole",
                disabled=(stock_voles <= 0)
            )

        # Cible VOL - toujours affichee (pas de rerun conditionnel dans un form)
        if autres_joueurs:
            st.selectbox(
                "🎯 Cible du vol *(ignore si Points Voles non coche)*",
                joueur_pseudos,
                index=default_cible_index,
                key="select_cible_vol"
            )
        else:
            st.markdown("<div style='color:#FF6B6B; font-size:0.8em;'>Aucun autre joueur disponible pour le vol</div>", unsafe_allow_html=True)

        # Bouton unique de validation
        submitted = st.form_submit_button("VALIDER MES PRONOSTICS", type="primary", use_container_width=True)

    # --- HORS DU FORM : traitement post-submit ---
    if submitted:
        # Lire toutes les valeurs depuis session_state (mises a jour par le form)
        total_mise = 0
        total_bonus = 0
        pronos_data = {}
        for match in matchs:
            match_id = match[0]
            h = st.session_state.get(f"h_{match_id}", 0)
            a = st.session_state.get(f"a_{match_id}", 0)
            m = st.session_state.get(f"m_{match_id}", 25)
            pronos_data[match_id] = {'home': h, 'away': a, 'mise': m, 'mise_bonus': 0}
            total_mise += m

        errors = []

        # Valider budget principal
        if total_mise != BUDGET_BASE:
            errors.append(f"Budget incorrect : {total_mise} / {BUDGET_BASE} pts (doit faire exactement {BUDGET_BASE})")

        # Valider budget bonus GC
        if joueur_gc:
            for match in matchs:
                match_id = match[0]
                gc_val = st.session_state.get(f"gc_{match_id}", 0)
                pronos_data[match_id]['mise_bonus'] = gc_val
                total_bonus += gc_val
                if gc_val > 0 and gc_val < 10:
                    errors.append("Mise bonus minimum : 10 pts par match")
                    break
            if total_bonus != BONUS_GRAND_CHELEM:
                errors.append(f"Bonus GC incorrect : {total_bonus} / {BONUS_GRAND_CHELEM} pts (doit faire exactement {BONUS_GRAND_CHELEM})")

        # Valider jokers
        chk_double = st.session_state.get("chk_joker_double", False)
        chk_vole = st.session_state.get("chk_joker_vole", False)

        if chk_double and chk_vole:
            errors.append("Un seul joker a la fois !")

        joker_type = "AUCUN"
        cible_id = None
        if chk_double and not chk_vole:
            if stock_doubles > 0:
                joker_type = "DOUBLE"
            else:
                errors.append("Stock de jokers Points Doubles epuise")
        elif chk_vole and not chk_double:
            if stock_voles > 0:
                joker_type = "VOLE"
                selected_pseudo = st.session_state.get("select_cible_vol")
                if selected_pseudo and selected_pseudo in joueur_pseudos:
                    cible_id = joueur_ids[joueur_pseudos.index(selected_pseudo)]
                if not cible_id:
                    errors.append("Selectionnez une cible pour le vol")
            else:
                errors.append("Stock de jokers Points Voles epuise")

        # Afficher erreurs ou sauvegarder
        if errors:
            for e in errors:
                st.error(e)
        else:
            success, message = sauvegarder_pronostics(
                user['id'], pronos_data, joker_type, cible_id, joker_actuel
            )
            if success:
                st.success(message)
                st.balloons()
                # Nettoyer le session_state lie au form
                for match in matchs:
                    mid = match[0]
                    for prefix in ['h_', 'a_', 'm_', 'gc_']:
                        st.session_state.pop(f"{prefix}{mid}", None)
                st.session_state.pop('chk_joker_double', None)
                st.session_state.pop('chk_joker_vole', None)
                st.session_state.pop('select_cible_vol', None)
                st.session_state.pop('pronos', None)
                st.session_state.pop('bonus_gc', None)
                st.session_state.pop('joker_selected', None)
                st.session_state.pop('joker_cible_id', None)
                st.session_state.pop('joker_ancien', None)
                st.session_state.pop('joker_init_done', None)
                st.session_state.mode_edition_pronos = False
                st.rerun()
            else:
                st.error(message)
