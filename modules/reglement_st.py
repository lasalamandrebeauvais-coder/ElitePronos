"""
Module Reglement pour Elite Pronos
Affichage des 5 articles du reglement officiel
"""
import streamlit as st


def afficher_reglement():
    """Affiche le reglement officiel d'Elite Pronos"""

    # Style CSS specifique pour le reglement - Design Cartes Blanches
    st.markdown("""
    <style>
        .reglement-container {
            background: #FFFFFF !important;
            border: 3px solid #D4AF37;
            border-radius: 15px;
            padding: 25px;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
        }

        .article-title {
            color: #D4AF37 !important;
            font-size: 1.4em;
            font-weight: bold;
            border-bottom: 2px solid #D4AF37;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }

        .article-content {
            color: #001529 !important;
            line-height: 1.8;
        }

        .article-content p {
            color: #001529 !important;
        }

        .article-content ul {
            margin-left: 20px;
        }

        .article-content li {
            margin: 8px 0;
            color: #001529 !important;
        }

        .article-content ol li {
            color: #001529 !important;
        }

        .article-content strong {
            color: #001529 !important;
        }

        .highlight-gold {
            color: #D4AF37 !important;
            font-weight: bold;
        }

        .highlight-box {
            background: rgba(212, 175, 55, 0.15);
            border: 2px solid #D4AF37;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }

        .highlight-box p {
            color: #001529 !important;
        }

        .highlight-box li {
            color: #001529 !important;
        }

        .emoji-big {
            font-size: 1.5em;
            margin-right: 10px;
            color: #D4AF37 !important;
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
        <div class="reglement-container">
            <div class="article-title">Article 1 - Participation et Inscription</div>
            <div class="article-content">
                <p><span class="emoji-big">1.1</span> <strong>Eligibilite</strong></p>
                <p>Elite Pronos est une ligue privee de pronostics football reservee aux membres invites.
                Toute inscription est soumise a validation par un administrateur.</p>

                <p><span class="emoji-big">1.2</span> <strong>Periode d'inscription</strong></p>
                <p>Les inscriptions sont ouvertes <span class="highlight-gold">30 jours avant la Journee 1</span>
                de chaque saison (J1 - 30). Aucune nouvelle inscription n'est acceptee apres le coup d'envoi
                du premier match de la saison.</p>

                <p><span class="emoji-big">1.3</span> <strong>Compte utilisateur</strong></p>
                <p>Chaque participant doit creer un compte unique avec :</p>
                <ul>
                    <li>Un pseudo (minimum 3 caracteres, unique)</li>
                    <li>Une adresse email valide</li>
                    <li>Un code PIN personnel (minimum 4 caracteres)</li>
                </ul>

                <p><span class="emoji-big">1.4</span> <strong>Engagement</strong></p>
                <p>En s'inscrivant, le participant s'engage a respecter l'ensemble du present reglement
                et a participer de bonne foi a la competition.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 2 : PRONOSTICS HEBDOMADAIRES
    # =====================================================
    with st.expander("ARTICLE 2 : PRONOSTICS HEBDOMADAIRES", expanded=True):
        st.markdown("""
        <div class="reglement-container">
            <div class="article-title">Article 2 - Pronostics Hebdomadaires</div>
            <div class="article-content">
                <p><span class="emoji-big">2.1</span> <strong>Selection des matchs</strong></p>
                <p>Chaque semaine, <span class="highlight-gold">4 matchs</span> sont proposes aux participants.
                Les matchs sont selectionnes prioritairement en Ligue 1, puis dans les autres grands championnats
                europeens (Premier League, Liga, Serie A, Bundesliga).</p>

                <p><span class="emoji-big">2.2</span> <strong>Format du pronostic</strong></p>
                <p>Pour chaque match, le participant doit indiquer :</p>
                <ul>
                    <li>Le <span class="highlight-gold">score exact</span> qu'il predit (ex: 2-1)</li>
                    <li>La <span class="highlight-gold">mise en points</span> qu'il souhaite engager</li>
                </ul>

                <p><span class="emoji-big">2.3</span> <strong>Budget hebdomadaire</strong></p>
                <div class="highlight-box">
                    <p>Chaque semaine, le participant dispose d'un budget de <span class="highlight-gold">100 POINTS</span>
                    a repartir obligatoirement sur les 4 matchs.</p>
                    <ul>
                        <li>Mise minimum par match : <span class="highlight-gold">10 points</span></li>
                        <li>Mise maximum par match : <span class="highlight-gold">60 points</span></li>
                        <li>Total des mises : exactement 100 points</li>
                    </ul>
                </div>

                <p><span class="emoji-big">2.4</span> <strong>Deadline</strong></p>
                <p>Les pronostics doivent etre valides <span class="highlight-gold">1 heure avant</span>
                le coup d'envoi du premier match de la semaine. Passe ce delai, aucune modification n'est possible.</p>

                <p><span class="emoji-big">2.5</span> <strong>Defaut de pronostic</strong></p>
                <p>Si un participant ne saisit pas ses pronostics avant la deadline, le systeme lui attribue
                automatiquement les pronostics du <span class="highlight-gold">dernier du classement</span>.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 3 : SYSTEME DE POINTS
    # =====================================================
    with st.expander("ARTICLE 3 : SYSTEME DE POINTS", expanded=True):
        st.markdown("""
        <div class="reglement-container">
            <div class="article-title">Article 3 - Systeme de Points</div>
            <div class="article-content">
                <p><span class="emoji-big">3.1</span> <strong>Resultat 1N2</strong></p>
                <p>Si le participant trouve le bon resultat (Victoire domicile / Nul / Victoire exterieur) :</p>
                <div class="highlight-box">
                    <p><span class="highlight-gold">Points gagnes = Mise x Cote du resultat</span></p>
                    <p style="color: #555555; font-size: 0.9em;">Exemple : Mise 30 pts sur PSG gagnant, cote 1.50 → 30 x 1.50 = 45 pts</p>
                </div>

                <p><span class="emoji-big">3.2</span> <strong>Score Exact</strong></p>
                <p>Si le participant trouve le <span class="highlight-gold">score exact</span> du match :</p>
                <div class="highlight-box">
                    <p><span class="highlight-gold">BONUS : +10 POINTS FIXES</span></p>
                    <p style="color: #555555; font-size: 0.9em;">Exemple : Mise 20, cote 2.0 avec score exact → (20 x 2.0) + 10 = 50 pts</p>
                </div>

                <p><span class="emoji-big">3.3</span> <strong>Mauvais pronostic</strong></p>
                <p>Si le resultat 1N2 est incorrect :</p>
                <div class="highlight-box" style="border-color: #ff6b6b; background: rgba(255, 107, 107, 0.1);">
                    <p style="color: #ff6b6b;"><strong>0 point gagne</strong> (la mise est perdue)</p>
                </div>

                <p><span class="emoji-big">3.4</span> <strong>Bonus Grand Chelem</strong></p>
                <p>Si un participant trouve les <span class="highlight-gold">4 resultats 1N2 corrects</span>
                sur une meme semaine :</p>
                <div class="highlight-box" style="border-color: #00FF00; background: rgba(0, 255, 0, 0.1);">
                    <p style="color: #00FF00;"><strong>BONUS GRAND CHELEM : +40 POINTS</strong></p>
                    <p style="color: #555555; font-size: 0.9em;">Applique sur la semaine SUIVANTE</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 4 : JOKERS
    # =====================================================
    with st.expander("ARTICLE 4 : LES JOKERS", expanded=True):
        st.markdown("""
        <div class="reglement-container">
            <div class="article-title">Article 4 - Les Jokers</div>
            <div class="article-content">
                <p>Chaque participant dispose de <span class="highlight-gold">2 jokers par saison</span>,
                a utiliser strategiquement.</p>

                <p><span class="emoji-big">4.1</span> <strong>Joker POINTS DOUBLES</strong></p>
                <div class="highlight-box" style="border-color: #9b59b6; background: rgba(155, 89, 182, 0.1);">
                    <p style="color: #9b59b6; font-size: 1.2em;"><strong>x2 sur tous les gains de la semaine</strong></p>
                    <ul>
                        <li>Active avant la deadline des pronostics</li>
                        <li>Multiplie par 2 TOUS les points gagnes sur les 4 matchs</li>
                        <li>Le bonus Grand Chelem est egalement double</li>
                        <li>Utilisable <span class="highlight-gold">1 seule fois</span> par saison</li>
                    </ul>
                </div>

                <p><span class="emoji-big">4.2</span> <strong>Joker POINTS VOLES</strong></p>
                <div class="highlight-box" style="border-color: #e74c3c; background: rgba(231, 76, 60, 0.1);">
                    <p style="color: #e74c3c; font-size: 1.2em;"><strong>Copie les pronostics d'un adversaire</strong></p>
                    <ul>
                        <li>Choisissez un adversaire AVANT la deadline</li>
                        <li>Vos pronostics sont remplaces par les siens</li>
                        <li>Vous gagnez les memes points que lui cette semaine</li>
                        <li>L'adversaire n'est pas prevenu</li>
                        <li>Utilisable <span class="highlight-gold">1 seule fois</span> par saison</li>
                    </ul>
                </div>

                <p><span class="emoji-big">4.3</span> <strong>Regles d'utilisation</strong></p>
                <ul>
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
    with st.expander("ARTICLE 5 : CLASSEMENT ET RECOMPENSES", expanded=True):
        st.markdown("""
        <div class="reglement-container">
            <div class="article-title">Article 5 - Classement et Recompenses</div>
            <div class="article-content">
                <p><span class="emoji-big">5.1</span> <strong>Classement general</strong></p>
                <p>Le classement est etabli selon le <span class="highlight-gold">cumul des points</span>
                gagnes depuis le debut de la saison. En cas d'egalite, les criteres de departage sont :</p>
                <ol>
                    <li>Nombre de scores exacts trouves</li>
                    <li>Nombre de Grand Chelems realises</li>
                    <li>Confrontation directe (semaines en commun)</li>
                </ol>

                <p><span class="emoji-big">5.2</span> <strong>Classement hebdomadaire</strong></p>
                <p>Un classement de la semaine est publie apres chaque journee, permettant de suivre
                les performances individuelles match par match.</p>

                <p><span class="emoji-big">5.3</span> <strong>Fin de saison</strong></p>
                <p>La saison se termine a l'issue de la derniere journee de Ligue 1.
                Le classement final est alors fige.</p>

                <p><span class="emoji-big">5.4</span> <strong>Podium</strong></p>
                <div class="highlight-box">
                    <div style="display: flex; justify-content: center; gap: 30px; text-align: center;">
                        <div>
                            <div style="font-size: 2em;">🥇</div>
                            <div style="color: #FFD700; font-weight: bold;">1er</div>
                            <div style="color: #555555; font-size: 0.9em;">Champion</div>
                        </div>
                        <div>
                            <div style="font-size: 2em;">🥈</div>
                            <div style="color: #C0C0C0; font-weight: bold;">2eme</div>
                            <div style="color: #555555; font-size: 0.9em;">Vice-Champion</div>
                        </div>
                        <div>
                            <div style="font-size: 2em;">🥉</div>
                            <div style="color: #CD7F32; font-weight: bold;">3eme</div>
                            <div style="color: #555555; font-size: 0.9em;">Bronze</div>
                        </div>
                    </div>
                </div>

                <p><span class="emoji-big">5.5</span> <strong>Fair-play</strong></p>
                <p>Tout comportement antisportif (multi-comptes, collusion, triche) entraine
                la <span style="color: #ff6b6b;">disqualification immediate</span> et definitive du participant.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #555555; font-size: 0.9em;">
        <p>Reglement officiel Elite Pronos - Saison 2025-2026</p>
        <p style="color: #D4AF37;">Que le meilleur pronostiqueur gagne !</p>
    </div>
    """, unsafe_allow_html=True)
