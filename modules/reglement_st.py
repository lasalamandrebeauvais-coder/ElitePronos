"""
Module Reglement pour Elite Pronos
Affichage des 5 articles du reglement officiel
"""
import streamlit as st


def afficher_reglement():
    """Affiche le reglement officiel d'Elite Pronos"""

    # Style CSS specifique pour le reglement - Design Cartes Blanches
    # Texte NOIR sur fond blanc, blocs flexibles
    st.markdown("""
    <style>
        /* Container principal - fond blanc, hauteur flexible */
        div.reglement-container,
        .stMarkdown div.reglement-container {
            background: #FFFFFF !important;
            border: 3px solid #D4AF37 !important;
            border-radius: 15px !important;
            padding: 20px !important;
            margin: 10px 0 !important;
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3) !important;
            height: auto !important;
            min-height: fit-content !important;
            overflow: visible !important;
        }

        /* Titre article - Or */
        div.reglement-container div.article-title,
        .stMarkdown div.reglement-container div.article-title {
            color: #D4AF37 !important;
            font-size: 1.3em !important;
            font-weight: bold !important;
            border-bottom: 2px solid #D4AF37 !important;
            padding-bottom: 8px !important;
            margin-bottom: 12px !important;
        }

        /* Contenu article - NOIR */
        div.reglement-container div.article-content,
        .stMarkdown div.reglement-container div.article-content {
            color: #000000 !important;
            line-height: 1.6 !important;
        }

        /* Tous les paragraphes - NOIR */
        div.reglement-container div.article-content p,
        div.reglement-container div.article-content span,
        .stMarkdown div.reglement-container div.article-content p,
        .stMarkdown div.reglement-container div.article-content span {
            color: #000000 !important;
            margin-bottom: 8px !important;
        }

        /* Listes - NOIR */
        div.reglement-container div.article-content ul,
        div.reglement-container div.article-content ol,
        .stMarkdown div.reglement-container div.article-content ul,
        .stMarkdown div.reglement-container div.article-content ol {
            margin-left: 20px !important;
            color: #000000 !important;
            padding-left: 0 !important;
        }

        div.reglement-container div.article-content li,
        .stMarkdown div.reglement-container div.article-content li {
            margin: 5px 0 !important;
            color: #000000 !important;
        }

        /* Strong/Bold - NOIR */
        div.reglement-container div.article-content strong,
        .stMarkdown div.reglement-container div.article-content strong {
            color: #000000 !important;
        }

        /* Texte dore pour mise en valeur */
        div.reglement-container span.highlight-gold,
        .stMarkdown div.reglement-container span.highlight-gold {
            color: #D4AF37 !important;
            font-weight: bold !important;
        }

        /* Boxes de mise en valeur - hauteur flexible */
        div.reglement-container div.highlight-box,
        .stMarkdown div.reglement-container div.highlight-box {
            background: rgba(212, 175, 55, 0.15) !important;
            border: 2px solid #D4AF37 !important;
            border-radius: 10px !important;
            padding: 12px !important;
            margin: 10px 0 !important;
            height: auto !important;
            min-height: fit-content !important;
        }

        div.reglement-container div.highlight-box p,
        div.reglement-container div.highlight-box span,
        div.reglement-container div.highlight-box li,
        .stMarkdown div.reglement-container div.highlight-box p,
        .stMarkdown div.reglement-container div.highlight-box span,
        .stMarkdown div.reglement-container div.highlight-box li {
            color: #000000 !important;
        }

        /* Numeros d'article - Or */
        div.reglement-container span.emoji-big,
        .stMarkdown div.reglement-container span.emoji-big {
            font-size: 1.3em !important;
            margin-right: 8px !important;
            color: #D4AF37 !important;
        }

        /* Override force pour tous les elements texte - NOIR */
        div.reglement-container *:not(.article-title):not(.highlight-gold):not(.emoji-big) {
            color: #000000 !important;
        }

        /* Garder les titres en Or */
        div.reglement-container .article-title {
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
        <div class="reglement-container" style="background: #FFFFFF !important; height: auto !important;">
            <div class="article-title" style="color: #D4AF37 !important;">Article 1 - Participation et Inscription</div>
            <div class="article-content" style="color: #000000 !important;">
                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">1.1</span> <strong style="color: #000000 !important;">Eligibilite</strong></p>
                <p style="color: #000000 !important;">Elite Pronos est une ligue privee de pronostics football reservee aux membres invites.
                Toute inscription est soumise a validation par un administrateur.</p>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">1.2</span> <strong style="color: #000000 !important;">Periode d'inscription</strong></p>
                <p style="color: #000000 !important;">Les inscriptions sont ouvertes <span class="highlight-gold" style="color: #D4AF37 !important;">30 jours avant la Journee 1</span>
                de chaque saison (J1 - 30). Aucune nouvelle inscription n'est acceptee apres le coup d'envoi
                du premier match de la saison.</p>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">1.3</span> <strong style="color: #000000 !important;">Compte utilisateur</strong></p>
                <p style="color: #000000 !important;">Chaque participant doit creer un compte unique avec :</p>
                <ul style="color: #000000 !important;">
                    <li style="color: #000000 !important;">Un pseudo (minimum 3 caracteres, unique)</li>
                    <li style="color: #000000 !important;">Une adresse email valide</li>
                    <li style="color: #000000 !important;">Un code PIN personnel (minimum 4 caracteres)</li>
                </ul>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">1.4</span> <strong style="color: #000000 !important;">Engagement</strong></p>
                <p style="color: #000000 !important;">En s'inscrivant, le participant s'engage a respecter l'ensemble du present reglement
                et a participer de bonne foi a la competition.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 2 : PRONOSTICS HEBDOMADAIRES
    # =====================================================
    with st.expander("ARTICLE 2 : PRONOSTICS HEBDOMADAIRES", expanded=True):
        st.markdown("""
        <div class="reglement-container" style="background: #FFFFFF !important; height: auto !important;">
            <div class="article-title" style="color: #D4AF37 !important;">Article 2 - Pronostics Hebdomadaires</div>
            <div class="article-content" style="color: #000000 !important;">
                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">2.1</span> <strong style="color: #000000 !important;">Selection des matchs</strong></p>
                <p style="color: #000000 !important;">Chaque semaine, <span class="highlight-gold" style="color: #D4AF37 !important;">des matchs sont proposes aux participants en fonction de leur cote</span>.
                Les matchs sont selectionnes prioritairement en Ligue 1, puis dans les autres grands championnats
                europeens (Premier League, Liga, Serie A, Bundesliga).</p>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">2.2</span> <strong style="color: #000000 !important;">Format du pronostic</strong></p>
                <p style="color: #000000 !important;">Pour chaque match, le participant doit indiquer :</p>
                <ul style="color: #000000 !important;">
                    <li style="color: #000000 !important;">Le <span class="highlight-gold" style="color: #D4AF37 !important;">score exact</span> qu'il predit (ex: 2-1)</li>
                    <li style="color: #000000 !important;">La <span class="highlight-gold" style="color: #D4AF37 !important;">mise en points</span> qu'il souhaite engager</li>
                </ul>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">2.3</span> <strong style="color: #000000 !important;">Budget hebdomadaire</strong></p>
                <div class="highlight-box" style="background: rgba(212, 175, 55, 0.15) !important; height: auto !important;">
                    <p style="color: #000000 !important;">Chaque semaine, le participant dispose d'un budget de <span class="highlight-gold" style="color: #D4AF37 !important;">100 POINTS</span>
                    a repartir obligatoirement sur les matchs.</p>
                    <ul style="color: #000000 !important;">
                        <li style="color: #000000 !important;">Mise minimum par match : <span class="highlight-gold" style="color: #D4AF37 !important;">10 points</span></li>
                        <li style="color: #000000 !important;">Mise maximum par match : <span class="highlight-gold" style="color: #D4AF37 !important;">60 points</span></li>
                        <li style="color: #000000 !important;">Total des mises : exactement 100 points</li>
                    </ul>
                </div>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">2.4</span> <strong style="color: #000000 !important;">Deadline</strong></p>
                <p style="color: #000000 !important;">Les pronostics doivent etre valides <span class="highlight-gold" style="color: #D4AF37 !important;">1 heure avant</span>
                le coup d'envoi du premier match de la semaine. Passe ce delai, aucune modification n'est possible.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 3 : SYSTEME DE POINTS
    # =====================================================
    with st.expander("ARTICLE 3 : SYSTEME DE POINTS", expanded=True):
        st.markdown("""
        <div class="reglement-container" style="background: #FFFFFF !important; height: auto !important;">
            <div class="article-title" style="color: #D4AF37 !important;">Article 3 - Systeme de Points</div>
            <div class="article-content" style="color: #000000 !important;">
                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">3.1</span> <strong style="color: #000000 !important;">Resultat 1N2</strong></p>
                <p style="color: #000000 !important;">Si le participant trouve le bon resultat (Victoire domicile / Nul / Victoire exterieur) :</p>
                <div class="highlight-box" style="background: rgba(212, 175, 55, 0.15) !important; height: auto !important;">
                    <p style="color: #000000 !important;"><span class="highlight-gold" style="color: #D4AF37 !important;">Points gagnes = Mise x Cote du resultat</span></p>
                    <p style="color: #555555 !important; font-size: 0.9em;">Exemple : Mise 30 pts sur PSG gagnant, cote 1.50 → 30 x 1.50 = 45 pts</p>
                </div>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">3.2</span> <strong style="color: #000000 !important;">Score Exact</strong></p>
                <p style="color: #000000 !important;">Si le participant trouve le <span class="highlight-gold" style="color: #D4AF37 !important;">score exact</span> du match :</p>
                <div class="highlight-box" style="background: rgba(212, 175, 55, 0.15) !important; height: auto !important;">
                    <p style="color: #000000 !important;"><span class="highlight-gold" style="color: #D4AF37 !important;">BONUS : +10 POINTS par score exact</span></p>
                    <p style="color: #555555 !important; font-size: 0.9em;">Exemple : Mise 20, cote 2.0 avec score exact → (20 x 2.0) + 10 = 50 pts</p>
                </div>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">3.3</span> <strong style="color: #000000 !important;">Mauvais pronostic</strong></p>
                <p style="color: #000000 !important;">Si le resultat 1N2 est incorrect :</p>
                <div class="highlight-box" style="border-color: #ff6b6b !important; background: rgba(255, 107, 107, 0.1) !important; height: auto !important;">
                    <p style="color: #ff6b6b !important;"><strong style="color: #ff6b6b !important;">0 point gagne</strong> (la mise est perdue)</p>
                </div>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">3.4</span> <strong style="color: #000000 !important;">Bonus Grand Chelem</strong></p>
                <p style="color: #000000 !important;">Si un participant trouve <span class="highlight-gold" style="color: #D4AF37 !important;">tous les resultats 1N2 corrects</span>
                sur une meme semaine :</p>
                <div class="highlight-box" style="border-color: #00FF00 !important; background: rgba(0, 255, 0, 0.1) !important; height: auto !important;">
                    <p style="color: #00FF00 !important;"><strong style="color: #00FF00 !important;">BONUS GRAND CHELEM : +40 POINTS</strong></p>
                    <p style="color: #555555 !important; font-size: 0.9em;">Cumules pour la journee SUIVANTE</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 4 : JOKERS
    # =====================================================
    with st.expander("ARTICLE 4 : LES JOKERS", expanded=True):
        st.markdown("""
        <div class="reglement-container" style="background: #FFFFFF !important; height: auto !important;">
            <div class="article-title" style="color: #D4AF37 !important;">Article 4 - Les Jokers</div>
            <div class="article-content" style="color: #000000 !important;">
                <p style="color: #000000 !important;">Chaque participant dispose de <span class="highlight-gold" style="color: #D4AF37 !important;">3 jokers Points Doubles</span>
                et <span class="highlight-gold" style="color: #D4AF37 !important;">2 jokers Points Voles</span> par saison, a utiliser strategiquement.</p>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">4.1</span> <strong style="color: #000000 !important;">Joker POINTS DOUBLES (x3 par saison)</strong></p>
                <div class="highlight-box" style="border-color: #9b59b6 !important; background: rgba(155, 89, 182, 0.1) !important; height: auto !important;">
                    <p style="color: #9b59b6 !important; font-size: 1.1em;"><strong style="color: #9b59b6 !important;">x2 sur tous les gains de la semaine</strong></p>
                    <ul style="color: #000000 !important;">
                        <li style="color: #000000 !important;">Active avant la deadline des pronostics</li>
                        <li style="color: #000000 !important;">Multiplie par 2 TOUS les points gagnes sur les matchs</li>
                        <li style="color: #000000 !important;">Le bonus Grand Chelem est egalement double</li>
                    </ul>
                </div>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">4.2</span> <strong style="color: #000000 !important;">Joker POINTS VOLES (x2 par saison)</strong></p>
                <div class="highlight-box" style="border-color: #e74c3c !important; background: rgba(231, 76, 60, 0.1) !important; height: auto !important;">
                    <p style="color: #e74c3c !important; font-size: 1.1em;"><strong style="color: #e74c3c !important;">Copie les pronostics d'un adversaire</strong></p>
                    <ul style="color: #000000 !important;">
                        <li style="color: #000000 !important;">Choisissez un adversaire AVANT la deadline</li>
                        <li style="color: #000000 !important;">Vos pronostics sont remplaces par les siens</li>
                        <li style="color: #000000 !important;">Vous gagnez les memes points que lui cette semaine</li>
                        <li style="color: #000000 !important;">L'adversaire n'est pas prevenu</li>
                    </ul>
                </div>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">4.3</span> <strong style="color: #000000 !important;">Oubli de pronostics</strong></p>
                <div class="highlight-box" style="border-color: #ff9800 !important; background: rgba(255, 152, 0, 0.1) !important; height: auto !important;">
                    <p style="color: #ff9800 !important;"><strong style="color: #ff9800 !important;">Si un joueur oublie de faire ses pronostics :</strong></p>
                    <p style="color: #000000 !important;">1 joker Points Voles sera automatiquement utilise sur le <span class="highlight-gold" style="color: #D4AF37 !important;">dernier du classement</span>.</p>
                </div>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">4.4</span> <strong style="color: #000000 !important;">Regles d'utilisation</strong></p>
                <ul style="color: #000000 !important;">
                    <li style="color: #000000 !important;">Un seul joker peut etre active par semaine</li>
                    <li style="color: #000000 !important;">Le joker doit etre active AVANT la deadline</li>
                    <li style="color: #000000 !important;">Une fois active, le joker ne peut pas etre annule</li>
                    <li style="color: #000000 !important;">Les jokers non utilises sont perdus en fin de saison</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 5 : CLASSEMENT ET RECOMPENSES
    # =====================================================
    with st.expander("ARTICLE 5 : CLASSEMENT ET RECOMPENSES", expanded=True):
        st.markdown("""
        <div class="reglement-container" style="background: #FFFFFF !important; height: auto !important;">
            <div class="article-title" style="color: #D4AF37 !important;">Article 5 - Classement et Recompenses</div>
            <div class="article-content" style="color: #000000 !important;">
                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">5.1</span> <strong style="color: #000000 !important;">Classement general</strong></p>
                <p style="color: #000000 !important;">Le classement est etabli selon le <span class="highlight-gold" style="color: #D4AF37 !important;">cumul des points</span>
                gagnes depuis le debut de la saison. En cas d'egalite, les criteres de departage sont :</p>
                <ol style="color: #000000 !important;">
                    <li style="color: #000000 !important;">Nombre de scores exacts trouves</li>
                    <li style="color: #000000 !important;">Nombre de Grand Chelems realises</li>
                    <li style="color: #000000 !important;">Confrontation directe (semaines en commun)</li>
                </ol>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">5.2</span> <strong style="color: #000000 !important;">Classement hebdomadaire</strong></p>
                <p style="color: #000000 !important;">Un classement de la semaine est publie apres chaque journee, permettant de suivre
                les performances individuelles match par match.</p>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">5.3</span> <strong style="color: #000000 !important;">Fin de saison</strong></p>
                <p style="color: #000000 !important;">La saison se termine a l'issue de la derniere journee de Ligue 1.
                Le classement final est alors fige.</p>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">5.4</span> <strong style="color: #000000 !important;">Podium</strong></p>
                <div class="highlight-box" style="background: rgba(212, 175, 55, 0.15) !important; height: auto !important;">
                    <div style="display: flex; justify-content: center; gap: 30px; text-align: center;">
                        <div>
                            <div style="font-size: 1.8em;">🥇</div>
                            <div style="color: #FFD700 !important; font-weight: bold;">1er</div>
                            <div style="color: #555555 !important; font-size: 0.9em;">Champion</div>
                        </div>
                        <div>
                            <div style="font-size: 1.8em;">🥈</div>
                            <div style="color: #C0C0C0 !important; font-weight: bold;">2eme</div>
                            <div style="color: #555555 !important; font-size: 0.9em;">Vice-Champion</div>
                        </div>
                        <div>
                            <div style="font-size: 1.8em;">🥉</div>
                            <div style="color: #CD7F32 !important; font-weight: bold;">3eme</div>
                            <div style="color: #555555 !important; font-size: 0.9em;">Bronze</div>
                        </div>
                    </div>
                </div>

                <p style="color: #000000 !important;"><span class="emoji-big" style="color: #D4AF37 !important;">5.5</span> <strong style="color: #000000 !important;">Fair-play</strong></p>
                <p style="color: #000000 !important;">Tout comportement antisportif (multi-comptes, collusion, triche) entraine
                la <span style="color: #ff6b6b !important;">disqualification immediate</span> et definitive du participant.</p>
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
