"""
Module Reglement pour Elite Pronos
Affichage des 5 articles du reglement officiel
Format: Articles entourés, points soulignés
"""
import streamlit as st
import os

# Chemin vers la mascotte
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')


def afficher_reglement():
    """Affiche le reglement officiel d'Elite Pronos"""

    # Header avec mascotte
    col_title, col_mascot = st.columns([3, 1])
    with col_title:
        st.markdown("## Reglement Officiel")
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo reglement.png")
        if os.path.exists(mascot_path):
            st.image(mascot_path, width=100)

    st.markdown("---")

    # Style CSS pour les articles
    st.markdown("""
    <style>
        .article-box {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #D4AF37;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
        }
        .article-title {
            color: #D4AF37;
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #D4AF37;
        }
        .point-title {
            color: #FFD700;
            font-weight: bold;
            text-decoration: underline;
            margin-top: 12px;
        }
        .point-content {
            color: #FFFFFF;
            margin: 5px 0 10px 0;
            line-height: 1.6;
        }
        .point-list {
            color: #FFFFFF;
            margin-left: 20px;
        }
        .highlight-gold {
            color: #FFD700;
            font-weight: bold;
        }
        .highlight-green {
            color: #00FF00;
            font-weight: bold;
        }
        .highlight-red {
            color: #FF6B6B;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 1 : PARTICIPATION
    # =====================================================
    st.markdown("""
    <div class="article-box">
        <div class="article-title">Article 1 - Participation et Inscription</div>

        <div class="point-title">1.1 Eligibilite</div>
        <div class="point-content">
            Elite Pronos est une ligue privee de pronostics football reservee aux membres invites.
            Toute inscription est soumise a validation par un administrateur.
        </div>

        <div class="point-title">1.2 Periode d'inscription</div>
        <div class="point-content">
            Les inscriptions sont ouvertes <span class="highlight-gold">30 jours avant la Journee 1</span>
            de chaque saison (J1 - 30). Aucune nouvelle inscription n'est acceptee apres le coup d'envoi
            du premier match de la saison.
        </div>

        <div class="point-title">1.3 Compte utilisateur</div>
        <div class="point-content">
            Chaque participant doit creer un compte unique avec :
            <ul class="point-list">
                <li>Un pseudo (minimum 3 caracteres, unique)</li>
                <li>Une adresse email valide</li>
                <li>Un code PIN personnel (minimum 4 caracteres)</li>
            </ul>
        </div>

        <div class="point-title">1.4 Engagement</div>
        <div class="point-content">
            En s'inscrivant, le participant s'engage a respecter l'ensemble du present reglement
            et a participer de bonne foi a la competition.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 2 : PRONOSTICS HEBDOMADAIRES
    # =====================================================
    st.markdown("""
    <div class="article-box">
        <div class="article-title">Article 2 - Pronostics Hebdomadaires</div>

        <div class="point-title">2.1 Selection des matchs</div>
        <div class="point-content">
            Chaque semaine, <span class="highlight-gold">4 matchs sont proposes</span> aux participants.
            Les matchs sont selectionnes prioritairement en Ligue 1, puis dans les autres grands championnats
            europeens (Premier League, Liga, Serie A, Bundesliga).
        </div>

        <div class="point-title">2.2 Format du pronostic</div>
        <div class="point-content">
            Pour chaque match, le participant doit indiquer :
            <ul class="point-list">
                <li>Le <span class="highlight-gold">score exact</span> qu'il predit (ex: 2-1)</li>
                <li>La <span class="highlight-gold">mise en points</span> qu'il souhaite engager</li>
            </ul>
        </div>

        <div class="point-title">2.3 Budget hebdomadaire</div>
        <div class="point-content">
            Chaque semaine, le participant dispose d'un budget de <span class="highlight-gold">100 POINTS</span>
            a repartir obligatoirement sur les 4 matchs.
            <ul class="point-list">
                <li>Mise minimum par match : <span class="highlight-gold">10 points</span></li>
                <li>Mise maximum par match : <span class="highlight-gold">60 points</span></li>
                <li>Total des mises : exactement 100 points</li>
            </ul>
        </div>

        <div class="point-title">2.4 Deadline</div>
        <div class="point-content">
            Les pronostics doivent etre valides <span class="highlight-gold">1 heure avant</span>
            le coup d'envoi du premier match de la semaine. Passe ce delai, aucune modification n'est possible.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 3 : SYSTEME DE POINTS
    # =====================================================
    st.markdown("""
    <div class="article-box">
        <div class="article-title">Article 3 - Systeme de Points</div>

        <div class="point-title">3.1 Resultat 1N2</div>
        <div class="point-content">
            Si le participant trouve le bon resultat (Victoire domicile / Nul / Victoire exterieur) :<br>
            <span class="highlight-gold">Points gagnes = Mise x Cote du resultat</span><br>
            <em>Exemple : Mise 30 pts sur PSG gagnant, cote 1.50 → 30 x 1.50 = 45 pts</em>
        </div>

        <div class="point-title">3.2 Score Exact</div>
        <div class="point-content">
            Si le participant trouve le score exact du match : <span class="highlight-green">+10 POINTS bonus</span>
        </div>

        <div class="point-title">3.3 Mauvais pronostic</div>
        <div class="point-content">
            Si le resultat 1N2 est incorrect : <span class="highlight-red">0 point gagne</span> (la mise est perdue)
        </div>

        <div class="point-title">3.4 Bonus Grand Chelem</div>
        <div class="point-content">
            Si un participant trouve <span class="highlight-gold">4/4 resultats 1N2 corrects</span> sur une meme semaine :
            <span class="highlight-green">+40 POINTS BONUS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 4 : JOKERS
    # =====================================================
    st.markdown("""
    <div class="article-box">
        <div class="article-title">Article 4 - Les Jokers</div>

        <div class="point-content" style="margin-bottom: 15px;">
            Chaque participant dispose de <span class="highlight-gold">3 jokers Points Doubles</span>
            et <span class="highlight-gold">2 jokers Points Voles</span> par saison.
        </div>

        <div class="point-title">4.1 Joker POINTS DOUBLES (x3 par saison)</div>
        <div class="point-content">
            Multiplie par 2 TOUS les points gagnes sur les 4 matchs de la semaine.
            <ul class="point-list">
                <li>Active avant la deadline des pronostics</li>
                <li>Le bonus Grand Chelem est egalement double</li>
            </ul>
        </div>

        <div class="point-title">4.2 Joker POINTS VOLES (x2 par saison)</div>
        <div class="point-content">
            Copie les pronostics d'un adversaire choisi.
            <ul class="point-list">
                <li>Choisissez un adversaire AVANT la deadline</li>
                <li>Vos pronostics sont remplaces par les siens</li>
                <li>Vous gagnez les memes points que lui cette semaine</li>
                <li>L'adversaire n'est pas prevenu</li>
            </ul>
        </div>

        <div class="point-title">4.3 Oubli de pronostics</div>
        <div class="point-content">
            Si un joueur oublie de faire ses pronostics, 1 joker Points Voles sera
            <span class="highlight-gold">automatiquement utilise</span> sur le
            <span class="highlight-gold">dernier du classement</span>.
        </div>

        <div class="point-title">4.4 Regles d'utilisation</div>
        <div class="point-content">
            <ul class="point-list">
                <li>Un seul joker peut etre active par semaine</li>
                <li>Le joker doit etre active AVANT la deadline</li>
                <li>Une fois active, le joker ne peut pas etre annule</li>
                <li>Les jokers non utilises sont perdus en fin de saison</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 5 : CLASSEMENT ET RECOMPENSES
    # =====================================================
    st.markdown("""
    <div class="article-box">
        <div class="article-title">Article 5 - Classement et Recompenses</div>

        <div class="point-title">5.1 Classement general</div>
        <div class="point-content">
            Le classement est etabli selon le <span class="highlight-gold">cumul des points</span>
            gagnes depuis le debut de la saison. En cas d'egalite, les criteres de departage sont :
            <ol class="point-list">
                <li>Nombre de scores exacts trouves</li>
                <li>Nombre de Grand Chelems realises</li>
                <li>Confrontation directe (semaines en commun)</li>
            </ol>
        </div>

        <div class="point-title">5.2 Classement hebdomadaire</div>
        <div class="point-content">
            Un classement de la semaine est publie apres chaque journee,
            permettant de suivre les performances individuelles.
        </div>

        <div class="point-title">5.3 Fin de saison</div>
        <div class="point-content">
            La saison se termine a l'issue de la derniere journee de Ligue 1.
            Le classement final est alors fige.
        </div>

        <div class="point-title">5.4 Podium</div>
        <div class="point-content" style="text-align: center; font-size: 1.2em;">
            🥇 <span style="color: #FFD700;">1er - Champion</span> &nbsp;&nbsp;
            🥈 <span style="color: #C0C0C0;">2eme - Vice-Champion</span> &nbsp;&nbsp;
            🥉 <span style="color: #CD7F32;">3eme - Bronze</span>
        </div>

        <div class="point-title">5.5 Fair-play</div>
        <div class="point-content">
            Tout comportement antisportif (multi-comptes, collusion, triche) entraine la
            <span class="highlight-red">disqualification immediate</span> et definitive du participant.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.caption("Reglement officiel Elite Pronos - Saison 2025-2026")
    st.markdown("**Que le meilleur pronostiqueur gagne !**")
