"""
Module Reglement pour Elite Pronos
Affichage des 5 articles du reglement officiel
"""
import streamlit as st


def afficher_reglement():
    """Affiche le reglement officiel d'Elite Pronos"""

    # Style CSS - texte noir, titres or, sans blocs blancs
    st.markdown("""
    <style>
        .article-title {
            color: #D4AF37 !important;
            font-size: 1.3em !important;
            font-weight: bold !important;
            border-bottom: 2px solid #D4AF37 !important;
            padding-bottom: 8px !important;
            margin: 15px 0 10px 0 !important;
        }

        .article-section {
            color: #D4AF37 !important;
            font-size: 1.1em !important;
            font-weight: bold !important;
            margin-right: 8px !important;
        }

        .reglement-text {
            color: #000000 !important;
            line-height: 1.6 !important;
        }

        .reglement-text p {
            color: #000000 !important;
            margin: 8px 0 !important;
        }

        .reglement-text ul, .reglement-text ol {
            color: #000000 !important;
            margin: 8px 0 8px 25px !important;
        }

        .reglement-text li {
            color: #000000 !important;
            margin: 4px 0 !important;
        }

        .reglement-text strong {
            color: #000000 !important;
        }

        .highlight-gold {
            color: #D4AF37 !important;
            font-weight: bold !important;
        }

        .text-red {
            color: #ff6b6b !important;
        }

        .text-green {
            color: #00CC00 !important;
        }

        .text-purple {
            color: #9b59b6 !important;
        }

        .text-orange {
            color: #ff9800 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("## Reglement Officiel")
    st.markdown("---")

    # =====================================================
    # ARTICLE 1 : PARTICIPATION
    # =====================================================
    with st.expander("ARTICLE 1 : PARTICIPATION ET INSCRIPTION", expanded=True):
        st.markdown("""
        <div class="reglement-text">
            <div class="article-title">Article 1 - Participation et Inscription</div>

            <p><span class="article-section">1.1</span> <strong>Eligibilite</strong></p>
            <p>Elite Pronos est une ligue privee de pronostics football reservee aux membres invites.
            Toute inscription est soumise a validation par un administrateur.</p>

            <p><span class="article-section">1.2</span> <strong>Periode d'inscription</strong></p>
            <p>Les inscriptions sont ouvertes <span class="highlight-gold">30 jours avant la Journee 1</span>
            de chaque saison (J1 - 30). Aucune nouvelle inscription n'est acceptee apres le coup d'envoi
            du premier match de la saison.</p>

            <p><span class="article-section">1.3</span> <strong>Compte utilisateur</strong></p>
            <p>Chaque participant doit creer un compte unique avec :</p>
            <ul>
                <li>Un pseudo (minimum 3 caracteres, unique)</li>
                <li>Une adresse email valide</li>
                <li>Un code PIN personnel (minimum 4 caracteres)</li>
            </ul>

            <p><span class="article-section">1.4</span> <strong>Engagement</strong></p>
            <p>En s'inscrivant, le participant s'engage a respecter l'ensemble du present reglement
            et a participer de bonne foi a la competition.</p>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 2 : PRONOSTICS HEBDOMADAIRES
    # =====================================================
    with st.expander("ARTICLE 2 : PRONOSTICS HEBDOMADAIRES", expanded=True):
        st.markdown("""
        <div class="reglement-text">
            <div class="article-title">Article 2 - Pronostics Hebdomadaires</div>

            <p><span class="article-section">2.1</span> <strong>Selection des matchs</strong></p>
            <p>Chaque semaine, <span class="highlight-gold">des matchs sont proposes aux participants en fonction de leur cote</span>.
            Les matchs sont selectionnes prioritairement en Ligue 1, puis dans les autres grands championnats
            europeens (Premier League, Liga, Serie A, Bundesliga).</p>

            <p><span class="article-section">2.2</span> <strong>Format du pronostic</strong></p>
            <p>Pour chaque match, le participant doit indiquer :</p>
            <ul>
                <li>Le <span class="highlight-gold">score exact</span> qu'il predit (ex: 2-1)</li>
                <li>La <span class="highlight-gold">mise en points</span> qu'il souhaite engager</li>
            </ul>

            <p><span class="article-section">2.3</span> <strong>Budget hebdomadaire</strong></p>
            <p>Chaque semaine, le participant dispose d'un budget de <span class="highlight-gold">100 POINTS</span>
            a repartir obligatoirement sur les matchs.</p>
            <ul>
                <li>Mise minimum par match : <span class="highlight-gold">10 points</span></li>
                <li>Mise maximum par match : <span class="highlight-gold">60 points</span></li>
                <li>Total des mises : exactement 100 points</li>
            </ul>

            <p><span class="article-section">2.4</span> <strong>Deadline</strong></p>
            <p>Les pronostics doivent etre valides <span class="highlight-gold">1 heure avant</span>
            le coup d'envoi du premier match de la semaine. Passe ce delai, aucune modification n'est possible.</p>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 3 : SYSTEME DE POINTS
    # =====================================================
    with st.expander("ARTICLE 3 : SYSTEME DE POINTS", expanded=True):
        st.markdown("""
        <div class="reglement-text">
            <div class="article-title">Article 3 - Systeme de Points</div>

            <p><span class="article-section">3.1</span> <strong>Resultat 1N2</strong></p>
            <p>Si le participant trouve le bon resultat (Victoire domicile / Nul / Victoire exterieur) :</p>
            <p><span class="highlight-gold">Points gagnes = Mise x Cote du resultat</span></p>
            <p>Exemple : Mise 30 pts sur PSG gagnant, cote 1.50 → 30 x 1.50 = 45 pts</p>

            <p><span class="article-section">3.2</span> <strong>Score Exact</strong></p>
            <p>Si le participant trouve le score exact du match :</p>
            <p><span class="highlight-gold">+10 POINTS par bon score</span></p>

            <p><span class="article-section">3.3</span> <strong>Mauvais pronostic</strong></p>
            <p>Si le resultat 1N2 est incorrect : <span class="text-red">0 point gagne</span> (la mise est perdue)</p>

            <p><span class="article-section">3.4</span> <strong>Bonus Grand Chelem</strong></p>
            <p>Si un participant trouve tous les resultats 1N2 corrects sur une meme semaine :</p>
            <p><span class="text-green">+40 POINTS BONUS</span> qui seront cumules pour la journee suivante.</p>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 4 : JOKERS
    # =====================================================
    with st.expander("ARTICLE 4 : LES JOKERS", expanded=True):
        st.markdown("""
        <div class="reglement-text">
            <div class="article-title">Article 4 - Les Jokers</div>

            <p>Chaque participant dispose de <span class="highlight-gold">3 jokers Points Doubles</span>
            et <span class="highlight-gold">2 jokers Points Voles</span> par saison, a utiliser strategiquement.</p>

            <p><span class="article-section">4.1</span> <strong>Joker POINTS DOUBLES (x3 par saison)</strong></p>
            <p><span class="text-purple">x2 sur tous les gains de la semaine</span></p>
            <ul>
                <li>Active avant la deadline des pronostics</li>
                <li>Multiplie par 2 TOUS les points gagnes sur les matchs</li>
                <li>Le bonus Grand Chelem est egalement double</li>
            </ul>

            <p><span class="article-section">4.2</span> <strong>Joker POINTS VOLES (x2 par saison)</strong></p>
            <p><span class="text-red">Copie les pronostics d'un adversaire</span></p>
            <ul>
                <li>Choisissez un adversaire AVANT la deadline</li>
                <li>Vos pronostics sont remplaces par les siens</li>
                <li>Vous gagnez les memes points que lui cette semaine</li>
                <li>L'adversaire n'est pas prevenu</li>
            </ul>

            <p><span class="article-section">4.3</span> <strong>Oubli de pronostics</strong></p>
            <p><span class="text-orange">Si un joueur oublie de faire ses pronostics :</span></p>
            <p>1 joker Points Voles sera automatiquement utilise sur le <span class="highlight-gold">dernier du classement</span>.</p>

            <p><span class="article-section">4.4</span> <strong>Regles d'utilisation</strong></p>
            <ul>
                <li>Un seul joker peut etre active par semaine</li>
                <li>Le joker doit etre active AVANT la deadline</li>
                <li>Une fois active, le joker ne peut pas etre annule</li>
                <li>Les jokers non utilises sont perdus en fin de saison</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 5 : CLASSEMENT ET RECOMPENSES
    # =====================================================
    with st.expander("ARTICLE 5 : CLASSEMENT ET RECOMPENSES", expanded=True):
        st.markdown("""
        <div class="reglement-text">
            <div class="article-title">Article 5 - Classement et Recompenses</div>

            <p><span class="article-section">5.1</span> <strong>Classement general</strong></p>
            <p>Le classement est etabli selon le <span class="highlight-gold">cumul des points</span>
            gagnes depuis le debut de la saison. En cas d'egalite, les criteres de departage sont :</p>
            <ol>
                <li>Nombre de scores exacts trouves</li>
                <li>Nombre de Grand Chelems realises</li>
                <li>Confrontation directe (semaines en commun)</li>
            </ol>

            <p><span class="article-section">5.2</span> <strong>Classement hebdomadaire</strong></p>
            <p>Un classement de la semaine est publie apres chaque journee, permettant de suivre
            les performances individuelles match par match.</p>

            <p><span class="article-section">5.3</span> <strong>Fin de saison</strong></p>
            <p>La saison se termine a l'issue de la derniere journee de Ligue 1.
            Le classement final est alors fige.</p>

            <p><span class="article-section">5.4</span> <strong>Podium</strong></p>
            <p style="text-align: center; font-size: 1.5em;">
                🥇 <span style="color: #FFD700;">1er - Champion</span> &nbsp;&nbsp;
                🥈 <span style="color: #C0C0C0;">2eme - Vice-Champion</span> &nbsp;&nbsp;
                🥉 <span style="color: #CD7F32;">3eme - Bronze</span>
            </p>

            <p><span class="article-section">5.5</span> <strong>Fair-play</strong></p>
            <p>Tout comportement antisportif (multi-comptes, collusion, triche) entraine
            la <span class="text-red">disqualification immediate</span> et definitive du participant.</p>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888888; font-size: 0.9em;">
        <p>Reglement officiel Elite Pronos - Saison 2025-2026</p>
        <p style="color: #D4AF37;">Que le meilleur pronostiqueur gagne !</p>
    </div>
    """, unsafe_allow_html=True)
