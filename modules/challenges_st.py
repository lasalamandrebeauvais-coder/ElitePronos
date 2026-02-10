"""
Module Challenges Streamlit pour Elite Pronos
3 onglets : Duel de la semaine, Face a face, Defis hebdomadaires
"""
import streamlit as st

from modules.supabase_db import get_supabase
from modules.database_manager import (
    get_saison_actuelle, get_saison_label, get_journee_courante,
    get_points_joueur_semaine, get_mvp_semaine
)


@st.cache_data(ttl=30)
def _get_points_semaine_cache(user_id, semaine_id, saison_id):
    """Version cachee de get_points_joueur_semaine"""
    return get_points_joueur_semaine(user_id, semaine_id, saison_id)


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

    # 3 onglets
    tab_duel, tab_h2h, tab_defis = st.tabs(["⚔️ Duel", "🤝 Face a face", "🎯 Defis"])

    # ================================================================
    # ONGLET 1 : DUEL DE LA SEMAINE
    # ================================================================
    with tab_duel:
        st.markdown("### Duel de la semaine")
        st.caption("Un rival designe chaque semaine pour un duel amical - pas de points en jeu !")

        rivaux_ids = supabase.get_rivaux_ids(current_user_id)

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

                # Points des 2 joueurs pour la journee courante
                pts_user = _get_points_semaine_cache(current_user_id, journee_courante, saison_id)
                pts_rival = _get_points_semaine_cache(rival_id, journee_courante, saison_id)

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
                <div style="display:flex;justify-content:center;align-items:center;gap:20px;margin:20px 0;">
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

        rivaux_ids = supabase.get_rivaux_ids(current_user_id)

        if not rivaux_ids:
            st.info("Selectionnez des rivaux dans **Mes Rivaux** pour voir le bilan H2H !")
        else:
            # Recuperer les pseudos des rivaux
            rivaux_ids_str = ','.join(map(str, rivaux_ids))
            rivaux_data = supabase._request('GET',
                f'utilisateurs?id=in.({rivaux_ids_str})&select=id,pseudo'
            ) or []
            rivaux_pseudo = {r['id']: r['pseudo'] for r in rivaux_data}

            # Pour chaque rival, compter victoires/nuls/defaites par journee
            bilans = []
            for rival_id in rivaux_ids:
                victories = 0
                draws = 0
                defeats = 0

                for j in range(1, journee_courante):
                    pts_me = _get_points_semaine_cache(current_user_id, j, saison_id)
                    pts_rival = _get_points_semaine_cache(rival_id, j, saison_id)

                    # Ne compter que si les deux ont joue
                    if pts_me['details'] and pts_rival['details']:
                        if pts_me['total'] > pts_rival['total']:
                            victories += 1
                        elif pts_me['total'] < pts_rival['total']:
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
            h2h_html = '<table style="width:100%;border-collapse:collapse;font-size:0.8rem;text-align:center;background:#001529;">'
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

            h2h_html += '</tbody></table>'
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
        st.caption("3 defis a relever chaque semaine - pour le plaisir !")

        # Determiner la semaine a afficher (courante si en cours, precedente si terminee)
        semaine_defis = journee_courante

        pts_data = _get_points_semaine_cache(current_user_id, semaine_defis, saison_id)

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
                'icon': '💰',
                'titre': '200+ points',
                'desc': f'Obtenir 200 points ou plus sur la J{semaine_defis}',
                'reussi': defi1_ok,
                'progress': f"{pts_data['total']}/200 pts"
            },
            {
                'icon': '🎯',
                'titre': '2 scores exacts',
                'desc': f'Trouver 2 scores exacts sur la J{semaine_defis}',
                'reussi': defi2_ok,
                'progress': f"{pts_data['nb_exacts']}/2 exacts"
            },
            {
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
                if defi['reussi']:
                    status_icon = "✅"
                    border_color = "#00FF00"
                    bg_gradient = "linear-gradient(135deg,#002520,#003530)"
                    status_text = "Reussi !"
                    status_color = "#00FF00"
                else:
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
                <div style="background:{bg_gradient};border:2px solid {border_color};border-radius:12px;padding:15px;text-align:center;min-height:180px;display:flex;flex-direction:column;justify-content:center;">
                    <div style="font-size:2em;">{defi['icon']}</div>
                    <div style="color:#FFD700;font-weight:bold;font-size:0.85em;margin:8px 0;">{defi['titre']}</div>
                    <div style="color:#888;font-size:0.7em;margin-bottom:8px;">{defi['desc']}</div>
                    <div style="font-size:1.3em;margin:5px 0;">{status_icon}</div>
                    <div style="color:{status_color};font-size:0.75em;font-weight:bold;">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)

        # Historique des defis (journees precedentes)
        if journee_courante > 1:
            st.markdown("---")
            st.markdown("#### Historique des defis")

            hist_html = '<table style="width:100%;border-collapse:collapse;font-size:0.75rem;text-align:center;background:#001529;">'
            hist_html += '<thead><tr style="background:linear-gradient(135deg,#D4AF37,#B8960C);color:#001529;font-weight:bold;">'
            hist_html += '<th style="padding:6px;border:1px solid #003060;">Journee</th>'
            hist_html += '<th style="padding:6px;border:1px solid #003060;">200+ pts</th>'
            hist_html += '<th style="padding:6px;border:1px solid #003060;">2 exacts</th>'
            hist_html += '<th style="padding:6px;border:1px solid #003060;">All-in</th>'
            hist_html += '</tr></thead><tbody>'

            for j in range(journee_courante - 1, max(0, journee_courante - 6), -1):
                pts_j = _get_points_semaine_cache(current_user_id, j, saison_id)
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

            hist_html += '</tbody></table>'
            st.markdown(hist_html, unsafe_allow_html=True)
