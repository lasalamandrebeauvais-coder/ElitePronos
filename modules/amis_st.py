"""
Module Amis/Rivaux Streamlit pour Elite Pronos
Gestion des relations entre joueurs et comparaison directe
"""
import streamlit as st
import sqlite3
import os
from datetime import datetime

# Chemins
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')
AVATARS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'avatars')


def get_avatar_path(pseudo):
    """Retourne le chemin de l'avatar du joueur"""
    avatar_file = os.path.join(AVATARS_PATH, f"{pseudo}.png")
    if os.path.exists(avatar_file):
        return avatar_file
    return None


def rechercher_utilisateur(pseudo_recherche, current_user_id):
    """Recherche un utilisateur par pseudo"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, pseudo, prenom
        FROM utilisateurs
        WHERE pseudo LIKE ? AND id != ? AND statut = 'Actif'
        LIMIT 5
    """, (f"%{pseudo_recherche}%", current_user_id))

    results = cursor.fetchall()
    conn.close()
    return results


def get_relation_status(user_id, ami_id):
    """Vérifie le statut de la relation entre deux utilisateurs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier dans les deux sens
    cursor.execute("""
        SELECT statut FROM relations
        WHERE (utilisateur_id = ? AND ami_id = ?)
           OR (utilisateur_id = ? AND ami_id = ?)
    """, (user_id, ami_id, ami_id, user_id))

    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def envoyer_demande(user_id, ami_id):
    """Envoie une demande d'ami"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO relations (utilisateur_id, ami_id, statut)
            VALUES (?, ?, 'en_attente')
        """, (user_id, ami_id))
        conn.commit()
        conn.close()
        return True, "Demande envoyee!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Demande deja envoyee."
    except Exception as e:
        conn.close()
        return False, f"Erreur: {str(e)}"


def accepter_demande(user_id, ami_id):
    """Accepte une demande d'ami"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE relations SET statut = 'amis'
        WHERE utilisateur_id = ? AND ami_id = ?
    """, (ami_id, user_id))

    conn.commit()
    conn.close()
    return True


def refuser_demande(user_id, ami_id):
    """Refuse une demande d'ami"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM relations
        WHERE utilisateur_id = ? AND ami_id = ?
    """, (ami_id, user_id))

    conn.commit()
    conn.close()
    return True


def supprimer_ami(user_id, ami_id):
    """Supprime une relation d'ami"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM relations
        WHERE (utilisateur_id = ? AND ami_id = ?)
           OR (utilisateur_id = ? AND ami_id = ?)
    """, (user_id, ami_id, ami_id, user_id))

    conn.commit()
    conn.close()
    return True


def get_mes_rivaux(user_id):
    """Récupère la liste des amis validés avec leur rang"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.pseudo, u.prenom,
               COALESCE(SUM(p.points_gagnes), 0) as total_points
        FROM utilisateurs u
        LEFT JOIN predictions p ON u.id = p.user_id
        WHERE u.id IN (
            SELECT CASE
                WHEN r.utilisateur_id = ? THEN r.ami_id
                ELSE r.utilisateur_id
            END
            FROM relations r
            WHERE (r.utilisateur_id = ? OR r.ami_id = ?)
              AND r.statut = 'amis'
        )
        GROUP BY u.id, u.pseudo, u.prenom
        ORDER BY total_points DESC
    """, (user_id, user_id, user_id))

    rivaux = cursor.fetchall()
    conn.close()
    return rivaux


def get_demandes_recues(user_id):
    """Récupère les demandes d'ami en attente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.pseudo, u.prenom
        FROM utilisateurs u
        JOIN relations r ON u.id = r.utilisateur_id
        WHERE r.ami_id = ? AND r.statut = 'en_attente'
    """, (user_id,))

    demandes = cursor.fetchall()
    conn.close()
    return demandes


def get_rang_general(user_id):
    """Récupère le rang d'un utilisateur au classement général"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.id, COALESCE(SUM(p.points_gagnes), 0) as total
            FROM utilisateurs u
            LEFT JOIN predictions p ON u.id = p.user_id
            WHERE u.statut = 'Actif'
            GROUP BY u.id
            ORDER BY total DESC
        """)

        classement = cursor.fetchall()
        for idx, (uid, _) in enumerate(classement):
            if uid == user_id:
                conn.close()
                return idx + 1
    except:
        pass

    conn.close()
    return "--"


def get_comparaison_3_semaines(user_id, ami_id):
    """Récupère la comparaison des points sur les 3 dernières semaines"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    semaine_actuelle = datetime.now().isocalendar()[1]
    semaines = [semaine_actuelle - 2, semaine_actuelle - 1, semaine_actuelle]

    comparaison = []

    for semaine in semaines:
        # Points utilisateur
        cursor.execute("""
            SELECT COALESCE(SUM(p.points_gagnes), 0)
            FROM predictions p
            JOIN matches m ON p.match_id = m.id
            WHERE p.user_id = ? AND m.semaine_id = ?
        """, (user_id, semaine))
        pts_user = cursor.fetchone()[0]

        # Points ami
        cursor.execute("""
            SELECT COALESCE(SUM(p.points_gagnes), 0)
            FROM predictions p
            JOIN matches m ON p.match_id = m.id
            WHERE p.user_id = ? AND m.semaine_id = ?
        """, (ami_id, semaine))
        pts_ami = cursor.fetchone()[0]

        comparaison.append({
            'semaine': semaine,
            'pts_user': pts_user,
            'pts_ami': pts_ami
        })

    conn.close()
    return comparaison


def afficher_amis(user):
    """Affiche le module de gestion des amis/rivaux"""

    # Style CSS Elite
    st.markdown("""
    <style>
        h1, h2, h3 { color: #FFD700 !important; }

        .rival-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #FFD700;
            border-radius: 15px;
            padding: 15px;
            margin: 10px 0;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .rival-card:hover {
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
            transform: translateY(-2px);
        }

        .rival-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #0a0a1a;
            font-weight: bold;
            font-size: 1.3em;
        }

        .demande-card {
            background: linear-gradient(135deg, #2d1f3d 0%, #1a1a2e 100%);
            border: 1px solid #9b59b6;
            border-radius: 10px;
            padding: 12px;
            margin: 8px 0;
        }

        .search-result {
            background: #1a1a2e;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
        }

        .duel-table {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #FFD700;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
        }

        .duel-header {
            text-align: center;
            color: #FFD700;
            font-size: 1.2em;
            margin-bottom: 15px;
        }

        .duel-row {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid #333;
        }

        .win { color: #00FF00; }
        .lose { color: #FF4444; }
        .draw { color: #FFD700; }
    </style>
    """, unsafe_allow_html=True)

    # Header avec bouton retour
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Retour"):
            st.session_state.dashboard_section = None
            st.session_state.selected_rival = None
            st.rerun()

    with col_title:
        st.markdown("## 👥 Mes Rivaux")

    st.markdown("---")

    current_user_id = user['id']

    # Initialiser la session pour le rival sélectionné
    if 'selected_rival' not in st.session_state:
        st.session_state.selected_rival = None

    # === SI UN RIVAL EST SÉLECTIONNÉ: AFFICHER LE DUEL ===
    if st.session_state.selected_rival:
        rival_id = st.session_state.selected_rival['id']
        rival_pseudo = st.session_state.selected_rival['pseudo']

        if st.button("← Retour aux rivaux"):
            st.session_state.selected_rival = None
            st.rerun()

        st.markdown(f"### ⚔️ Duel: Vous vs {rival_pseudo}")

        # Comparaison sur 3 semaines
        comparaison = get_comparaison_3_semaines(current_user_id, rival_id)

        st.markdown("""
        <div class="duel-table">
            <div class="duel-header">📊 Comparaison des 3 dernières semaines</div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.markdown(f"**Vous ({user['pseudo']})**")
        with col2:
            st.markdown("**Semaine**")
        with col3:
            st.markdown(f"**{rival_pseudo}**")

        total_user = 0
        total_rival = 0
        wins = 0

        for comp in comparaison:
            col1, col2, col3 = st.columns([2, 1, 2])

            pts_user = comp['pts_user']
            pts_ami = comp['pts_ami']
            total_user += pts_user
            total_rival += pts_ami

            if pts_user > pts_ami:
                wins += 1
                style_user = "color: #00FF00; font-weight: bold;"
                style_ami = "color: #FF4444;"
            elif pts_user < pts_ami:
                style_user = "color: #FF4444;"
                style_ami = "color: #00FF00; font-weight: bold;"
            else:
                style_user = style_ami = "color: #FFD700;"

            with col1:
                st.markdown(f"<span style='{style_user}'>{pts_user} pts</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"S{comp['semaine']}")
            with col3:
                st.markdown(f"<span style='{style_ami}'>{pts_ami} pts</span>", unsafe_allow_html=True)

        st.markdown("---")

        # Total
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.metric("Total", f"{total_user} pts")
        with col2:
            st.markdown("**TOTAL**")
        with col3:
            st.metric("Total", f"{total_rival} pts")

        # Verdict
        if total_user > total_rival:
            st.success(f"🏆 Vous menez le duel! ({wins}/3 semaines gagnées)")
        elif total_user < total_rival:
            st.error(f"😤 {rival_pseudo} mène le duel!")
        else:
            st.info("🤝 Égalité parfaite!")

        st.markdown("</div>", unsafe_allow_html=True)

        # Option de suppression
        st.markdown("---")
        if st.button(f"❌ Retirer {rival_pseudo} de mes rivaux", type="secondary"):
            supprimer_ami(current_user_id, rival_id)
            st.session_state.selected_rival = None
            st.success("Rival supprimé.")
            st.rerun()

        return

    # === BARRE DE RECHERCHE ===
    st.markdown("### 🔍 Rechercher un joueur")

    search_query = st.text_input(
        "Pseudo",
        placeholder="Entrez un pseudo...",
        label_visibility="collapsed"
    )

    if search_query and len(search_query) >= 2:
        results = rechercher_utilisateur(search_query, current_user_id)

        if results:
            for user_result in results:
                uid, pseudo, prenom = user_result
                relation = get_relation_status(current_user_id, uid)

                col1, col2, col3 = st.columns([1, 3, 2])

                with col1:
                    st.markdown(f"""
                    <div class="rival-avatar">{pseudo[0].upper()}</div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"**{pseudo}**")
                    if prenom:
                        st.caption(prenom)

                with col3:
                    if relation == 'amis':
                        st.success("✓ Déjà rivaux")
                    elif relation == 'en_attente':
                        st.info("⏳ En attente")
                    else:
                        if st.button(f"➕ Ajouter", key=f"add_{uid}"):
                            success, msg = envoyer_demande(current_user_id, uid)
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)
                            st.rerun()

                st.markdown("---")
        else:
            st.info("Aucun joueur trouvé.")

    # === DEMANDES EN ATTENTE ===
    demandes = get_demandes_recues(current_user_id)

    if demandes:
        st.markdown("### 📬 Demandes en attente")

        for demande in demandes:
            uid, pseudo, prenom = demande

            st.markdown(f"""
            <div class="demande-card">
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

            with col1:
                st.markdown(f"""
                <div class="rival-avatar" style="width:40px; height:40px; font-size:1em;">{pseudo[0].upper()}</div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"**{pseudo}** veut devenir votre rival!")

            with col3:
                if st.button("✓", key=f"accept_{uid}", help="Accepter"):
                    accepter_demande(current_user_id, uid)
                    st.success(f"{pseudo} ajouté!")
                    st.rerun()

            with col4:
                if st.button("✗", key=f"decline_{uid}", help="Refuser"):
                    refuser_demande(current_user_id, uid)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

    # === MES RIVAUX ===
    st.markdown("### ⚔️ Mes Rivaux")

    rivaux = get_mes_rivaux(current_user_id)

    if not rivaux:
        st.info("Vous n'avez pas encore de rivaux. Recherchez des joueurs pour les ajouter!")
    else:
        for rival in rivaux:
            rival_id, pseudo, prenom, total_points = rival
            rang = get_rang_general(rival_id)

            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])

            with col1:
                st.markdown(f"""
                <div class="rival-avatar">{pseudo[0].upper()}</div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"**{pseudo}**")
                st.caption(f"#{rang} au classement")

            with col3:
                st.markdown(f"**{total_points}** pts")

            with col4:
                if st.button("⚔️", key=f"duel_{rival_id}", help="Voir le duel"):
                    st.session_state.selected_rival = {
                        'id': rival_id,
                        'pseudo': pseudo
                    }
                    st.rerun()

            st.markdown("---")

    # Stats
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rivaux", len(rivaux))
    with col2:
        st.metric("Demandes", len(demandes))
