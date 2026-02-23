"""
Module Classement Streamlit pour Elite Pronos
Classements avec 5 onglets : General, Scores Exacts, Pronostics, Ma Semaine, Records
"""
import streamlit as st
import os
from datetime import datetime

# Import Supabase
from modules.supabase_db import get_supabase
from modules.database_manager import get_mvp_semaine, get_saison_actuelle, get_saison_label, get_journee_courante, get_streak_meilleur_joueur, get_bonus_meilleur_joueur

# Chemins pour assets (images)
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')


@st.cache_data(ttl=30)
def get_classement_general_complet():
    """
    Recupere le classement general avec cache (TTL 60s)
    Version optimisee : 2 requetes au lieu de N
    """
    try:
        client = get_supabase()

        # 1. Une seule requete pour TOUTES les predictions
        all_predictions = client._request('GET',
            'predictions?select=user_id,points_gagnes,is_score_exact'
        ) or []

        # 2. Agreger les stats par utilisateur
        user_stats = {}
        for p in all_predictions:
            uid = p['user_id']
            if uid not in user_stats:
                user_stats[uid] = {'points': 0, 'bons': 0, 'exacts': 0}
            pts = p.get('points_gagnes') or 0
            user_stats[uid]['points'] += pts
            if pts > 0:
                user_stats[uid]['bons'] += 1
            if p.get('is_score_exact'):
                user_stats[uid]['exacts'] += 1

        # 3. Une seule requete pour les utilisateurs + jokers
        utilisateurs = client.get_all_utilisateurs(statut='Actif')

        # 4. Une seule requete pour tous les jokers
        all_jokers = client._request('GET', 'stock_jokers?select=utilisateur_id,joker_double,joker_vol') or []
        jokers_dict = {j['utilisateur_id']: j for j in all_jokers}

        # 5. Calculer les Grand Chelems par joueur (4/4 corrects par semaine)
        # Utiliser 2 requetes separees au lieu d'une jointure (plus fiable avec l'API REST)
        saison_id = get_saison_actuelle()

        # Recuperer tous les matchs actifs termines
        all_matchs_gc = client._request('GET',
            f'matches?saison_id=eq.{saison_id}&score_final_home=not.is.null&is_active=eq.true&select=id,semaine_id,score_final_home,score_final_away'
        )
        if not isinstance(all_matchs_gc, list):
            all_matchs_gc = []
        matchs_gc_dict = {m['id']: m for m in all_matchs_gc}

        # Recuperer toutes les predictions de la saison
        gc_match_ids = [m['id'] for m in all_matchs_gc]
        gc_par_joueur = {}

        if gc_match_ids:
            gc_match_ids_str = ','.join(map(str, gc_match_ids))
            all_preds_gc = client._request('GET',
                f'predictions?match_id=in.({gc_match_ids_str})&select=user_id,match_id,score_prono_home,score_prono_away'
            )
            if not isinstance(all_preds_gc, list):
                all_preds_gc = []

            # Recuperer les voleurs par semaine (exclus du GC)
            all_jokers_vol = client._request('GET',
                f'jokers_historique?saison_id=eq.{saison_id}&type_joker=eq.VOL&select=utilisateur_id,semaine_id'
            )
            if not isinstance(all_jokers_vol, list):
                all_jokers_vol = []
            voleurs_par_semaine = {}
            for jv in all_jokers_vol:
                sid = jv['semaine_id']
                if sid not in voleurs_par_semaine:
                    voleurs_par_semaine[sid] = set()
                voleurs_par_semaine[sid].add(jv['utilisateur_id'])

            # Compter 1N2 corrects par (user, semaine) sur matchs actifs termines
            user_semaine_corrects = {}
            for p in all_preds_gc:
                mid = p['match_id']
                m = matchs_gc_dict.get(mid)
                if not m:
                    continue
                uid = p['user_id']
                sid = m['semaine_id']

                # Exclure voleurs
                if uid in voleurs_par_semaine.get(sid, set()):
                    continue

                prono_h, prono_a = p['score_prono_home'], p['score_prono_away']
                score_h, score_a = m['score_final_home'], m['score_final_away']
                bon = ((prono_h > prono_a and score_h > score_a) or
                       (prono_h < prono_a and score_h < score_a) or
                       (prono_h == prono_a and score_h == score_a))
                if bon:
                    key = (uid, sid)
                    user_semaine_corrects[key] = user_semaine_corrects.get(key, 0) + 1

            # Compter les GC par joueur (semaines avec 4/4)
            for (uid, sid), count in user_semaine_corrects.items():
                if count >= 4:
                    gc_par_joueur[uid] = gc_par_joueur.get(uid, 0) + 1

        classement = []
        for user in utilisateurs:
            uid = user['id']
            stats = user_stats.get(uid, {'points': 0, 'bons': 0, 'exacts': 0})
            jokers = jokers_dict.get(uid, {})

            classement.append({
                'user_id': uid,
                'pseudo': user['pseudo'],
                'points': round(stats['points'], 2),
                'bons_pronos': stats['bons'],
                'scores_exacts': stats['exacts'],
                'grand_chelem': gc_par_joueur.get(uid, 0),
                'jokers_double': jokers.get('joker_double', 3) or 3,
                'jokers_vol': jokers.get('joker_vol', 2) or 2,
                'meilleure_place': 1
            })

        classement.sort(key=lambda x: x['points'], reverse=True)

        for idx, joueur in enumerate(classement):
            joueur['place'] = idx + 1
            joueur['meilleure_place'] = idx + 1

        return classement

    except Exception as e:
        print(f"Erreur classement Supabase: {e}")
        return []


@st.cache_data(ttl=30)
def get_evolution_classement():
    """Compare classement actuel (temps reel) vs classement il y a 5 journees max"""
    try:
        client = get_supabase()

        # Toutes les predictions avec semaine_id
        all_preds = client._request('GET',
            'predictions?select=user_id,points_gagnes,matches(semaine_id)'
        ) or []

        # Trouver toutes les journees disponibles
        all_semaines = sorted({
            (p.get('matches') or {}).get('semaine_id')
            for p in all_preds
            if (p.get('matches') or {}).get('semaine_id') is not None
        })

        # Pas assez de journees pour comparer
        if len(all_semaines) <= 1:
            return {}

        # Reference = 5 journees en arriere (ou la premiere dispo)
        # Ex: [J19,J20,J21] → idx=max(0,3-6)=0 → ref=J19
        # Ex: [J19..J25] → idx=max(0,7-6)=1 → ref=J20
        ref_idx = max(0, len(all_semaines) - 6)
        ref_semaine = all_semaines[ref_idx]

        # Points actuels (toutes journees) et points a la journee de reference
        current_pts = {}
        old_pts = {}
        for p in all_preds:
            uid = p['user_id']
            pts = p.get('points_gagnes') or 0
            current_pts[uid] = current_pts.get(uid, 0) + pts
            semaine = (p.get('matches') or {}).get('semaine_id')
            if semaine is not None and semaine <= ref_semaine:
                old_pts[uid] = old_pts.get(uid, 0) + pts

        # Classement actuel
        current_rank = sorted(current_pts.items(), key=lambda x: x[1], reverse=True)
        current_pos = {uid: i+1 for i, (uid, _) in enumerate(current_rank)}

        # Classement a la reference
        old_rank = sorted(old_pts.items(), key=lambda x: x[1], reverse=True)
        old_pos = {uid: i+1 for i, (uid, _) in enumerate(old_rank)}

        # Evolution = ancienne_pos - actuelle_pos (positif = monte)
        evolution = {}
        for uid in current_pos:
            if uid in old_pos:
                evolution[uid] = old_pos[uid] - current_pos[uid]
            else:
                evolution[uid] = 0
        return evolution
    except Exception as e:
        print(f"Erreur evolution: {e}")
        return {}


@st.cache_data(ttl=30)
def get_historique_joueur(user_id):
    """Recupere l'historique des pronostics par journee pour un joueur (cache 30s)"""
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


@st.cache_data(ttl=30)
def get_records_joueur(user_id):
    """Recupere les records d'un joueur (cache 30s)"""
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

    # Header avec bouton retour, accueil, actualiser et mascotte
    col_back, col_home, col_title, col_refresh, col_mascot = st.columns([0.5, 0.5, 3, 0.8, 0.7])
    with col_back:
        if st.button("◀", help="Retour", use_container_width=True, key="btn_retour_classement"):
            st.session_state.dashboard_section = None
            st.rerun()
    with col_home:
        if st.button("🏠", help="Accueil", use_container_width=True, key="btn_accueil_classement"):
            st.session_state.dashboard_section = None
            st.session_state.page = "Accueil"
            st.rerun()
    with col_title:
        st.markdown("## Classement Elite")
    with col_refresh:
        if st.button("🔄", help="Actualiser", use_container_width=True, key="btn_refresh_classement"):
            st.cache_data.clear()
            st.rerun()
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo classements.png")
        if os.path.exists(mascot_path):
            try:
                from PIL import Image
                mascot_img = Image.open(mascot_path)
                st.image(mascot_img, width=70)
            except Exception:
                pass

    st.markdown("---")

    current_user_id = user['id']

    # Onglets (6 onglets)
    tab1, tab_mj, tab2, tab3, tab4, tab5 = st.tabs(["🥇 General", "🏆 Meilleur joueur", "🎯 Scores Exacts", "✅ Pronostics", "📅 Ma Semaine", "🔥 Records"])

    # === ONGLET GENERAL ===
    with tab1:
        st.markdown("### Classement General")
        st.caption("Cumul total des points de la saison")

        classement = get_classement_general_complet()

        if classement:
            # Recuperer l'evolution du classement
            evolution = get_evolution_classement()

            # Construire le tableau complet en une seule chaine HTML (scrollable sur mobile)
            cls_html = '<div class="ep-table-scroll">'
            cls_html += '<div class="ep-classement-header" style="display:flex; background:#D4AF37; padding:8px 5px; border-radius:8px 8px 0 0; font-weight:bold; font-size:0.7em; color:#001529;">'
            cls_html += '<span style="width:40px; text-align:center;">#</span>'
            cls_html += '<span style="flex:1;">Pseudo</span>'
            cls_html += '<span style="width:35px; text-align:center;">Evol</span>'
            cls_html += '<span style="width:55px; text-align:center;">Pts</span>'
            cls_html += '<span style="width:40px; text-align:center;">Bons</span>'
            cls_html += '<span style="width:40px; text-align:center;">Exacts</span>'
            cls_html += '<span style="width:35px; text-align:center;">GC</span>'
            cls_html += '<span style="width:35px; text-align:center;">x2</span>'
            cls_html += '<span style="width:35px; text-align:center;">Vol</span>'
            cls_html += '<span style="width:35px; text-align:center;">Top</span>'
            cls_html += '</div>'

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

                evol = evolution.get(joueur['user_id'], 0)
                if evol > 0:
                    evol_html = '<span class="evol-up">▲</span>'
                elif evol < 0:
                    evol_html = '<span class="evol-down">▼</span>'
                else:
                    evol_html = '<span class="evol-same">-</span>'

                cls_html += f'<div class="ep-classement-row" style="display:flex; align-items:center; background:{bg}; padding:4px 5px; margin:0; border-bottom:1px solid #222; font-size:0.7em; {border}">'
                cls_html += f'<span style="width:40px; text-align:center;">{icon}</span>'
                cls_html += f'<span style="flex:1; color:#FFF;">{joueur["pseudo"]}</span>'
                cls_html += f'<span style="width:35px; text-align:center;">{evol_html}</span>'
                cls_html += f'<span style="width:55px; text-align:center; color:#00FF00; font-weight:bold;">{joueur["points"]}</span>'
                cls_html += f'<span style="width:40px; text-align:center; color:#4488FF;">{joueur["bons_pronos"]}</span>'
                cls_html += f'<span style="width:40px; text-align:center; color:#FFD700;">{joueur["scores_exacts"]}</span>'
                cls_html += f'<span style="width:35px; text-align:center; color:#FF6600;">{joueur["grand_chelem"]}</span>'
                cls_html += f'<span style="width:35px; text-align:center; color:#00BFFF;">{joueur["jokers_double"]}</span>'
                cls_html += f'<span style="width:35px; text-align:center; color:#FF69B4;">{joueur["jokers_vol"]}</span>'
                cls_html += f'<span style="width:35px; text-align:center; color:#AAAAAA;">{joueur["meilleure_place"]}</span>'
                cls_html += '</div>'

            cls_html += '<div style="background:#0a1628; padding:6px; text-align:center; font-size:0.55em; color:#666; border-radius:0 0 8px 8px;">'
            cls_html += 'Bons = 1N2 correct | Exacts = Score exact | GC = Grand Chelem | x2 = Joker Double | Vol = Joker Vol | Top = Meilleure place'
            cls_html += '</div></div>'
            st.markdown(cls_html, unsafe_allow_html=True)
        else:
            st.info("Aucun joueur dans le classement.")

    # === ONGLET MEILLEUR JOUEUR ===
    with tab_mj:
        saison_id = get_saison_actuelle()
        saison_label = get_saison_label(saison_id)
        journee_courante = get_journee_courante(saison_id)

        st.markdown(f"### Meilleur joueur de la semaine")
        st.caption(f"Saison {saison_label} - Le joueur avec le plus de points chaque journee")

        if journee_courante > 1:
            try:
                # Compter les titres par joueur
                titres = {}
                mvp_list = []
                for j in range(1, journee_courante):
                    mvp_j = get_mvp_semaine(j, saison_id)
                    mvp_list.append((j, mvp_j))
                    if mvp_j:
                        pseudo = mvp_j['pseudo']
                        titres[pseudo] = titres.get(pseudo, 0) + 1

                # Podium des joueurs les plus titres
                if titres:
                    podium = sorted(titres.items(), key=lambda x: x[1], reverse=True)[:3]
                    podium_html = '<div style="display:flex;justify-content:center;gap:15px;margin:15px 0;">'
                    medals = ['🥇', '🥈', '🥉']
                    for i, (pseudo, count) in enumerate(podium):
                        is_me_p = (pseudo == user['pseudo'])
                        border_color = '#FFD700' if i == 0 else '#C0C0C0' if i == 1 else '#CD7F32'
                        pseudo_display = f"⭐ {pseudo}" if is_me_p else pseudo
                        podium_html += f'''<div style="background:linear-gradient(135deg,#001529,#002040);border:2px solid {border_color};border-radius:10px;padding:12px 18px;text-align:center;min-width:90px;">
                            <div style="font-size:1.5em;">{medals[i]}</div>
                            <div style="color:#FFFFFF;font-weight:bold;font-size:0.85em;margin:4px 0;">{pseudo_display}</div>
                            <div style="color:{border_color};font-size:0.8em;">{count}x meilleur</div>
                        </div>'''
                    podium_html += '</div>'
                    st.markdown(podium_html, unsafe_allow_html=True)

                # Calculer les streaks pour chaque joueur qui a ete MVP
                # On parcourt la liste de la fin vers le debut pour detecter les series
                streaks_at_journee = {}
                for idx_j in range(len(mvp_list)):
                    j, mvp_j = mvp_list[idx_j]
                    if not mvp_j:
                        continue
                    # Compter combien de journees consecutives ce joueur est MVP
                    # en regardant en arriere depuis cette journee
                    streak = 1
                    for k in range(idx_j - 1, -1, -1):
                        _, prev_mvp = mvp_list[k]
                        if prev_mvp and prev_mvp['user_id'] == mvp_j['user_id']:
                            streak += 1
                        else:
                            break
                    streaks_at_journee[j] = streak

                # Calculer le bonus pour les joueurs actuellement en serie
                bonus_actifs = {}
                if mvp_list:
                    for pseudo, count in titres.items():
                        # Trouver le user_id pour ce pseudo
                        for j, mvp_j in mvp_list:
                            if mvp_j and mvp_j['pseudo'] == pseudo:
                                uid = mvp_j['user_id']
                                bonus = get_bonus_meilleur_joueur(uid, saison_id)
                                if bonus > 0:
                                    bonus_actifs[pseudo] = bonus
                                break

                # Afficher les bonus actifs
                if bonus_actifs:
                    bonus_html = '<div style="background:linear-gradient(135deg,#002520,#003530);border:2px solid #00FF00;border-radius:10px;padding:12px;margin:15px 0;">'
                    bonus_html += '<div style="color:#00FF00;font-weight:bold;text-align:center;margin-bottom:8px;">🔥 Bonus serie active</div>'
                    for pseudo, bonus in bonus_actifs.items():
                        streak = get_streak_meilleur_joueur(
                            next(mvp_j['user_id'] for j, mvp_j in mvp_list if mvp_j and mvp_j['pseudo'] == pseudo),
                            saison_id
                        )
                        bonus_html += f'<div style="color:#FFF;text-align:center;font-size:0.85em;">{pseudo} : {streak} journees consecutives → <span style="color:#00FF00;font-weight:bold;">+{bonus} pts</span></div>'
                    bonus_html += '</div>'
                    st.markdown(bonus_html, unsafe_allow_html=True)

                # Tableau historique
                mvp_html = '<div class="ep-table-scroll">'
                mvp_html += '<table style="width:100%;border-collapse:collapse;font-size:0.8rem;text-align:center;background:#001529;">'
                mvp_html += '<thead><tr style="background:linear-gradient(135deg,#D4AF37,#B8960C);color:#001529;font-weight:bold;">'
                mvp_html += '<th style="padding:8px 6px;border:1px solid #003060;">Journee</th>'
                mvp_html += '<th style="padding:8px 6px;border:1px solid #003060;">Meilleur joueur</th>'
                mvp_html += '<th style="padding:8px 6px;border:1px solid #003060;">Points</th>'
                mvp_html += '<th style="padding:8px 6px;border:1px solid #003060;">Serie</th>'
                mvp_html += '<th style="padding:8px 6px;border:1px solid #003060;">Bonus</th>'
                mvp_html += '</tr></thead><tbody>'

                has_mvp = False
                for j, mvp_j in mvp_list:
                    bg = '#002040' if j % 2 == 0 else '#001a35'
                    if mvp_j:
                        has_mvp = True
                        is_me_mvp = (mvp_j['user_id'] == current_user_id)
                        pseudo_display = f"⭐ {mvp_j['pseudo']}" if is_me_mvp else mvp_j['pseudo']
                        pts_color = '#00FF00' if mvp_j['points_journee'] >= 0 else '#FF4444'

                        streak = streaks_at_journee.get(j, 1)
                        streak_display = f"🔥 {streak}" if streak >= 2 else str(streak)

                        if streak >= 2:
                            bonus = 10 + 15 * (streak - 2) if streak > 2 else 10
                            bonus_display = f'<span style="color:#00FF00;">+{bonus}</span>'
                        else:
                            bonus_display = '-'

                        mvp_html += f'<tr style="background:{bg};color:#FFF;">'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;">J{j}</td>'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;font-weight:bold;">{pseudo_display}</td>'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;color:{pts_color};">{mvp_j["points_journee"]} pts</td>'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;">{streak_display}</td>'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;">{bonus_display}</td>'
                        mvp_html += '</tr>'
                    else:
                        mvp_html += f'<tr style="background:{bg};color:#555;">'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;">J{j}</td>'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;">-</td>'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;">-</td>'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;">-</td>'
                        mvp_html += f'<td style="padding:6px;border:1px solid #003060;">-</td>'
                        mvp_html += '</tr>'

                mvp_html += '</tbody></table></div>'

                if has_mvp:
                    st.markdown(mvp_html, unsafe_allow_html=True)
                else:
                    st.info("Aucun meilleur joueur disponible pour le moment.")

            except Exception as e:
                st.warning(f"Erreur chargement meilleur joueur: {e}")
        else:
            st.info("Le classement du meilleur joueur sera disponible apres la J1.")

    # === ONGLET SCORES EXACTS ===
    with tab2:
        st.markdown("### Classement Scores Exacts")
        st.caption("Nombre total de scores parfaitement predits")

        classement_se = get_classement_general_complet()

        if classement_se:
            # Trier par scores exacts decroissant
            classement_se = sorted(classement_se, key=lambda x: x['scores_exacts'], reverse=True)

            # Header du tableau
            st.markdown("""
            <div style="display:flex; background:#D4AF37; padding:8px 10px; border-radius:8px 8px 0 0; font-weight:bold; font-size:0.75em; color:#001529;">
                <span style="width:45px; text-align:center;">#</span>
                <span style="flex:1;">Pseudo</span>
                <span style="width:80px; text-align:center;">Scores Exacts</span>
            </div>
            """, unsafe_allow_html=True)

            for idx, joueur in enumerate(classement_se):
                rang = idx + 1
                is_current = (joueur['user_id'] == current_user_id)
                bg = "#002855" if is_current else "#001529"
                border = "border-left:4px solid #FFD700;" if is_current else ""

                if rang == 1:
                    icon = "🥇"
                elif rang == 2:
                    icon = "🥈"
                elif rang == 3:
                    icon = "🥉"
                else:
                    icon = f"<span style='color:#888;'>{rang}</span>"

                st.markdown(f"""
                <div style="display:flex; align-items:center; background:{bg}; padding:6px 10px; margin:0; border-bottom:1px solid #222; font-size:0.75em; {border}">
                    <span style="width:45px; text-align:center;">{icon}</span>
                    <span style="flex:1; color:#FFF;">{joueur['pseudo']}</span>
                    <span style="width:80px; text-align:center; color:#FFD700; font-weight:bold;">{joueur['scores_exacts']}</span>
                </div>
                """, unsafe_allow_html=True)

            # Fermeture tableau
            st.markdown("""
            <div style="height:6px; background:#0a1628; border-radius:0 0 8px 8px;"></div>
            """, unsafe_allow_html=True)
        else:
            st.info("Aucun joueur dans le classement.")

    # === ONGLET PRONOSTICS ===
    with tab3:
        st.markdown("### Classement Pronostics")
        st.caption("Nombre total de resultats 1N2 corrects")

        classement_bp = get_classement_general_complet()

        if classement_bp:
            # Trier par bons pronostics decroissant
            classement_bp = sorted(classement_bp, key=lambda x: x['bons_pronos'], reverse=True)

            # Header du tableau
            st.markdown("""
            <div style="display:flex; background:#D4AF37; padding:8px 10px; border-radius:8px 8px 0 0; font-weight:bold; font-size:0.75em; color:#001529;">
                <span style="width:45px; text-align:center;">#</span>
                <span style="flex:1;">Pseudo</span>
                <span style="width:80px; text-align:center;">Bons Pronos</span>
            </div>
            """, unsafe_allow_html=True)

            for idx, joueur in enumerate(classement_bp):
                rang = idx + 1
                is_current = (joueur['user_id'] == current_user_id)
                bg = "#002855" if is_current else "#001529"
                border = "border-left:4px solid #FFD700;" if is_current else ""

                if rang == 1:
                    icon = "🥇"
                elif rang == 2:
                    icon = "🥈"
                elif rang == 3:
                    icon = "🥉"
                else:
                    icon = f"<span style='color:#888;'>{rang}</span>"

                st.markdown(f"""
                <div style="display:flex; align-items:center; background:{bg}; padding:6px 10px; margin:0; border-bottom:1px solid #222; font-size:0.75em; {border}">
                    <span style="width:45px; text-align:center;">{icon}</span>
                    <span style="flex:1; color:#FFF;">{joueur['pseudo']}</span>
                    <span style="width:80px; text-align:center; color:#4488FF; font-weight:bold;">{joueur['bons_pronos']}</span>
                </div>
                """, unsafe_allow_html=True)

            # Fermeture tableau
            st.markdown("""
            <div style="height:6px; background:#0a1628; border-radius:0 0 8px 8px;"></div>
            """, unsafe_allow_html=True)
        else:
            st.info("Aucun joueur dans le classement.")

    # === ONGLET MA SEMAINE ===
    with tab4:
        st.markdown("### Mon Historique")
        st.caption("Historique de mes pronostics par journee")

        historique = get_historique_joueur(current_user_id)

        if historique:
            for h in historique:
                # Total de la journee
                total_color = "#00FF00" if h['total'] >= 0 else "#FF4444"

                with st.expander(f"📅 Journee {h['journee']} - {'+' if h['total'] > 0 else ''}{h['total']} pts", expanded=(h == historique[0])):
                    # Construire le HTML complet en une seule chaine (scrollable sur mobile)
                    hist_html = '<div class="ep-table-scroll">'
                    hist_html += '<div style="display: grid; grid-template-columns: 2fr 1fr 0.8fr 1fr 0.8fr; gap: 5px; padding: 5px; font-size: 0.7em; color: #888; background: #002040; border-radius: 5px; min-width: 350px;">'
                    hist_html += '<span>Match</span><span style="text-align: center;">Prono</span><span style="text-align: center;">Mise</span><span style="text-align: center;">Score</span><span style="text-align: center;">Pts</span></div>'

                    for prono in h['pronos']:
                        home, away, ph, pa, mise, pts, score_h, score_a, is_exact = prono

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

                        hist_html += f'<div style="display: grid; grid-template-columns: 2fr 1fr 0.8fr 1fr 0.8fr; gap: 5px; padding: 5px; font-size: 0.75em; border-bottom: 1px solid #333; min-width: 350px;">'
                        hist_html += f'<span style="color: #FFFFFF;" title="{home} vs {away}">{home_short} - {away_short}</span>'
                        hist_html += f'<span style="color: #4488FF; text-align: center;">{ph}-{pa}</span>'
                        hist_html += f'<span style="color: #FFD700; text-align: center;">{mise}</span>'
                        hist_html += f'<span style="color: #00FF00; text-align: center;">{score_display} {icon}</span>'
                        hist_html += f'<span style="color: {pts_color}; text-align: center; font-weight: bold;">{("+" if pts_val > 0 else "")}{pts_val}</span>'
                        hist_html += '</div>'

                    hist_html += '</div>'
                    st.markdown(hist_html, unsafe_allow_html=True)
        else:
            st.info("Aucun historique disponible.")

    # === ONGLET RECORDS ===
    with tab5:
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
