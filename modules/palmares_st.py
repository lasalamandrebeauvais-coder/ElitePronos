"""
Module Palmares pour Elite Pronos
Affiche le podium et l'historique des saisons terminées
"""
import streamlit as st
from modules.supabase_db import get_supabase
from modules.database_manager import get_saison_label


@st.cache_data(ttl=300)
def get_saisons_terminees():
    """Recupere toutes les saisons archivees (is_active = false)"""
    supabase = get_supabase()
    return supabase._request('GET', 'saisons?is_active=eq.false&select=annee_debut&order=annee_debut.desc') or []


@st.cache_data(ttl=300)
def get_palmares_saison(saison_id):
    """Recupere le palmares complet d'une saison, trié par place"""
    supabase = get_supabase()
    results = supabase._request('GET',
        f'palmares?saison_id=eq.{saison_id}&select=place,points_total,bonnes_predictions,scores_exacts,grand_chelem,user_id&order=place.asc'
    ) or []

    if not results:
        return []

    # Récupérer les pseudos
    user_ids = [str(r['user_id']) for r in results]
    users_raw = supabase._request('GET', f'utilisateurs?id=in.({",".join(user_ids)})&select=id,pseudo') or []
    user_map = {u['id']: u['pseudo'] for u in users_raw}

    for r in results:
        r['pseudo'] = user_map.get(r['user_id'], f"Joueur #{r['user_id']}")

    return results


def afficher_palmares():
    """Page principale du palmarès"""

    st.markdown("""
    <style>
    .palmares-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #D4AF37, #FFD700, #B8960C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .palmares-subtitle {
        text-align: center;
        color: #8899aa;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    .podium-card {
        background: linear-gradient(135deg, #001f3f, #002d5a);
        border: 1px solid #D4AF37;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .podium-1 { border-color: #FFD700; border-width: 2px; }
    .podium-2 { border-color: #C0C0C0; }
    .podium-3 { border-color: #CD7F32; }
    .podium-pseudo {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0.3rem 0;
    }
    .podium-pts {
        font-size: 1.4rem;
        font-weight: 800;
        color: #D4AF37;
    }
    .podium-stats {
        font-size: 0.75rem;
        color: #8899aa;
        margin-top: 0.3rem;
    }
    .classement-row {
        display: flex;
        align-items: center;
        padding: 0.5rem 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.3rem;
        background: #001529;
    }
    .classement-row:nth-child(even) { background: #001a35; }
    .rank-badge {
        font-size: 0.85rem;
        font-weight: 700;
        color: #8899aa;
        width: 2rem;
        flex-shrink: 0;
    }
    .player-name {
        flex: 1;
        font-weight: 600;
        color: #ffffff;
        font-size: 0.9rem;
    }
    .player-pts {
        color: #D4AF37;
        font-weight: 700;
        font-size: 0.9rem;
        width: 5rem;
        text-align: right;
    }
    .player-stats-mini {
        color: #556677;
        font-size: 0.75rem;
        width: 8rem;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="palmares-title">🏆 Palmarès</div>', unsafe_allow_html=True)
    st.markdown('<div class="palmares-subtitle">Classements définitifs des saisons terminées</div>', unsafe_allow_html=True)

    saisons = get_saisons_terminees()

    if not saisons:
        st.info("Aucune saison archivée pour l'instant. Le palmarès sera disponible à la fin de la première saison.")
        return

    # Sélecteur de saison
    options = {get_saison_label(s['annee_debut']): s['annee_debut'] for s in saisons}
    saison_choisie_label = st.selectbox("Saison", list(options.keys()), index=0)
    saison_id = options[saison_choisie_label]

    palmares = get_palmares_saison(saison_id)

    if not palmares:
        st.warning(f"Aucune donnée de palmarès pour la saison {saison_choisie_label}.")
        return

    # --- PODIUM ---
    st.markdown(f"### Podium — Saison {saison_choisie_label}")

    medailles = {1: "🥇", 2: "🥈", 3: "🥉"}
    podium = [p for p in palmares if p['place'] <= 3]
    autres = [p for p in palmares if p['place'] > 3]

    # Affichage podium en colonnes (2-1-3 pour effet podium)
    ordre_affichage = []
    if len(podium) >= 2:
        ordre_affichage.append(podium[1])  # 2ème à gauche
    if len(podium) >= 1:
        ordre_affichage.insert(1, podium[0])  # 1er au centre
    if len(podium) >= 3:
        ordre_affichage.append(podium[2])  # 3ème à droite

    if ordre_affichage:
        cols = st.columns(len(ordre_affichage))
        for col, joueur in zip(cols, ordre_affichage):
            place = joueur['place']
            css_class = f"podium-{place}"
            medaille = medailles.get(place, str(place))
            with col:
                st.markdown(f"""
                <div class="podium-card {css_class}">
                    <div style="font-size:2rem">{medaille}</div>
                    <div class="podium-pseudo">{joueur['pseudo']}</div>
                    <div class="podium-pts">{joueur['points_total']} pts</div>
                    <div class="podium-stats">
                        {joueur['bonnes_predictions']} bons pronos &nbsp;·&nbsp;
                        {joueur['scores_exacts']} exacts &nbsp;·&nbsp;
                        {joueur['grand_chelem']} GC
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- RESTE DU CLASSEMENT ---
    if autres:
        st.markdown("### Classement complet")
        rows_html = ""
        for j in autres:
            rows_html += f"""
            <div class="classement-row">
                <span class="rank-badge">{j['place']}.</span>
                <span class="player-name">{j['pseudo']}</span>
                <span class="player-stats-mini">{j['bonnes_predictions']} bons · {j['scores_exacts']} exacts · {j['grand_chelem']} GC</span>
                <span class="player-pts">{j['points_total']} pts</span>
            </div>
            """
        st.markdown(rows_html, unsafe_allow_html=True)

    # --- RECORDS DE LA SAISON ---
    st.markdown("---")
    st.markdown("### Records de la saison")
    col1, col2, col3 = st.columns(3)

    if palmares:
        meilleur_exact = max(palmares, key=lambda x: x['scores_exacts'])
        meilleur_gc = max(palmares, key=lambda x: x['grand_chelem'])
        meilleur_bons = max(palmares, key=lambda x: x['bonnes_predictions'])

        col1.metric("🎯 Plus de scores exacts", meilleur_exact['pseudo'], f"{meilleur_exact['scores_exacts']} exacts")
        col2.metric("⚡ Plus de Grand Chelem", meilleur_gc['pseudo'], f"{meilleur_gc['grand_chelem']} GC")
        col3.metric("✅ Plus de bons pronos", meilleur_bons['pseudo'], f"{meilleur_bons['bonnes_predictions']} bons")
