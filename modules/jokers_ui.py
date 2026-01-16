"""
Module UI pour les Jokers - Elite Pronos
Composants visuels et ancres CSS/JS pour les animations
"""
import streamlit as st


def inject_jokers_css():
    """
    Injecte les styles CSS pour les animations de jokers.
    Ancres préparées pour les animations futures.
    """
    st.markdown("""
    <style>
        /* ============================================ */
        /* JOKER POINTS DOUBLES (👑x2) - Halo Doré */
        /* ============================================ */

        .joker-double-active {
            position: relative;
            animation: halo-pulse 2s ease-in-out infinite;
        }

        .joker-double-active::before {
            content: '';
            position: absolute;
            top: -5px;
            left: -5px;
            right: -5px;
            bottom: -5px;
            background: linear-gradient(45deg, #FFD700, #FFA500, #FFD700);
            border-radius: 20px;
            z-index: -1;
            opacity: 0.7;
            animation: halo-glow 2s ease-in-out infinite;
        }

        @keyframes halo-pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }

        @keyframes halo-glow {
            0%, 100% { opacity: 0.5; filter: blur(10px); }
            50% { opacity: 0.8; filter: blur(15px); }
        }

        .joker-double-badge {
            position: absolute;
            top: -10px;
            right: -10px;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #0a0a1a;
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
            animation: badge-bounce 1s ease-in-out infinite;
        }

        @keyframes badge-bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-3px); }
        }

        /* ============================================ */
        /* JOKER POINTS VOLÉS (✋➡️) - Grille Grisée */
        /* ============================================ */

        .joker-vol-active {
            position: relative;
            opacity: 0.85;
        }

        .joker-vol-active::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                rgba(128, 128, 128, 0.1) 10px,
                rgba(128, 128, 128, 0.1) 20px
            );
            pointer-events: none;
            border-radius: 15px;
        }

        .joker-vol-badge {
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #9b59b6, #8e44ad);
            color: white;
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 15px;
            font-size: 0.8em;
            box-shadow: 0 0 15px rgba(155, 89, 182, 0.5);
        }

        .vol-target-info {
            text-align: center;
            color: #9b59b6;
            font-style: italic;
            margin-top: 10px;
            padding: 10px;
            background: rgba(155, 89, 182, 0.1);
            border-radius: 10px;
            border: 1px dashed #9b59b6;
        }

        /* ============================================ */
        /* COFFRE-FORT (Pronostics verrouillés) */
        /* ============================================ */

        .coffre-fort {
            position: relative;
            border: 3px solid #FFD700;
            border-radius: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }

        .coffre-fort::before {
            content: '🔒';
            position: absolute;
            top: -15px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 1.5em;
            background: #0a0a1a;
            padding: 0 10px;
        }

        .coffre-fort-locked {
            pointer-events: none;
            opacity: 0.7;
        }

        .coffre-fort-locked::after {
            content: 'VERROUILLÉ';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 0, 0, 0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: bold;
        }

        /* ============================================ */
        /* CARTES DE SÉLECTION DE JOKER */
        /* ============================================ */

        .joker-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #444;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 150px;
        }

        .joker-card:hover {
            border-color: #FFD700;
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.2);
        }

        .joker-card-selected {
            border-color: #FFD700 !important;
            background: linear-gradient(135deg, #2a2a3e 0%, #1a3a5e 100%) !important;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
        }

        .joker-card-disabled {
            opacity: 0.5;
            cursor: not-allowed;
            border-color: #333 !important;
        }

        .joker-card-disabled:hover {
            transform: none;
            box-shadow: none;
        }

        .joker-icon {
            font-size: 3em;
            margin-bottom: 10px;
        }

        .joker-name {
            font-size: 1.1em;
            font-weight: bold;
            color: #FFD700;
            margin-bottom: 5px;
        }

        .joker-description {
            font-size: 0.85em;
            color: #888;
        }

        .joker-stock {
            margin-top: 10px;
            font-size: 0.9em;
            color: #FFD700;
        }

        /* ============================================ */
        /* GRAND CHELEM */
        /* ============================================ */

        .grand-chelem-banner {
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%);
            color: #0a0a1a;
            text-align: center;
            padding: 20px;
            border-radius: 15px;
            font-size: 1.5em;
            font-weight: bold;
            animation: grand-chelem-shine 3s ease-in-out infinite;
            margin: 20px 0;
        }

        @keyframes grand-chelem-shine {
            0%, 100% {
                box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
                background-position: 0% 50%;
            }
            50% {
                box-shadow: 0 0 40px rgba(255, 215, 0, 0.8);
                background-position: 100% 50%;
            }
        }

        /* ============================================ */
        /* SÉLECTEUR DE CIBLE POUR VOL */
        /* ============================================ */

        .cible-selector {
            background: #1a1a2e;
            border: 1px solid #9b59b6;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }

        .cible-option {
            display: flex;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .cible-option:hover {
            background: rgba(155, 89, 182, 0.2);
        }

        .cible-option-selected {
            background: rgba(155, 89, 182, 0.3);
            border: 1px solid #9b59b6;
        }

        .cible-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #9b59b6, #8e44ad);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            margin-right: 15px;
        }

        .cible-info {
            flex: 1;
        }

        .cible-pseudo {
            font-weight: bold;
            color: white;
        }

        .cible-rang {
            font-size: 0.85em;
            color: #888;
        }
    </style>
    """, unsafe_allow_html=True)


def inject_jokers_js():
    """
    Injecte le JavaScript pour les interactions de jokers.
    """
    st.markdown("""
    <script>
        // Fonction pour activer l'animation du halo doré
        function activerHaloDouble(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.classList.add('joker-double-active');
            }
        }

        // Fonction pour activer l'effet de vol
        function activerEffetVol(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.classList.add('joker-vol-active');
            }
        }

        // Fonction pour le coffre-fort
        function verrouillerCoffreFort(elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.classList.add('coffre-fort-locked');
            }
        }

        // Animation de confettis pour le Grand Chelem
        function celebrerGrandChelem() {
            // Placeholder pour future intégration avec une lib de confettis
            console.log('🏆 GRAND CHELEM CÉLÉBRÉ!');
        }
    </script>
    """, unsafe_allow_html=True)


def afficher_carte_joker(type_joker, stock, is_selected=False, is_disabled=False):
    """
    Affiche une carte de joker cliquable.

    Args:
        type_joker: 'double' ou 'vol'
        stock: nombre de jokers disponibles
        is_selected: si le joker est actuellement sélectionné
        is_disabled: si le joker est indisponible
    """
    if type_joker == 'double':
        icon = "👑"
        name = "POINTS DOUBLES"
        description = "×2 sur tous vos gains de la semaine"
        color = "#FFD700"
    else:
        icon = "✋"
        name = "POINTS VOLÉS"
        description = "Copiez les pronostics d'un rival"
        color = "#9b59b6"

    card_class = "joker-card"
    if is_selected:
        card_class += " joker-card-selected"
    if is_disabled or stock <= 0:
        card_class += " joker-card-disabled"

    st.markdown(f"""
    <div class="{card_class}">
        <div class="joker-icon">{icon}</div>
        <div class="joker-name" style="color: {color};">{name}</div>
        <div class="joker-description">{description}</div>
        <div class="joker-stock">Stock: {stock}</div>
    </div>
    """, unsafe_allow_html=True)


def afficher_badge_joker_actif(type_joker, cible_pseudo=None):
    """
    Affiche le badge indiquant qu'un joker est actif.
    """
    if type_joker == 'DOUBLE':
        st.markdown("""
        <div class="joker-double-badge">👑 ×2 ACTIF</div>
        """, unsafe_allow_html=True)
    elif type_joker in ('VOL', 'VOL_AUTO'):
        st.markdown(f"""
        <div class="joker-vol-badge">✋ VOL ACTIF</div>
        <div class="vol-target-info">
            Pronostics copiés de: <strong>{cible_pseudo or 'N/A'}</strong>
        </div>
        """, unsafe_allow_html=True)


def afficher_banner_grand_chelem():
    """Affiche la bannière Grand Chelem"""
    st.markdown("""
    <div class="grand-chelem-banner">
        🏆 GRAND CHELEM ! 🏆<br>
        <small>+50 points bonus</small>
    </div>
    """, unsafe_allow_html=True)
