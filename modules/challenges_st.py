"""
Module Challenges Streamlit pour Elite Pronos
3 onglets : Duel de la semaine, Face a face, Defis hebdomadaires
Version optimisee : 2-3 requetes Supabase max (batch)
"""
import streamlit as st

from modules.supabase_db import get_supabase
from modules.database_manager import (
    get_saison_actuelle, get_saison_label, get_journee_courante
)


@st.cache_data(ttl=60)
def _get_defis_recompenses(user_id, saison_id):
    """Retourne l'ensemble des (semaine_id, defi_numero) deja recompenses pour ce joueur."""
    supabase = get_supabase()
    rows = supabase._request('GET',
        f'defis_recompenses?user_id=eq.{user_id}&saison_id=eq.{saison_id}&select=semaine_id,defi_numero'
    ) or []
    return {(r['semaine_id'], r['defi_numero']) for r in rows}


@st.cache_data(ttl=30)
def _get_all_points_by_user_journee(user_ids, saison_id):
    """
    Recupere en UNE SEULE requete les points de tous les joueurs par journee.
    Retourne: {user_id: {semaine_id: {'total': X, 'nb_exacts': Y, 'details': [...]}}}
    """
    supabase = get_supabase()

    # Convertir en tuple pour le cache hashable
    user_ids = list(user_ids)
    user_ids_str = ','.join(map(str, user_ids))

    # 1 seule requete : toutes les predictions de tous les users avec semaine_id
    predictions = supabase._request('GET',
        f'predictions?user_id=in.({user_ids_str})&saison_id=eq.{saison_id}'
        f'&select=user_id,match_id,mise_points,points_gagnes,is_score_exact,matches(semaine_id)'
    ) or []

    # Agreger par user_id + semaine_id
    result = {}
    for p in predictions:
        uid = p['user_id']
        semaine = (p.get('matches') or {}).get('semaine_id')
        if semaine is None:
            continue

        if uid not in result:
            result[uid] = {}
        if semaine not in result[uid]:
            result[uid][semaine] = {'total': 0, 'nb_exacts': 0, 'details': []}

        pts = p.get('points_gagnes') or 0
        result[uid][semaine]['total'] += pts
        if p.get('is_score_exact'):
            result[uid][semaine]['nb_exacts'] += 1
        result[uid][semaine]['details'].append({
            'match_id': p['match_id'],
            'mise': p.get('mise_points') or 0,
            'points_gagnes': pts,
            'is_exact': p.get('is_score_exact') or False
        })

    return result


def afficher_challenges(user):
    """Affiche le menu Challenges avec 3 onglets"""

    # Header
    col_back, col_home, col_title = st.columns([0.5, 0.5, 5])
    with col_back:
        if st.button("◀", help="Retour", use_container_width=True, key="btn_retour_challenges"):
            st.session_state.dashboard_section = None
            st.rerun()
    with col_home:
        if st.button("🏠", help="Accueil", use_container_width=True, key="btn_accueil_challenges"):
            st.session_state.dashboard_section = None
            st.session_state.page = "Accueil"
            st.rerun()
    with col_title:
        st.markdown("## Challenges")

    st.markdown("---")

    supabase = get_supabase()
    saison_id = get_saison_actuelle()
    journee_courante = get_journee_courante(saison_id)
    current_user_id = user['id']

    # Recuperer les rivaux UNE SEULE FOIS
    rivaux_ids = supabase.get_rivaux_ids(current_user_id)

    # Charger TOUTES les donnees en 1 requete batch (user + tous les rivaux)
    all_user_ids = tuple(sorted(set([current_user_id] + rivaux_ids)))
    all_data = _get_all_points_by_user_journee(all_user_ids, saison_id)

    # Helper pour acceder aux donnees
    EMPTY = {'total': 0, 'nb_exacts': 0, 'details': []}
    def pts(uid, j):
        return all_data.get(uid, {}).get(j, EMPTY)

    # 3 onglets
    tab_duel, tab_h2h, tab_defis = st.tabs(["⚔️ Duel", "🤝 Face a face", "🎯 Defis"])

    # ================================================================
    # ONGLET 1 : DUEL DE LA SEMAINE
    # ================================================================
    with tab_duel:
        st.markdown("### Duel de la semaine")
        st.caption("Un rival designe chaque semaine pour un duel amical - pas de points en jeu !")

        if not rivaux_ids:
            st.info("Selectionnez des rivaux dans **Mes Rivaux** pour debloquer les duels !")
        else:
            # Selection deterministe du rival pour la semaine
            rival_id = rivaux_ids[journee_courante % len(rivaux_ids)]

            # Recuperer le pseudo du rival
            rival_data = supabase._request('GET',
                f'utilisateurs?id=eq.{rival_id}&select=id,pseudo'
            ) or []

            if not rival_data:
                st.warning("Rival introuvable.")
            else:
                rival_pseudo = rival_data[0]['pseudo']

                pts_user = pts(current_user_id, journee_courante)
                pts_rival = pts(rival_id, journee_courante)

                user_total = pts_user['total']
                rival_total = pts_rival['total']

                # Determiner qui mene
                if user_total > rival_total:
                    user_color = "#00FF00"
                    rival_color = "#FF4444"
                    result_text = "Vous menez !"
                    result_color = "#00FF00"
                elif rival_total > user_total:
                    user_color = "#FF4444"
                    rival_color = "#00FF00"
                    result_text = f"{rival_pseudo} mene !"
                    result_color = "#FF4444"
                else:
                    user_color = "#FFD700"
                    rival_color = "#FFD700"
                    result_text = "Egalite !"
                    result_color = "#FFD700"

                # Affichage visuel face a face
                st.markdown(f"""
                <div class="ep-duel" style="display:flex;justify-content:center;align-items:center;gap:20px;margin:20px 0;">
                    <div style="background:linear-gradient(135deg,#001529,#002040);border:2px solid {user_color};border-radius:15px;padding:20px 30px;text-align:center;min-width:130px;">
                        <div style="font-size:1.5em;margin-bottom:5px;">🧑</div>
                        <div style="color:#FFFFFF;font-weight:bold;font-size:1em;">{user['pseudo']}</div>
                        <div style="color:{user_color};font-size:2em;font-weight:bold;margin:10px 0;">{user_total}</div>
                        <div style="color:#888;font-size:0.75em;">points J{journee_courante}</div>
                        <div style="color:#FFD700;font-size:0.7em;margin-top:5px;">{pts_user['nb_exacts']} exact(s)</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:2em;color:#FFD700;">VS</div>
                        <div style="color:{result_color};font-weight:bold;font-size:0.85em;margin-top:5px;">{result_text}</div>
                    </div>
                    <div style="background:linear-gradient(135deg,#001529,#002040);border:2px solid {rival_color};border-radius:15px;padding:20px 30px;text-align:center;min-width:130px;">
                        <div style="font-size:1.5em;margin-bottom:5px;">👤</div>
                        <div style="color:#FFFFFF;font-weight:bold;font-size:1em;">{rival_pseudo}</div>
                        <div style="color:{rival_color};font-size:2em;font-weight:bold;margin:10px 0;">{rival_total}</div>
                        <div style="color:#888;font-size:0.75em;">points J{journee_courante}</div>
                        <div style="color:#FFD700;font-size:0.7em;margin-top:5px;">{pts_rival['nb_exacts']} exact(s)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="text-align:center;color:#888;font-size:0.8em;margin-top:10px;">
                    Duel amical - Journee {journee_courante} - Aucun point en jeu
                </div>
                """, unsafe_allow_html=True)

    # ================================================================
    # ONGLET 2 : FACE A FACE (H2H)
    # ================================================================
    with tab_h2h:
        st.markdown("### Face a face")
        st.caption("Bilan de vos confrontations directes contre vos rivaux")

        if not rivaux_ids:
            st.info("Selectionnez des rivaux dans **Mes Rivaux** pour voir le bilan H2H !")
        else:
            # Recuperer les pseudos des rivaux
            rivaux_ids_str = ','.join(map(str, rivaux_ids))
            rivaux_data = supabase._request('GET',
                f'utilisateurs?id=in.({rivaux_ids_str})&select=id,pseudo'
            ) or []
            rivaux_pseudo = {r['id']: r['pseudo'] for r in rivaux_data}

            # Calculer les bilans H2H (tout en memoire, 0 requete supplementaire)
            bilans = []
            for rival_id in rivaux_ids:
                victories = 0
                draws = 0
                defeats = 0

                for j in range(1, journee_courante):
                    pts_me = pts(current_user_id, j)
                    pts_riv = pts(rival_id, j)

                    # Ne compter que si les deux ont joue
                    if pts_me['details'] and pts_riv['details']:
                        if pts_me['total'] > pts_riv['total']:
                            victories += 1
                        elif pts_me['total'] < pts_riv['total']:
                            defeats += 1
                        else:
                            draws += 1

                total_played = victories + draws + defeats
                if total_played > 0:
                    diff = victories - defeats
                    if diff > 0:
                        bilan_str = f"+{diff}"
                        bilan_color = "#00FF00"
                    elif diff < 0:
                        bilan_str = str(diff)
                        bilan_color = "#FF4444"
                    else:
                        bilan_str = "0"
                        bilan_color = "#FFD700"
                else:
                    bilan_str = "-"
                    bilan_color = "#888"

                bilans.append({
                    'pseudo': rivaux_pseudo.get(rival_id, '???'),
                    'victories': victories,
                    'draws': draws,
                    'defeats': defeats,
                    'bilan_str': bilan_str,
                    'bilan_color': bilan_color
                })

            # Affichage tableau H2H
            h2h_html = '<div class="ep-table-scroll">'
            h2h_html += '<table style="width:100%;border-collapse:collapse;font-size:0.8rem;text-align:center;background:#001529;">'
            h2h_html += '<thead><tr style="background:linear-gradient(135deg,#D4AF37,#B8960C);color:#001529;font-weight:bold;">'
            h2h_html += '<th style="padding:8px 6px;border:1px solid #003060;">Rival</th>'
            h2h_html += '<th style="padding:8px 6px;border:1px solid #003060;">V</th>'
            h2h_html += '<th style="padding:8px 6px;border:1px solid #003060;">N</th>'
            h2h_html += '<th style="padding:8px 6px;border:1px solid #003060;">D</th>'
            h2h_html += '<th style="padding:8px 6px;border:1px solid #003060;">Bilan</th>'
            h2h_html += '</tr></thead><tbody>'

            for idx, b in enumerate(bilans):
                bg = '#002040' if idx % 2 == 0 else '#001a35'
                h2h_html += f'<tr style="background:{bg};color:#FFF;">'
                h2h_html += f'<td style="padding:6px;border:1px solid #003060;font-weight:bold;">{b["pseudo"]}</td>'
                h2h_html += f'<td style="padding:6px;border:1px solid #003060;color:#00FF00;">{b["victories"]}</td>'
                h2h_html += f'<td style="padding:6px;border:1px solid #003060;color:#FFD700;">{b["draws"]}</td>'
                h2h_html += f'<td style="padding:6px;border:1px solid #003060;color:#FF4444;">{b["defeats"]}</td>'
                h2h_html += f'<td style="padding:6px;border:1px solid #003060;color:{b["bilan_color"]};font-weight:bold;">{b["bilan_str"]}</td>'
                h2h_html += '</tr>'

            h2h_html += '</tbody></table></div>'
            st.markdown(h2h_html, unsafe_allow_html=True)

            st.markdown("""
            <div style="text-align:center;color:#888;font-size:0.7em;margin-top:8px;">
                V = Victoires | N = Nuls | D = Defaites | Bilan = V - D
            </div>
            """, unsafe_allow_html=True)

    # ================================================================
    # ONGLET 3 : DEFIS HEBDOMADAIRES
    # ================================================================
    with tab_defis:
        st.markdown("### Defis hebdomadaires")
        st.caption("3 defis a relever chaque semaine — chaque defi reussi rapporte **+1 🃏 Joker VOL** !")

        # Semaine courante
        semaine_defis = journee_courante
        pts_data = pts(current_user_id, semaine_defis)
        saison_id = get_saison_actuelle()

        # Defis deja recompenses pour ce joueur
        recompenses = _get_defis_recompenses(current_user_id, saison_id)

        # Defi 1 : 200+ points
        defi1_ok = pts_data['total'] >= 200
        # Defi 2 : 2 scores exacts
        defi2_ok = pts_data['nb_exacts'] >= 2
        # Defi 3 : Miser 40+ pts sur un match et gagner
        defi3_ok = any(
            d['mise'] >= 40 and d['points_gagnes'] > 0
            for d in pts_data['details']
        )

        defis = [
            {
                'num': 1,
                'icon': '💰',
                'titre': '200+ points',
                'desc': f'Obtenir 200 points ou plus sur la J{semaine_defis}',
                'reussi': defi1_ok,
                'progress': f"{pts_data['total']}/200 pts"
            },
            {
                'num': 2,
                'icon': '🎯',
                'titre': '2 scores exacts',
                'desc': f'Trouver 2 scores exacts sur la J{semaine_defis}',
                'reussi': defi2_ok,
                'progress': f"{pts_data['nb_exacts']}/2 exacts"
            },
            {
                'num': 3,
                'icon': '🎲',
                'titre': 'All-in gagnant',
                'desc': f'Miser 40+ pts sur un match et gagner (J{semaine_defis})',
                'reussi': defi3_ok,
                'progress': "Reussi !" if defi3_ok else "En cours..."
            }
        ]

        # Afficher les 3 cartes de defis
        cols = st.columns(3)
        for i, defi in enumerate(defis):
            with cols[i]:
                joker_attribue = (semaine_defis, defi['num']) in recompenses
                if defi['reussi']:
                    status_icon = "✅"
                    border_color = "#00FF00"
                    bg_gradient = "linear-gradient(135deg,#002520,#003530)"
                    status_text = "Reussi !"
                    status_color = "#00FF00"
                    joker_badge = '<div style="color:#FFD700;font-size:0.75em;margin-top:6px;">🃏 +1 Joker VOL' + (' attribue !' if joker_attribue else ' a venir') + '</div>'
                else:
                    joker_badge = '<div style="color:#444;font-size:0.7em;margin-top:6px;">🃏 +1 Joker VOL si reussi</div>'
                    has_data = len(pts_data['details']) > 0
                    if has_data:
                        status_icon = "❌"
                        border_color = "#FF6600"
                        bg_gradient = "linear-gradient(135deg,#1a1a2e,#16213e)"
                        status_text = defi['progress']
                        status_color = "#FF6600"
                    else:
                        status_icon = "🔒"
                        border_color = "#555"
                        bg_gradient = "linear-gradient(135deg,#111,#1a1a2e)"
                        status_text = "Pas encore"
                        status_color = "#888"

                st.markdown(f"""
                <div style="background:{bg_gradient};border:2px solid {border_color};border-radius:12px;padding:15px;text-align:center;min-height:195px;display:flex;flex-direction:column;justify-content:center;">
                    <div style="font-size:2em;">{defi['icon']}</div>
                    <div style="color:#FFD700;font-weight:bold;font-size:0.85em;margin:8px 0;">{defi['titre']}</div>
                    <div style="color:#888;font-size:0.7em;margin-bottom:8px;">{defi['desc']}</div>
                    <div style="font-size:1.3em;margin:5px 0;">{status_icon}</div>
                    <div style="color:{status_color};font-size:0.75em;font-weight:bold;">{status_text}</div>
                    {joker_badge}
                </div>
                """, unsafe_allow_html=True)

        # Historique des defis (journees precedentes, deja en memoire)
        if journee_courante > 1:
            st.markdown("---")
            st.markdown("#### Historique des defis")

            hist_html = '<div class="ep-table-scroll">'
            hist_html += '<table style="width:100%;border-collapse:collapse;font-size:0.75rem;text-align:center;background:#001529;">'
            hist_html += '<thead><tr style="background:linear-gradient(135deg,#D4AF37,#B8960C);color:#001529;font-weight:bold;">'
            hist_html += '<th style="padding:6px;border:1px solid #003060;">Journee</th>'
            hist_html += '<th style="padding:6px;border:1px solid #003060;">200+ pts</th>'
            hist_html += '<th style="padding:6px;border:1px solid #003060;">2 exacts</th>'
            hist_html += '<th style="padding:6px;border:1px solid #003060;">All-in</th>'
            hist_html += '</tr></thead><tbody>'

            for j in range(journee_courante - 1, max(0, journee_courante - 6), -1):
                pts_j = pts(current_user_id, j)
                d1 = "✅" if pts_j['total'] >= 200 else "❌"
                d2 = "✅" if pts_j['nb_exacts'] >= 2 else "❌"
                d3 = "✅" if any(d['mise'] >= 40 and d['points_gagnes'] > 0 for d in pts_j['details']) else "❌"

                bg = '#002040' if j % 2 == 0 else '#001a35'
                hist_html += f'<tr style="background:{bg};color:#FFF;">'
                hist_html += f'<td style="padding:5px;border:1px solid #003060;">J{j}</td>'
                hist_html += f'<td style="padding:5px;border:1px solid #003060;">{d1}</td>'
                hist_html += f'<td style="padding:5px;border:1px solid #003060;">{d2}</td>'
                hist_html += f'<td style="padding:5px;border:1px solid #003060;">{d3}</td>'
                hist_html += '</tr>'

            hist_html += '</tbody></table></div>'
            st.markdown(hist_html, unsafe_allow_html=True)
