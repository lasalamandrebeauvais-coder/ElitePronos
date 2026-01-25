"""
Module Classement Streamlit pour Elite Pronos
Classements avec 3 onglets : General, Ma Semaine, Records
"""
import streamlit as st
import os
from datetime import datetime

# Import Supabase
from modules.supabase_db import get_supabase

# Chemins pour assets (images)
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')


def get_classement_general_complet():
    """
    Recupere le classement general avec toutes les stats depuis Supabase:
    - Place, Pseudo, Points, Bons pronos, Scores exacts, Grand Chelem
    - Jokers restants (Doubles, Voles), Meilleure place
    """
    try:
        client = get_supabase()

        # Recuperer tous les utilisateurs actifs
        utilisateurs = client.get_all_utilisateurs(statut='Actif')
        if not utilisateurs:
            return []

        classement = []
        for user in utilisateurs:
            user_id = user['id']
            pseudo = user['pseudo']

            # Recuperer toutes les predictions de cet utilisateur
            predictions = client._request('GET',
                f'predictions?user_id=eq.{user_id}&select=points_gagnes,is_score_exact,match_id'
            ) or []

            # Calculer les stats
            total_points = sum(p.get('points_gagnes', 0) or 0 for p in predictions)
            bons_pronos = sum(1 for p in predictions if (p.get('points_gagnes') or 0) > 0)
            scores_exacts = sum(1 for p in predictions if p.get('is_score_exact'))

            # Grand Chelem: compter les semaines avec 4+ bons pronos
            # (simplifie pour l'instant)
            nb_grand_chelem = 0

            # Jokers restants (valeurs par defaut)
            stock = client.get_stock_jokers(user_id)
            jokers_double = stock.get('joker_double', 2) if stock else 2
            jokers_vol = stock.get('joker_vol', 2) if stock else 2

            classement.append({
                'user_id': user_id,
                'pseudo': pseudo,
                'points': total_points,
                'bons_pronos': bons_pronos,
                'scores_exacts': scores_exacts,
                'grand_chelem': nb_grand_chelem,
                'jokers_double': jokers_double,
                'jokers_vol': jokers_vol,
                'meilleure_place': 1  # Placeholder
            })

        # Trier par points decroissants
        classement.sort(key=lambda x: x['points'], reverse=True)

        # Ajouter les places et meilleure place
        for idx, joueur in enumerate(classement):
            joueur['place'] = idx + 1
            joueur['meilleure_place'] = idx + 1

        return classement

    except Exception as e:
        print(f"Erreur classement Supabase: {e}")
        return []


def get_historique_joueur(user_id):
    """Recupere l'historique des pronostics par journee pour un joueur depuis Supabase"""
    try:
        client = get_supabase()

        # Recuperer toutes les predictions de cet utilisateur avec les matchs
        predictions = client._request('GET',
            f'predictions?user_id=eq.{user_id}&select=*,matches(semaine_id,equipe_home,equipe_away,score_final_home,score_final_away,date_match,saison_id)'
        ) or []

        if not predictions:
            return []

        # Grouper par journee
        journees_dict = {}
        for p in predictions:
            match = p.get('matches', {})
            if not match:
                continue
            journee = match.get('semaine_id')
            if journee not in journees_dict:
                journees_dict[journee] = []

            prono = (
                match.get('equipe_home', ''),
                match.get('equipe_away', ''),
                p.get('score_prono_home'),
                p.get('score_prono_away'),
                p.get('mise_points'),
                p.get('points_gagnes'),
                match.get('score_final_home'),
                match.get('score_final_away'),
                p.get('is_score_exact')
            )
            journees_dict[journee].append(prono)

        # Construire l'historique
        historique = []
        for journee in sorted(journees_dict.keys(), reverse=True):
            pronos = journees_dict[journee]
            total_journee = sum(p[5] or 0 for p in pronos)
            historique.append({
                'journee': journee,
                'pronos': pronos,
                'total': total_journee
            })

        return historique

    except Exception as e:
        print(f"Erreur historique Supabase: {e}")
        return []


def get_records_joueur(user_id):
    """Recupere les records d'un joueur depuis Supabase"""
    try:
        client = get_supabase()

        # Recuperer toutes les predictions de cet utilisateur
        predictions = client._request('GET',
            f'predictions?user_id=eq.{user_id}&select=points_gagnes,is_score_exact,match_id,matches(semaine_id)'
        ) or []

        # Nombre de scores exacts
        nb_scores_exacts = sum(1 for p in predictions if p.get('is_score_exact'))

        # Nombre de bons pronostics (1N2 correct)
        nb_bons_pronos = sum(1 for p in predictions if (p.get('points_gagnes') or 0) > 0)

        # Meilleur score en une journee
        journees_points = {}
        for p in predictions:
            match = p.get('matches', {})
            if match:
                journee = match.get('semaine_id')
                if journee:
                    journees_points[journee] = journees_points.get(journee, 0) + (p.get('points_gagnes') or 0)

        meilleur_journee = max(journees_points.values()) if journees_points else 0

        return {
            'scores_exacts': nb_scores_exacts,
            'bons_pronos': nb_bons_pronos,
            'meilleur_journee': meilleur_journee
        }

    except Exception as e:
        print(f"Erreur records Supabase: {e}")
        return {'scores_exacts': 0, 'bons_pronos': 0, 'meilleur_journee': 0}


def afficher_classement(user):
    """Affiche le module de classement complet"""

    # Style CSS Elite
    st.markdown("""
    <style>
        h1, h2, h3 { color: #FFD700 !important; }
        .stButton > button { color: #FFD700 !important; border-color: #FFD700 !important; }
    </style>
    """, unsafe_allow_html=True)

    # Header avec bouton retour JAUNE et mascotte
    col_back, col_title, col_mascot = st.columns([0.6, 4.5, 0.8])
    with col_back:
        st.markdown("""
        <style>
            div[data-testid="column"]:first-child button {
                color: #FFD700 !important;
                border-color: #FFD700 !important;
                background-color: transparent !important;
            }
        </style>
        """, unsafe_allow_html=True)
        if st.button("◀", help="Retour", use_container_width=True, key="btn_retour_classement"):
            st.session_state.dashboard_section = None
            st.rerun()
    with col_title:
        st.markdown("## 🏆 Classement Elite")
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo classements.png")
        if os.path.exists(mascot_path):
            from PIL import Image
            mascot_img = Image.open(mascot_path)
            st.image(mascot_img, width=70)

    st.markdown("---")

    current_user_id = user['id']

    # Onglets (3 onglets - sans Assiduite)
    tab1, tab2, tab3 = st.tabs(["🥇 General", "📅 Ma Semaine", "🔥 Records"])

    # === ONGLET GENERAL ===
    with tab1:
        st.markdown("### Classement General")
        st.caption("Cumul total des points de la saison")

        classement = get_classement_general_complet()

        if classement:
            # Header du tableau
            st.markdown("""
            <div style="display:flex; background:#D4AF37; padding:8px 5px; border-radius:8px 8px 0 0; font-weight:bold; font-size:0.75em; color:#001529;">
                <span style="width:50px; text-align:center;">#</span>
                <span style="flex:1;">Pseudo</span>
                <span style="width:70px; text-align:center;">Points</span>
                <span style="width:50px; text-align:center;">Bons</span>
                <span style="width:50px; text-align:center;">Exacts</span>
            </div>
            """, unsafe_allow_html=True)

            # Lignes du tableau - une par une avec fond forcé
            for joueur in classement:
                is_current = (joueur['user_id'] == current_user_id)
                bg = "#002855" if is_current else "#001529"
                border = "border-left:4px solid #FFD700;" if is_current else ""

                if joueur['place'] == 1:
                    icon = "🥇"
                elif joueur['place'] == 2:
                    icon = "🥈"
                elif joueur['place'] == 3:
                    icon = "🥉"
                else:
                    icon = f"<span style='color:#888;'>{joueur['place']}</span>"

                st.markdown(f"""
                <div style="display:flex; align-items:center; background:{bg}; padding:6px 5px; border-bottom:1px solid #333; font-size:0.8em; {border}">
                    <span style="width:50px; text-align:center;">{icon}</span>
                    <span style="flex:1; color:#FFF;">{joueur['pseudo']}</span>
                    <span style="width:70px; text-align:center; color:#00FF00; font-weight:bold;">{joueur['points']}</span>
                    <span style="width:50px; text-align:center; color:#4488FF;">{joueur['bons_pronos']}</span>
                    <span style="width:50px; text-align:center; color:#FFD700;">{joueur['scores_exacts']}</span>
                </div>
                """, unsafe_allow_html=True)

            # Légende
            st.markdown("""
            <div style="background:#0a1628; padding:6px; text-align:center; font-size:0.6em; color:#666; border-radius:0 0 8px 8px;">
                Bons = 1N2 correct | Exacts = Score exact
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Aucun joueur dans le classement.")

    # === ONGLET MA SEMAINE ===
    with tab2:
        st.markdown("### Mon Historique")
        st.caption("Historique de mes pronostics par journee")

        historique = get_historique_joueur(current_user_id)

        if historique:
            for h in historique:
                # Total de la journee
                total_color = "#00FF00" if h['total'] >= 0 else "#FF4444"

                with st.expander(f"📅 Journee {h['journee']} - {'+' if h['total'] > 0 else ''}{h['total']} pts", expanded=(h == historique[0])):
                    # Header
                    st.markdown("""
                    <div style="display: grid; grid-template-columns: 2fr 1fr 0.8fr 1fr 0.8fr; gap: 5px; padding: 5px; font-size: 0.7em; color: #888; background: #002040; border-radius: 5px;">
                        <span>Match</span>
                        <span style="text-align: center;">Prono</span>
                        <span style="text-align: center;">Mise</span>
                        <span style="text-align: center;">Score</span>
                        <span style="text-align: center;">Pts</span>
                    </div>
                    """, unsafe_allow_html=True)

                    for prono in h['pronos']:
                        home, away, ph, pa, mise, pts, score_h, score_a, is_exact = prono

                        # Icone resultat
                        if score_h is not None:
                            if is_exact:
                                icon = "🎯"
                            elif pts and pts > 0:
                                icon = "✅"
                            else:
                                icon = "❌"
                            score_display = f"{score_h}-{score_a}"
                        else:
                            icon = "⏳"
                            score_display = "-"

                        pts_val = pts if pts else 0
                        pts_color = "#00FF00" if pts_val > 0 else "#FF4444" if pts_val < 0 else "#888"

                        home_short = home[:10] + ".." if len(home) > 12 else home
                        away_short = away[:10] + ".." if len(away) > 12 else away

                        st.markdown(f"""
                        <div style="display: grid; grid-template-columns: 2fr 1fr 0.8fr 1fr 0.8fr; gap: 5px; padding: 5px; font-size: 0.75em; border-bottom: 1px solid #333;">
                            <span style="color: #FFFFFF;" title="{home} vs {away}">{home_short} - {away_short}</span>
                            <span style="color: #4488FF; text-align: center;">{ph}-{pa}</span>
                            <span style="color: #FFD700; text-align: center;">{mise}</span>
                            <span style="color: #00FF00; text-align: center;">{score_display} {icon}</span>
                            <span style="color: {pts_color}; text-align: center; font-weight: bold;">{'+' if pts_val > 0 else ''}{pts_val}</span>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Aucun historique disponible.")

    # === ONGLET RECORDS ===
    with tab3:
        st.markdown("### Mes Records")
        st.caption("Mes performances personnelles")

        records = get_records_joueur(current_user_id)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1a472a 0%, #2d5a3c 100%);
                border: 2px solid #00FF00;
                border-radius: 15px;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-size: 2.5em; color: #00FF00; font-weight: bold;">🎯</div>
                <div style="font-size: 2em; color: #FFFFFF; font-weight: bold;">{records['scores_exacts']}</div>
                <div style="color: #00FF00; font-size: 0.9em;">Scores Exacts</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1a3a5c 0%, #2d4a6c 100%);
                border: 2px solid #4488FF;
                border-radius: 15px;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-size: 2.5em; color: #4488FF; font-weight: bold;">✅</div>
                <div style="font-size: 2em; color: #FFFFFF; font-weight: bold;">{records['bons_pronos']}</div>
                <div style="color: #4488FF; font-size: 0.9em;">Bons Pronostics</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #5c3a1a 0%, #6c4a2d 100%);
                border: 2px solid #FFD700;
                border-radius: 15px;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-size: 2.5em; color: #FFD700; font-weight: bold;">🏆</div>
                <div style="font-size: 2em; color: #FFFFFF; font-weight: bold;">{records['meilleur_journee']}</div>
                <div style="color: #FFD700; font-size: 0.9em;">Record Journee</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #AAAAAA; padding: 10px;">
        <small>Classements mis a jour en temps reel</small>
    </div>
    """, unsafe_allow_html=True)
