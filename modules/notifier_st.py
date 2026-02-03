"""
Module Notifier pour Elite Pronos
Gestion des emails automatises via SMTP
Design Elite: Bleu Nuit & Dore
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Import des fonctions de database_manager
from modules.database_manager import (
    get_setting,
    is_mode_officiel,
    get_utilisateurs_emails,
    get_date_j1,
    get_saison_actuelle,
    get_saison_label
)


# ============================================
# CONFIGURATION SMTP
# ============================================

def get_streamlit_secret(key, default=''):
    """Recupere un secret depuis Streamlit Cloud ou .env"""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.environ.get(key, default)


def get_smtp_config():
    """Recupere la configuration SMTP depuis les settings, env ou Streamlit secrets"""
    return {
        'host': get_setting('smtp_host') or get_streamlit_secret('SMTP_HOST', 'smtp.gmail.com'),
        'port': int(get_setting('smtp_port') or get_streamlit_secret('SMTP_PORT', '587')),
        'user': get_setting('smtp_user') or get_streamlit_secret('SMTP_USER', ''),
        'password': get_setting('smtp_password') or get_streamlit_secret('SMTP_PASSWORD', '')
    }


def send_email(destinataire, sujet, html_content):
    """
    Envoie un email via SMTP
    Retourne (success, message)
    """
    # Verifier le mode officiel
    if not is_mode_officiel():
        return True, f"[MODE TEST] Email simule vers {destinataire}: {sujet}"

    config = get_smtp_config()

    if not config['host'] or not config['user']:
        return False, "Configuration SMTP incomplete"

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = sujet
        msg['From'] = f"Elite Pronos <{config['user']}>"
        msg['To'] = destinataire

        # Contenu HTML
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # Connexion et envoi
        with smtplib.SMTP(config['host'], config['port']) as server:
            server.starttls()
            server.login(config['user'], config['password'])
            server.send_message(msg)

        return True, f"Email envoye a {destinataire}"

    except Exception as e:
        return False, f"Erreur envoi email: {str(e)}"


# ============================================
# BIBLIOTHEQUE DE PHRASES IRONIQUES
# ============================================

import random

PHRASES_IRONIQUES = {
    'premier': [
        "Le roi de la semaine ! Enfin, jusqu'a ce qu'il se plante lamentablement...",
        "Bravo champion ! Les debutants ont parfois de la chance...",
        "Impressionnant ! Tu as du regarder les matchs au lieu de deviner ?",
        "Attention, on a un expert parmi nous... ou juste un coup de bol ?",
        "Tel un aigle, tu domines... pour l'instant.",
        "La place est chaude, profites-en avant qu'elle refroidisse !",
    ],
    'dernier': [
        "Au moins, tu es constant dans la mediocrite !",
        "Tu devrais peut-etre essayer les echecs a la place ?",
        "Ton joker aurait ete plus utile que tes pronostics...",
        "Meme un singe avec des flechettes aurait fait mieux !",
        "Le fond du classement te dit merci pour ta fidelite.",
        "Tu collectionnes les defaites comme d'autres les timbres.",
    ],
    'progresse': [
        "Tiens, tu as enfin trouve comment marche le foot ?",
        "Belle remontee ! Tu lisais des tutos sur YouTube ?",
        "Miracle ! Il y a de l'espoir pour toi finalement.",
        "Tu as change de lunettes ou quoi ?",
        "Enfin reveille ! On commencait a s'inquieter.",
    ],
    'regresse': [
        "La chute est rude ! Tu etais en vacances mentales ?",
        "De heros a zero en une semaine, chapeau !",
        "Retour sur Terre brutal... ca fait mal ?",
        "Tu redescends aussi vite que tu es monte.",
        "L'ascenseur etait en panne ? Tu as pris l'escalier... vers le bas.",
    ],
    'stable': [
        "Stable comme un diesel... qui ne demarre pas.",
        "Ni bon ni mauvais, juste... la.",
        "La regularite dans la mediocrite, c'est presque un talent.",
        "Tu fais du surplace, mais au moins tu ne recules pas.",
        "Comme un meuble : present mais pas remarque.",
    ],
    'grand_chelem': [
        "4/4 ! Tu as vendu ton ame au diable ou tu savais vraiment ?",
        "GRAND CHELEM ! Meme Nostradamus est jaloux !",
        "Perfection ! C'est louche... on verifie les cameras.",
        "4 sur 4 ! Tu as des informateurs dans les vestiaires ?",
        "Le sans-faute ! Profite, ca n'arrivera plus avant longtemps.",
        "Grand Chelem ! Ta boule de cristal fonctionne encore ?",
        "LEGENDAIRE ! On devrait t'appeler Madame Irma.",
    ],
    'score_exact': [
        "Score exact ! Tu as un don ou c'est de la triche ?",
        "Dans le mille ! Meme le bookmaker est impressionne.",
        "Score parfait ! Tu as soudoye l'arbitre ?",
        "Precision chirurgicale ! On t'engage comme consultant.",
        "Score exact ! La chance sourit aux audacieux... ou aux tricheurs.",
        "Bullseye ! Tu devrais jouer aux flechettes aussi.",
    ],
    'joker_vole_reussi': [
        "Ton vol a paye ! Le crime parfait existe donc.",
        "Braquage reussi ! Ta victime doit s'en mordre les doigts.",
        "Points voles avec succes ! Tel un pickpocket de genie.",
        "Le casse du siecle ! Ocean's Eleven peut aller se rhabiller.",
        "Vol qualifie et assume ! Pas de remords, que des points.",
        "Tu as vole ses pronos ET sa dignite. Bien joue !",
    ],
    'joker_vole_rate': [
        "Tu as vole les pronos d'un nul... Bien joue, genie !",
        "Bravo, tu as copie sur le plus mauvais de la classe !",
        "Vol rate ! Tu aurais du choisir une meilleure cible...",
        "Felicitations, tu as herite des pires pronos. Karma ?",
        "Comme voler une voiture en panne... Quelle strategie !",
        "Tu as vole a l'aveugle et tu es tombe sur un borgne.",
        "Le voleur vole ! La cible etait encore plus nulle que toi.",
    ],
    'lanterne_rouge': [
        "Lanterne rouge ! Tu eclaires le chemin... par le bas.",
        "Dernier ! Mais bon, quelqu'un doit bien fermer la marche.",
        "La cave t'attend, tu y es deja installe confortablement.",
        "Tu touches le fond ? Non, tu creuses encore !",
        "Bonnet d'ane ! Au moins tu es premier... en partant de la fin.",
        "Le sous-sol du classement te connait bien maintenant.",
        "Dernier ! On dit que la vue est belle d'en bas... non en fait.",
        "Tu as trouve ta place : tout en bas, bien au chaud.",
    ],
    'oubli_prono': [
        "Oubli de pronos ! Le systeme t'a attribue ceux du dernier. Malin !",
        "Pas de pronos ? Felicitations, tu herites des pires predictions !",
        "Tu as oublie de jouer... Le Bot a joue pour toi. Spoiler : c'est pas fou.",
        "Absence injustifiee ! Tu as les pronos du bonnet d'ane maintenant.",
        "Oups ! Oubli de deadline = cadeau empoisonne automatique.",
        "Le reveil n'a pas sonne ? Pas grave, le dernier du classement t'a prete ses pronos.",
        "Memoire de poisson rouge ! Le systeme t'a mis d'office les pires pronos.",
    ],
    'holdup': [
        "HOLD-UP ! Tu as braque la banque des pronos !",
        "Le casse du siecle ! Ta victime ne s'en remettra pas.",
        "Braquage en regle ! Ocean's Eleven peut aller se rhabiller.",
        "Hold-up reussi ! Le crime parfait, ca existe.",
        "Tu as cambriole les pronos comme un pro. Respect... ou pas.",
        "HOLD-UP MAGISTRAL ! La cible n'a rien vu venir.",
    ],
    'joker_double_gagnant': [
        "Joker x2 au bon moment ! Tu as double la mise et le butin !",
        "Points doubles actives et ca paye ! Stratege ou chanceux ?",
        "Le x2 etait parfait ! Tu as fait sauter la banque.",
        "Joker double bien place ! Les autres peuvent pleurer.",
        "Multiplication des points ! Ta semaine est en or.",
    ],
    'joker_double_perdant': [
        "Joker x2 sur une semaine pourrie... Double peine !",
        "Tu as double... tes echecs. Bravo champion !",
        "Le x2 sur une catastrophe, c'etait vraiment l'idee du siecle ?",
        "Points doubles sur zero points = toujours zero. Les maths, c'est cruel.",
        "Joker gaspille ! Tu aurais du le garder pour une bonne semaine.",
    ]
}


def get_phrase_ironique(categorie):
    """Retourne une phrase ironique aleatoire pour une categorie donnee"""
    if categorie in PHRASES_IRONIQUES:
        return random.choice(PHRASES_IRONIQUES[categorie])
    return random.choice(PHRASES_IRONIQUES['stable'])


def generer_commentaire_joueur(joueur_data):
    """
    Genere un commentaire ironique personnalise selon les performances du joueur.
    joueur_data: dict avec rang, evolution, grand_chelem, scores_exacts, joker_vol,
                 oubli_prono, joker_double_utilise, joker_double_reussi, etc.
    """
    # Priorite 0: Oubli de pronostic (le plus honteux!)
    if joueur_data.get('oubli_prono'):
        return get_phrase_ironique('oubli_prono')

    # Priorite 1: Grand Chelem (4/4)
    if joueur_data.get('grand_chelem'):
        return get_phrase_ironique('grand_chelem')

    # Priorite 2: Joker Double (x2)
    if joueur_data.get('joker_double_utilise'):
        if joueur_data.get('joker_double_reussi'):
            return get_phrase_ironique('joker_double_gagnant')
        else:
            return get_phrase_ironique('joker_double_perdant')

    # Priorite 3: Joker Vole (Hold-up!)
    if joueur_data.get('joker_vol_utilise'):
        if joueur_data.get('joker_vol_reussi'):
            # Alterner entre holdup et joker_vole_reussi pour varier
            return get_phrase_ironique(random.choice(['holdup', 'joker_vole_reussi']))
        else:
            return get_phrase_ironique('joker_vole_rate')

    # Priorite 4: Lanterne rouge (dernier du classement general)
    if joueur_data.get('lanterne_rouge'):
        return get_phrase_ironique('lanterne_rouge')

    # Priorite 5: Score exact
    if joueur_data.get('scores_exacts', 0) > 0:
        return get_phrase_ironique('score_exact')

    # Priorite 5: Position dans le classement de la semaine
    rang = joueur_data.get('rang', 0)
    total_joueurs = joueur_data.get('total_joueurs', 10)

    if rang == 1:
        return get_phrase_ironique('premier')
    elif rang == total_joueurs:
        return get_phrase_ironique('dernier')

    # Priorite 6: Evolution
    evolution = joueur_data.get('evolution', 0)
    if evolution > 2:
        return get_phrase_ironique('progresse')
    elif evolution < -2:
        return get_phrase_ironique('regresse')

    return get_phrase_ironique('stable')


# ============================================
# TEMPLATES HTML ELITE
# ============================================

def get_base_template(content, titre="Elite Pronos"):
    """Template HTML de base avec style Elite"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #0a0a1a;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: linear-gradient(135deg, #0d1b2a 0%, #1a1a2e 100%);
                border: 2px solid #FFD700;
                border-radius: 15px;
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                color: #0a0a1a;
                margin: 0;
                font-size: 28px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            .header .subtitle {{
                color: #1a1a2e;
                font-size: 14px;
                margin-top: 5px;
            }}
            .content {{
                padding: 30px;
                color: #ffffff;
            }}
            .content h2 {{
                color: #FFD700;
                margin-top: 0;
            }}
            .content p {{
                line-height: 1.6;
                color: #cccccc;
            }}
            .button {{
                display: inline-block;
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                color: #0a0a1a !important;
                padding: 15px 40px;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                text-transform: uppercase;
                margin: 20px 0;
            }}
            .highlight-box {{
                background: rgba(255, 215, 0, 0.1);
                border: 1px solid #FFD700;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }}
            .highlight-box .big-text {{
                font-size: 36px;
                color: #FFD700;
                font-weight: bold;
            }}
            .footer {{
                background: #0a0a1a;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
            .footer a {{
                color: #FFD700;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{titre}</h1>
                <div class="subtitle">La ligue des experts du football</div>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>Cet email a ete envoye automatiquement par Elite Pronos.</p>
                <p>Saison {get_saison_label(get_saison_actuelle())}</p>
            </div>
        </div>
    </body>
    </html>
    '''


# ============================================
# CAMPAGNES EMAIL
# ============================================

def email_lancement_saison(utilisateur):
    """Email d'ouverture des inscriptions (J1-30)"""
    prenom = utilisateur.get('prenom') or utilisateur.get('pseudo')
    date_j1 = get_date_j1()
    date_j1_str = date_j1.strftime('%d/%m/%Y a %Hh%M') if date_j1 else 'bientot'

    content = f'''
    <h2>La nouvelle saison arrive !</h2>
    <p>Bonjour <strong>{prenom}</strong>,</p>
    <p>Les inscriptions pour la saison <strong>{get_saison_label(get_saison_actuelle())}</strong>
    sont officiellement ouvertes !</p>

    <div class="highlight-box">
        <div class="big-text">J-30</div>
        <p style="margin: 10px 0 0 0; color: #FFD700;">Coup d'envoi le {date_j1_str}</p>
    </div>

    <p>Preparez-vous a affronter les meilleurs pronostiqueurs et a prouver
    que vous etes un veritable expert du football !</p>

    <p style="text-align: center;">
        <a href="#" class="button">Acceder a Elite Pronos</a>
    </p>

    <p><strong>Rappel des regles :</strong></p>
    <ul style="color: #cccccc;">
        <li>4 matchs a pronostiquer chaque semaine</li>
        <li>100 points de budget a repartir</li>
        <li>2 jokers a utiliser strategiquement</li>
        <li>Bonus Grand Chelem : +40 pts si 4/4 corrects</li>
    </ul>

    <p>Que la meilleure strategie gagne !</p>
    '''

    return get_base_template(content, "Nouvelle Saison")


def email_bienvenue(utilisateur):
    """
    Email de bienvenue complet pour un nouvel inscrit
    Inclut: tarifs, paiement, gains, prix fixes, reglement
    """
    prenom = utilisateur.get('prenom') or utilisateur.get('pseudo')
    pseudo = utilisateur.get('pseudo')

    content = f'''
    <h2>Felicitations !</h2>
    <p>Bonjour <strong>{prenom}</strong>,</p>
    <p>Votre demande d'inscription a bien ete recue !</p>
    <p>Pour rejoindre officiellement l'aventure <strong style="color: #FFD700;">Elite Pronos</strong>,
    voici les modalites finales :</p>

    <!-- PARTICIPATION FINANCIERE -->
    <div style="background: rgba(255, 215, 0, 0.05); border: 1px solid #FFD700; border-radius: 10px; padding: 20px; margin: 25px 0;">
        <h3 style="color: #FFD700; margin-top: 0;">Participation financiere</h3>
        <ul style="color: #ffffff; font-size: 1.1em; list-style: none; padding: 0;">
            <li style="margin: 10px 0;"><strong style="color: #FFD700;">Mise de jeu :</strong> 50 euros <span style="color: #AAAAAA;">(integralement reverses dans la cagnotte)</span></li>
            <li style="margin: 10px 0;"><strong style="color: #FFD700;">Frais de maintenance :</strong> 5 euros <span style="color: #AAAAAA;">(frais techniques)</span></li>
        </ul>
        <p style="color: #00FF00; margin-top: 15px; padding-top: 15px; border-top: 1px solid #333;">
            Votre compte sera active par <strong>Baggio</strong> des reception de votre reglement par cheque ou virement.
        </p>
    </div>

    <!-- REPARTITION DES RECOMPENSES -->
    <div style="background: rgba(0, 255, 0, 0.05); border: 1px solid #00FF00; border-radius: 10px; padding: 20px; margin: 25px 0;">
        <h3 style="color: #00FF00; margin-top: 0;">Repartition des Recompenses</h3>
        <p style="color: #AAAAAA; font-style: italic;">(Arrondies a la dizaine)</p>

        <p style="color: #FFD700; margin-top: 15px;"><strong>Prix Fixes :</strong></p>
        <ul style="color: #ffffff; margin-left: 20px;">
            <li style="margin: 8px 0;"><span style="color: #FFD700; font-weight: bold;">Meilleur score :</span> 50 euros</li>
            <li style="margin: 8px 0;"><span style="color: #FFD700; font-weight: bold;">Plus de paris reussis :</span> 25 euros</li>
        </ul>

        <p style="color: #FFD700; margin-top: 20px;"><strong>Cagnotte de fin de saison :</strong></p>
        <ul style="color: #ffffff; margin-left: 20px;">
            <li style="margin: 8px 0;"><strong>Jusqu'a 20 joueurs :</strong> Top 3 recompenses</li>
            <li style="margin: 8px 0;"><strong>De 21 a 40 joueurs :</strong> Top 5 recompenses</li>
            <li style="margin: 8px 0;"><strong>41 joueurs et plus :</strong> Top 7 recompenses</li>
        </ul>

        <p style="color: #AAAAAA; font-size: 0.95em; margin-top: 20px; padding-top: 15px; border-top: 1px solid #333;">
            Le versement de vos gains s'effectuera <strong style="color: #FFD700;">15 jours</strong> apres le coup de sifflet final du championnat.
        </p>
    </div>

    <!-- REGLEMENT -->
    <div style="background: #0a0a1a; border: 2px solid #D4AF37; border-radius: 10px; padding: 20px; margin: 25px 0;">
        <h3 style="color: #D4AF37; margin-top: 0; text-align: center;">REGLEMENT COMPLET DU CLUB</h3>

        <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 1 - Participation et Inscription</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                Elite Pronos est une ligue privee reservee aux membres invites.
                Inscription soumise a validation admin. Compte unique obligatoire (pseudo min. 3 car., email valide, PIN min. 4 car.).
                Inscriptions ouvertes 30 jours avant la J1. Aucune inscription apres le coup d'envoi du 1er match.
            </p>
        </div>

        <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 2 - Pronostics Hebdomadaires</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                4 matchs par semaine. Budget de 100 points a repartir (mise min. 10 pts, max. 60 pts par match).
                Deadline : 1h avant le premier match. Defaut de pronostic = pronostics du dernier du classement attribues automatiquement.
            </p>
        </div>

        <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 3 - Systeme de Points</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                <strong>Formule :</strong> Points = Mise x Cote (si 1N2 correct).<br>
                <strong>Bonus score exact :</strong> +10 points fixes.<br>
                <strong>Grand Chelem (4/4 corrects) :</strong> +40 points appliques la semaine suivante.
            </p>
        </div>

        <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 4 - Les Jokers</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                2 jokers par saison :<br>
                <strong>Points Doubles :</strong> x2 sur tous les gains de la semaine.<br>
                <strong>Points Voles :</strong> Copie les pronostics d'un adversaire choisi.<br>
                Activation avant la deadline, non annulable. Jokers non utilises perdus en fin de saison.
            </p>
        </div>

        <div>
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 5 - Classement et Recompenses</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                Classement par cumul des points. Departage : scores exacts, Grand Chelems, confrontation directe.
                <strong style="color: #ff6b6b;">Tout comportement antisportif (multi-comptes, collusion, triche) = disqualification immediate et definitive.</strong>
            </p>
        </div>
    </div>

    <p style="color: #cccccc; text-align: center;">
        Preparez vos strategies, le <strong style="color: #9b59b6;">Bot Elite</strong> vous attend deja sur le terrain !
    </p>

    <p style="text-align: center;">
        <a href="#" class="button">Acceder a Elite Pronos</a>
    </p>

    <p style="color: #FFD700; font-weight: bold; text-align: right; margin-top: 30px;">
        L'Admin Elite Pronos
    </p>
    '''

    return get_base_template(content, "Bienvenue dans le Club")


def email_rappel_j7(utilisateur):
    """Email de rappel J-7 avant debut saison"""
    prenom = utilisateur.get('prenom') or utilisateur.get('pseudo')
    date_j1 = get_date_j1()
    date_j1_str = date_j1.strftime('%d/%m/%Y') if date_j1 else ''

    content = f'''
    <h2>Plus que 7 jours !</h2>
    <p>Bonjour <strong>{prenom}</strong>,</p>
    <p>La Journee 1 de la saison <strong>{get_saison_label(get_saison_actuelle())}</strong>
    debute dans une semaine !</p>

    <div class="highlight-box">
        <div class="big-text">J-7</div>
        <p style="margin: 10px 0 0 0; color: #FFD700;">{date_j1_str}</p>
    </div>

    <p style="color: #ff6b6b;"><strong>Attention :</strong> Vous n'avez pas encore valide
    vos pronostics pour la J1 !</p>

    <p>N'oubliez pas : si vous ne saisissez pas vos pronostics avant le coup d'envoi,
    le systeme vous attribuera automatiquement les pronostics du dernier du classement.</p>

    <p style="text-align: center;">
        <a href="#" class="button">Saisir mes pronostics</a>
    </p>
    '''

    return get_base_template(content, "Rappel J-7")


def email_rappel_j1(utilisateur):
    """Email de rappel J-1 avant debut saison"""
    prenom = utilisateur.get('prenom') or utilisateur.get('pseudo')

    content = f'''
    <h2>Dernier jour !</h2>
    <p>Bonjour <strong>{prenom}</strong>,</p>

    <div class="highlight-box" style="border-color: #ff6b6b; background: rgba(255, 107, 107, 0.1);">
        <div class="big-text" style="color: #ff6b6b;">URGENT</div>
        <p style="margin: 10px 0 0 0; color: #ff6b6b;">
            La J1 commence DEMAIN et vous n'avez toujours pas saisi vos pronostics !
        </p>
    </div>

    <p>C'est votre derniere chance d'entrer vos predictions avant que
    le systeme ne vous attribue les pronostics du dernier joueur.</p>

    <p style="text-align: center;">
        <a href="#" class="button" style="background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);">
            Saisir mes pronostics MAINTENANT
        </a>
    </p>

    <p style="color: #AAAAAA; font-size: 12px; text-align: center;">
        Vous avez jusqu'au coup d'envoi du premier match.
    </p>
    '''

    return get_base_template(content, "Dernier Rappel")


# ============================================
# EMAILS ADMIN : SYNTHESE & RESULTATS
# ============================================

def email_synthese_paris(semaine_id, data_paris, jokers_actifs=None, stats_matchs=None):
    """
    Email de synthese des paris de tous les joueurs
    Envoye 15min apres la deadline
    data_paris: liste de dicts {pseudo, matchs: [{equipes, prono, mise}]}
    jokers_actifs: liste de dicts {pseudo, type_joker, cible_pseudo}
    stats_matchs: dict {equipes: {dom: %, nul: %, ext: %}}
    """
    if jokers_actifs is None:
        jokers_actifs = []
    if stats_matchs is None:
        stats_matchs = {}

    # === SECTION JOKERS ACTIFS ===
    jokers_html = ""
    if jokers_actifs:
        jokers_items = ""
        for joker in jokers_actifs:
            pseudo = joker.get('pseudo', '?')
            type_j = joker.get('type_joker', '')
            cible = joker.get('cible_pseudo', '')

            if type_j == 'double':
                jokers_items += f'''
                <div style="display: flex; align-items: center; padding: 10px; margin: 5px 0; background: rgba(255, 215, 0, 0.1); border-radius: 8px; border-left: 4px solid #FFD700;">
                    <span style="font-size: 24px; margin-right: 12px;">x2</span>
                    <div>
                        <div style="color: #FFD700; font-weight: bold;">@{pseudo}</div>
                        <div style="color: #AAAAAA; font-size: 12px;">Points Doubles actives</div>
                    </div>
                </div>
                '''
            elif type_j == 'vol':
                jokers_items += f'''
                <div style="display: flex; align-items: center; padding: 10px; margin: 5px 0; background: rgba(155, 89, 182, 0.1); border-radius: 8px; border-left: 4px solid #9b59b6;">
                    <span style="font-size: 24px; margin-right: 12px;">🎭</span>
                    <div>
                        <div style="color: #9b59b6; font-weight: bold;">@{pseudo}</div>
                        <div style="color: #AAAAAA; font-size: 12px;">Vole les pronos de <strong style="color: #fff;">@{cible}</strong></div>
                    </div>
                </div>
                '''

        jokers_html = f'''
        <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #FFD700; margin: 0 0 15px 0; font-size: 16px;">🃏 Jokers Actives cette semaine</h3>
            {jokers_items}
        </div>
        '''
    else:
        jokers_html = '''
        <div style="background: #0a0a1a; border: 1px solid #333; border-radius: 10px; padding: 15px; margin: 20px 0; text-align: center;">
            <p style="color: #666; margin: 0;">Aucun joker active cette semaine</p>
        </div>
        '''

    # === SECTION STATISTIQUES PAR MATCH ===
    stats_html = ""
    if stats_matchs:
        stats_rows = ""
        for match_name, tendances in stats_matchs.items():
            pct_dom = tendances.get('dom', 0)
            pct_nul = tendances.get('nul', 0)
            pct_ext = tendances.get('ext', 0)

            stats_rows += f'''
            <div style="margin: 10px 0; padding: 12px; background: #1a1a2e; border-radius: 8px;">
                <div style="color: #ccc; font-size: 13px; margin-bottom: 8px;">{match_name}</div>
                <div style="display: flex; height: 24px; border-radius: 4px; overflow: hidden; background: #333;">
                    <div style="width: {pct_dom}%; background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); display: flex; align-items: center; justify-content: center;">
                        <span style="color: #fff; font-size: 11px; font-weight: bold;">{pct_dom}%</span>
                    </div>
                    <div style="width: {pct_nul}%; background: linear-gradient(135deg, #7f8c8d 0%, #95a5a6 100%); display: flex; align-items: center; justify-content: center;">
                        <span style="color: #fff; font-size: 11px; font-weight: bold;">{pct_nul}%</span>
                    </div>
                    <div style="width: {pct_ext}%; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); display: flex; align-items: center; justify-content: center;">
                        <span style="color: #fff; font-size: 11px; font-weight: bold;">{pct_ext}%</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 10px; color: #666;">
                    <span>🏠 Dom</span>
                    <span>🤝 Nul</span>
                    <span>✈️ Ext</span>
                </div>
            </div>
            '''

        stats_html = f'''
        <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #FFD700; margin: 0 0 10px 0; font-size: 16px;">📊 Tendances des Pronos</h3>
            <p style="color: #AAAAAA; font-size: 12px; margin: 0 0 15px 0;">Repartition des pronostics par match</p>
            {stats_rows}
        </div>
        '''

    # === TABLEAU DES PRONOSTICS ===
    rows_html = ""
    for joueur in data_paris:
        pseudo = joueur['pseudo']
        joker_badge = ""

        # Verifier si ce joueur a un joker actif
        for j in jokers_actifs:
            if j.get('pseudo') == pseudo:
                if j.get('type_joker') == 'double':
                    joker_badge = ' <span style="background: #FFD700; color: #000; padding: 2px 6px; border-radius: 4px; font-size: 10px;">x2</span>'
                elif j.get('type_joker') == 'vol':
                    joker_badge = ' <span style="background: #9b59b6; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px;">🎭</span>'
                break

        for i, match in enumerate(joueur.get('matchs', [])):
            equipes = match.get('equipes', 'Match inconnu')
            prono = f"{match.get('home', '?')}-{match.get('away', '?')}"
            mise = match.get('mise', 0)

            if i == 0:
                rows_html += f'''
                <tr style="border-bottom: 1px solid #333;">
                    <td rowspan="{len(joueur.get('matchs', []))}" style="padding: 10px; color: #FFD700; font-weight: bold; vertical-align: top; border-right: 1px solid #333;">
                        @{pseudo}{joker_badge}
                    </td>
                    <td style="padding: 8px; color: #ccc;">{equipes}</td>
                    <td style="padding: 8px; color: #fff; text-align: center; font-weight: bold;">{prono}</td>
                    <td style="padding: 8px; color: #FFD700; text-align: center;">{mise} pts</td>
                </tr>
                '''
            else:
                rows_html += f'''
                <tr style="border-bottom: 1px solid #222;">
                    <td style="padding: 8px; color: #ccc;">{equipes}</td>
                    <td style="padding: 8px; color: #fff; text-align: center; font-weight: bold;">{prono}</td>
                    <td style="padding: 8px; color: #FFD700; text-align: center;">{mise} pts</td>
                </tr>
                '''

    content = f'''
    <h2>Synthese des Paris - Semaine {semaine_id}</h2>
    <p>Les pronostics sont clos ! Voici le recapitulatif complet des paris de la semaine.</p>

    {jokers_html}

    {stats_html}

    <div style="background: #0a0a1a; border-radius: 10px; padding: 15px; margin: 20px 0; overflow-x: auto;">
        <h3 style="color: #FFD700; margin: 0 0 15px 0; font-size: 16px;">📋 Tableau des Mises</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <thead>
                <tr style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);">
                    <th style="padding: 12px; color: #0a0a1a; text-align: left;">Joueur</th>
                    <th style="padding: 12px; color: #0a0a1a; text-align: left;">Match</th>
                    <th style="padding: 12px; color: #0a0a1a; text-align: center;">Prono</th>
                    <th style="padding: 12px; color: #0a0a1a; text-align: center;">Mise</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>

    <div class="highlight-box">
        <p style="color: #FFD700; margin: 0;">Que le meilleur gagne !</p>
        <p style="color: #AAAAAA; font-size: 12px; margin: 5px 0 0 0;">
            Les resultats seront calcules automatiquement apres les matchs.
        </p>
    </div>
    '''

    return get_base_template(content, "Synthese des Paris")


def email_resultats_ironiques(semaine_id, classement, commentaires, donnees_speciales=None):
    """
    Email de resultats avec commentaires ironiques
    classement: liste de dicts {pseudo, points, rang, evolution, grand_chelem, scores_exacts, joker_vol_utilise, joker_vol_reussi, lanterne_rouge}
    commentaires: dict {pseudo: commentaire_ironique} (surcharge manuelle)
    donnees_speciales: dict optionnel avec infos supplementaires par pseudo
    """
    if donnees_speciales is None:
        donnees_speciales = {}

    total_joueurs = len(classement)

    # Construire le classement HTML
    classement_html = ""
    for joueur in classement:
        rang = joueur.get('rang', '?')
        pseudo = joueur.get('pseudo', 'Inconnu')
        points = joueur.get('points', 0)
        evolution = joueur.get('evolution', 0)

        # Emoji d'evolution
        if evolution > 0:
            evo_emoji = f"<span style='color: #00FF00;'>↑ +{evolution}</span>"
        elif evolution < 0:
            evo_emoji = f"<span style='color: #FF4444;'>↓ {evolution}</span>"
        else:
            evo_emoji = "<span style='color: #AAAAAA;'>→ 0</span>"

        # Couleur selon le rang
        if rang == 1:
            rang_style = "background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #0a0a1a;"
        elif rang == total_joueurs:
            rang_style = "background: #8B0000; color: #fff;"
        elif rang <= 3:
            rang_style = "background: #C0C0C0; color: #0a0a1a;"
        else:
            rang_style = "background: #333; color: #fff;"

        # Generer commentaire ironique intelligent
        if pseudo in commentaires:
            commentaire = commentaires[pseudo]
        else:
            # Preparer les donnees du joueur pour le generateur
            joueur_data = {
                'rang': rang,
                'total_joueurs': total_joueurs,
                'evolution': evolution,
                'grand_chelem': joueur.get('grand_chelem', False),
                'scores_exacts': joueur.get('scores_exacts', 0),
                'joker_vol_utilise': joueur.get('joker_vol_utilise', False),
                'joker_vol_reussi': joueur.get('joker_vol_reussi', False),
                'lanterne_rouge': joueur.get('lanterne_rouge', False),
            }
            # Fusionner avec donnees speciales si disponibles
            if pseudo in donnees_speciales:
                joueur_data.update(donnees_speciales[pseudo])

            commentaire = generer_commentaire_joueur(joueur_data)

        classement_html += f'''
        <div style="
            display: flex;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            background: #1a1a2e;
            border-radius: 10px;
            border: 1px solid #333;
        ">
            <div style="
                {rang_style}
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 18px;
                margin-right: 15px;
            ">{rang}</div>
            <div style="flex: 1;">
                <div style="color: #FFD700; font-weight: bold;">@{pseudo}</div>
                <div style="color: #666; font-size: 12px; font-style: italic;">{commentaire}</div>
            </div>
            <div style="text-align: right;">
                <div style="color: #fff; font-size: 18px; font-weight: bold;">{points} pts</div>
                <div style="font-size: 12px;">{evo_emoji}</div>
            </div>
        </div>
        '''

    content = f'''
    <h2>Resultats Semaine {semaine_id}</h2>
    <p>Les matchs sont termines ! Voici qui a brille... et qui s'est plante.</p>

    <div style="margin: 25px 0;">
        {classement_html}
    </div>

    <div class="highlight-box" style="border-color: #9b59b6; background: rgba(155, 89, 182, 0.1);">
        <p style="color: #9b59b6; margin: 0; font-size: 14px;">
            "Le football, c'est simple : 22 joueurs courent apres un ballon,
            et a la fin... c'est toujours quelqu'un d'autre qui gagne !"
        </p>
    </div>

    <p style="text-align: center;">
        <a href="#" class="button">Voir le classement complet</a>
    </p>

    <p style="color: #AAAAAA; font-size: 12px; text-align: center;">
        Rendez-vous la semaine prochaine pour de nouveaux pronostics !
    </p>
    '''

    return get_base_template(content, "Resultats de la Semaine")


# ============================================
# ENVOI DE CAMPAGNES
# ============================================

## envoyer_campagne_lancement supprime (non utilise)


def envoyer_email_bienvenue(utilisateur):
    """Envoie l'email de bienvenue a un nouvel inscrit"""
    html = email_bienvenue(utilisateur)
    return send_email(
        utilisateur['email'],
        "Bienvenue dans le Club Elite Pronos ! (Validation de votre compte)",
        html
    )


def email_alerte_nouvel_inscrit(pseudo, prenom, parrain, email):
    """Email d'alerte admin pour un nouvel inscrit"""
    date_inscription = datetime.now().strftime('%d/%m/%Y a %H:%M')

    content = f'''
    <h2>Nouvelle inscription !</h2>
    <p>Un nouveau joueur vient de s'inscrire sur Elite Pronos.</p>

    <div class="highlight-box">
        <div style="text-align: left;">
            <p style="margin: 5px 0;"><strong style="color: #FFD700;">Pseudo :</strong> <span style="color: #fff;">@{pseudo}</span></p>
            <p style="margin: 5px 0;"><strong style="color: #FFD700;">Prenom :</strong> <span style="color: #fff;">{prenom or "Non renseigne"}</span></p>
            <p style="margin: 5px 0;"><strong style="color: #FFD700;">Email :</strong> <span style="color: #fff;">{email}</span></p>
            <p style="margin: 5px 0;"><strong style="color: #FFD700;">Parrain :</strong> <span style="color: #00FF00; font-weight: bold;">{parrain}</span></p>
            <p style="margin: 5px 0;"><strong style="color: #FFD700;">Date :</strong> <span style="color: #AAAAAA;">{date_inscription}</span></p>
        </div>
    </div>

    <p style="color: #ff6b6b;">
        <strong>Action requise :</strong> Validez cette inscription dans le panel admin apres reception du paiement.
    </p>

    <p style="text-align: center;">
        <a href="#" class="button">Acceder au Panel Admin</a>
    </p>
    '''

    return get_base_template(content, "Nouvel Inscrit")


def envoyer_alerte_nouvel_inscrit(pseudo, prenom, parrain, email):
    """Envoie une alerte email a l'admin pour chaque nouvel inscrit"""
    ADMIN_EMAIL = "elite.pronos.2@gmail.com"
    html = email_alerte_nouvel_inscrit(pseudo, prenom, parrain, email)
    return send_email(
        ADMIN_EMAIL,
        f"Elite Pronos - Nouvel inscrit: @{pseudo} (Parrain: {parrain})",
        html
    )


## envoyer_rappels_j7 et envoyer_rappels_j1 supprimes
## (utilisaient SQLite, non appeles depuis l'admin)


def envoyer_synthese_paris(semaine_id):
    """
    Envoie la synthese des paris a tous les joueurs
    A appeler 15min apres la deadline
    Version Supabase
    """
    from modules.supabase_db import get_supabase
    supabase = get_supabase()

    # Recuperer les matchs de la semaine
    matchs = supabase._request('GET', f'matches?semaine_id=eq.{semaine_id}&select=id,equipe_home,equipe_away') or []
    match_ids = [m['id'] for m in matchs]
    match_map = {m['id']: m for m in matchs}

    if not match_ids:
        return []

    # Recuperer toutes les predictions pour ces matchs
    predictions = supabase._request('GET', f'predictions?match_id=in.({",".join(map(str, match_ids))})&select=user_id,match_id,score_prono_home,score_prono_away,mise_points') or []

    # Recuperer les utilisateurs
    users = supabase._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo') or []
    user_map = {u['id']: u['pseudo'] for u in users}

    # Construire les rows (pseudo, user_id, home, away, prono_h, prono_a, mise)
    rows = []
    for p in predictions:
        match = match_map.get(p['match_id'])
        pseudo = user_map.get(p['user_id'], 'Inconnu')
        if match:
            rows.append((pseudo, p['user_id'], match['equipe_home'], match['equipe_away'],
                        p['score_prono_home'], p['score_prono_away'], p['mise_points']))

    # Trier par pseudo puis match_id
    rows.sort(key=lambda x: (x[0], x[2]))

    # === RECUPERER LES JOKERS ACTIFS ===
    jokers_data = supabase._request('GET', f'jokers_historique?semaine_id=eq.{semaine_id}&select=utilisateur_id,type_joker,cible_vol_id') or []

    jokers_actifs = []
    for jrow in jokers_data:
        pseudo = user_map.get(jrow['utilisateur_id'], 'Inconnu')
        cible_pseudo = user_map.get(jrow.get('cible_vol_id'), '') if jrow.get('cible_vol_id') else ''
        jokers_actifs.append({
            'pseudo': pseudo,
            'type_joker': jrow['type_joker'],
            'cible_pseudo': cible_pseudo
        })

    # Organiser par joueur
    data_paris = {}
    stats_brut = {}  # Pour calculer les tendances

    for row in rows:
        pseudo, user_id, home, away, prono_h, prono_a, mise = row
        match_key = f"{home} vs {away}"

        if pseudo not in data_paris:
            data_paris[pseudo] = {'pseudo': pseudo, 'matchs': []}
        data_paris[pseudo]['matchs'].append({
            'equipes': match_key,
            'home': prono_h,
            'away': prono_a,
            'mise': mise
        })

        # Calculer les tendances 1/N/2
        if match_key not in stats_brut:
            stats_brut[match_key] = {'dom': 0, 'nul': 0, 'ext': 0, 'total': 0}

        stats_brut[match_key]['total'] += 1
        if prono_h > prono_a:
            stats_brut[match_key]['dom'] += 1
        elif prono_h == prono_a:
            stats_brut[match_key]['nul'] += 1
        else:
            stats_brut[match_key]['ext'] += 1

    # Convertir en pourcentages
    stats_matchs = {}
    for match_key, counts in stats_brut.items():
        total = counts['total']
        if total > 0:
            stats_matchs[match_key] = {
                'dom': round(counts['dom'] * 100 / total),
                'nul': round(counts['nul'] * 100 / total),
                'ext': round(counts['ext'] * 100 / total)
            }
            # Ajuster pour que la somme fasse 100%
            diff = 100 - (stats_matchs[match_key]['dom'] + stats_matchs[match_key]['nul'] + stats_matchs[match_key]['ext'])
            if diff != 0:
                stats_matchs[match_key]['nul'] += diff

    # Envoyer a tous les utilisateurs
    utilisateurs = get_utilisateurs_emails()
    resultats = []

    html = email_synthese_paris(semaine_id, list(data_paris.values()), jokers_actifs, stats_matchs)

    for user in utilisateurs:
        success, msg = send_email(
            user['email'],
            f"Elite Pronos - Synthese des Paris (Semaine {semaine_id})",
            html
        )
        resultats.append({'user': user['pseudo'], 'success': success, 'message': msg})

    return resultats


def envoyer_resultats_ironiques(semaine_id):
    """
    Envoie le recapitulatif des resultats avec commentaires ironiques
    A appeler apres le calcul des points
    Version Supabase
    """
    from modules.supabase_db import get_supabase
    supabase = get_supabase()

    # Recuperer les matchs de la semaine
    matchs = supabase._request('GET', f'matches?semaine_id=eq.{semaine_id}&select=id') or []
    match_ids = [m['id'] for m in matchs]

    # Recuperer les utilisateurs actifs
    users = supabase._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo') or []
    user_map = {u['id']: u['pseudo'] for u in users}

    # Calculer les points par utilisateur pour cette semaine
    points_par_user = {u['id']: 0 for u in users}

    if match_ids:
        predictions = supabase._request('GET', f'predictions?match_id=in.({",".join(map(str, match_ids))})&select=user_id,points_gagnes') or []
        for p in predictions:
            if p['user_id'] in points_par_user and p.get('points_gagnes') is not None:
                points_par_user[p['user_id']] += p['points_gagnes']

    # Trier par points decroissants
    sorted_users = sorted(points_par_user.items(), key=lambda x: x[1], reverse=True)

    # Construire le classement
    classement = []
    for i, (user_id, points) in enumerate(sorted_users, 1):
        classement.append({
            'rang': i,
            'pseudo': user_map.get(user_id, 'Inconnu'),
            'points': points,
            'evolution': 0  # TODO: calculer par rapport a la semaine precedente
        })

    # Generer des commentaires ironiques personnalises
    commentaires = {}  # On laisse le systeme generer aleatoirement

    # Envoyer a tous les utilisateurs
    utilisateurs = get_utilisateurs_emails()
    resultats = []

    html = email_resultats_ironiques(semaine_id, classement, commentaires)

    for user in utilisateurs:
        success, msg = send_email(
            user['email'],
            f"Elite Pronos - Resultats Semaine {semaine_id}",
            html
        )
        resultats.append({'user': user['pseudo'], 'success': success, 'message': msg})

    return resultats


# ============================================
# TEST
# ============================================

def test_email_template():
    """Teste le rendu des templates"""
    user_test = {
        'id': 1,
        'pseudo': 'TestUser',
        'prenom': 'Jean',
        'email': 'test@example.com'
    }

    # Donnees de test pour synthese
    data_paris_test = [
        {
            'pseudo': 'Baggio10',
            'matchs': [
                {'equipes': 'PSG vs OM', 'home': 2, 'away': 1, 'mise': 30},
                {'equipes': 'Lyon vs Monaco', 'home': 1, 'away': 1, 'mise': 25}
            ]
        },
        {
            'pseudo': 'Zidane98',
            'matchs': [
                {'equipes': 'PSG vs OM', 'home': 3, 'away': 0, 'mise': 40},
                {'equipes': 'Lyon vs Monaco', 'home': 0, 'away': 2, 'mise': 20}
            ]
        }
    ]

    # Donnees de test pour resultats
    classement_test = [
        {'rang': 1, 'pseudo': 'Baggio10', 'points': 85, 'evolution': 2},
        {'rang': 2, 'pseudo': 'Zidane98', 'points': 72, 'evolution': -1},
        {'rang': 3, 'pseudo': 'Henry14', 'points': 65, 'evolution': 0}
    ]

    print("=== TEST TEMPLATES EMAIL ===\n")

    templates = [
        ("Lancement Saison", email_lancement_saison(user_test)),
        ("Bienvenue", email_bienvenue(user_test)),
        ("Rappel J-7", email_rappel_j7(user_test)),
        ("Rappel J-1", email_rappel_j1(user_test)),
        ("Synthese Paris", email_synthese_paris(1, data_paris_test)),
        ("Resultats Ironiques", email_resultats_ironiques(1, classement_test, {}))
    ]

    for name, html in templates:
        print(f"[OK] Template '{name}' genere ({len(html)} caracteres)")

    print("\n=== FIN TEST ===")
    return True


if __name__ == "__main__":
    test_email_template()
