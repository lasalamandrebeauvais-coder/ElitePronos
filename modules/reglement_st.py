"""
Module Reglement pour Elite Pronos
Affichage des 5 articles du reglement officiel
Format: Articles en couleur, points soulignes, sans blocs
"""
import streamlit as st
import os

# Chemin vers la mascotte
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')


def afficher_reglement():
    """Affiche le reglement officiel d'Elite Pronos"""

    # Header avec mascotte en haut a droite
    col_title, col_mascot = st.columns([4, 1])
    with col_title:
        st.markdown("## Reglement Officiel")
    with col_mascot:
        mascot_path = os.path.join(ASSETS_PATH, "kingo reglement.png")
        if os.path.exists(mascot_path):
            st.image(mascot_path, width=80)

    st.markdown("---")

    # Style CSS - Articles en couleur, points soulignes, sans blocs
    st.markdown("""
    <style>
        .article-titre {
            color: #D4AF37;
            font-size: 1.4em;
            font-weight: bold;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        .point-titre {
            color: #FFD700;
            font-weight: bold;
            text-decoration: underline;
            font-size: 1.05em;
            margin-top: 15px;
            margin-bottom: 5px;
        }
        .point-texte {
            color: #FFFFFF;
            margin-left: 10px;
            margin-bottom: 10px;
            line-height: 1.6;
        }
        .valeur-or {
            color: #FFD700;
            font-weight: bold;
        }
        .valeur-vert {
            color: #00FF00;
            font-weight: bold;
        }
        .valeur-rouge {
            color: #FF6B6B;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 1 : PARTICIPATION
    # =====================================================
    st.markdown('<div class="article-titre">Article 1 - Participation et Inscription</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">1.1 Eligibilite</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Elite Pronos est une ligue privee de pronostics football reservee aux membres invites. Toute inscription est soumise a validation par un administrateur.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">1.2 Periode d\'inscription</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Les inscriptions sont ouvertes <span class="valeur-or">30 jours avant la Journee 1</span> de chaque saison. Aucune nouvelle inscription apres le coup d\'envoi du premier match.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">1.3 Compte utilisateur</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Chaque participant doit creer un compte unique avec : un pseudo (min 3 caracteres), une adresse email valide, un code PIN personnel (min 4 caracteres).</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">1.4 Engagement</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">En s\'inscrivant, le participant s\'engage a respecter le present reglement et a participer de bonne foi.</div>', unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 2 : PRONOSTICS HEBDOMADAIRES
    # =====================================================
    st.markdown('<div class="article-titre">Article 2 - Pronostics Hebdomadaires</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">2.1 Selection des matchs</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Chaque semaine, <span class="valeur-or">4 matchs sont proposes</span>. Priorite Ligue 1, puis autres championnats europeens.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">2.2 Format du pronostic</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Pour chaque match : le <span class="valeur-or">score exact</span> predit (ex: 2-1) et la <span class="valeur-or">mise en points</span> engagee.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">2.3 Budget hebdomadaire</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Budget : <span class="valeur-or">100 POINTS</span> a repartir sur 4 matchs. Mise min : <span class="valeur-or">10 pts</span> / Mise max : <span class="valeur-or">60 pts</span> par match.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">2.4 Deadline</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Pronostics a valider <span class="valeur-or">1 heure avant</span> le coup d\'envoi du premier match. Aucune modification possible apres.</div>', unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 3 : SYSTEME DE POINTS
    # =====================================================
    st.markdown('<div class="article-titre">Article 3 - Systeme de Points</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">3.1 Resultat 1N2 correct</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte"><span class="valeur-or">Points = Mise x Cote</span> (Ex: 30 pts x cote 1.50 = 45 pts)</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">3.2 Score Exact</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Bonus <span class="valeur-vert">+10 POINTS</span> si score exact trouve</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">3.3 Mauvais pronostic</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte"><span class="valeur-rouge">0 point</span> si le resultat 1N2 est incorrect</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">3.4 Grand Chelem</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Bonus <span class="valeur-vert">+40 POINTS</span> si 4/4 resultats corrects sur une semaine</div>', unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 4 : JOKERS
    # =====================================================
    st.markdown('<div class="article-titre">Article 4 - Les Jokers</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-texte">Stock par saison : <span class="valeur-or">3 jokers Points Doubles</span> + <span class="valeur-or">2 jokers Points Voles</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">4.1 Joker POINTS DOUBLES</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Multiplie par 2 TOUS les points gagnes de la semaine (bonus Grand Chelem inclus).</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">4.2 Joker POINTS VOLES</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Copie les pronostics d\'un adversaire choisi. Vous gagnez les memes points que lui.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">4.3 Oubli de pronostics</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">1 joker Points Voles <span class="valeur-or">automatiquement utilise</span> sur le dernier du classement.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">4.4 Regles</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Un seul joker par semaine, a activer AVANT la deadline, non annulable, perdu en fin de saison.</div>', unsafe_allow_html=True)

    # =====================================================
    # ARTICLE 5 : CLASSEMENT
    # =====================================================
    st.markdown('<div class="article-titre">Article 5 - Classement et Recompenses</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">5.1 Classement general</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Base sur le <span class="valeur-or">cumul des points</span>. Departage : scores exacts, Grand Chelems, confrontation directe.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">5.2 Classement hebdomadaire</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Publie apres chaque journee pour suivre les performances.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">5.3 Fin de saison</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Termine a l\'issue de la derniere journee de Ligue 1. Classement final fige.</div>', unsafe_allow_html=True)

    st.markdown('<div class="point-titre">5.4 Podium</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="point-texte" style="text-align: center;">
        <span style="color: #FFD700; font-size: 1.2em;">🥇 1er - Champion</span> &nbsp;&nbsp;
        <span style="color: #C0C0C0; font-size: 1.2em;">🥈 2eme</span> &nbsp;&nbsp;
        <span style="color: #CD7F32; font-size: 1.2em;">🥉 3eme</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="point-titre">5.5 Fair-play</div>', unsafe_allow_html=True)
    st.markdown('<div class="point-texte">Triche = <span class="valeur-rouge">disqualification immediate</span> et definitive.</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.caption("Reglement officiel Elite Pronos - Saison 2025-2026")
