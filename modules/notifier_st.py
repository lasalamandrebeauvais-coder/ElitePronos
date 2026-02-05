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
    """Recupere la configuration SMTP depuis Streamlit secrets ou env"""
    return {
        'host': get_streamlit_secret('SMTP_HOST', 'smtp.gmail.com'),
        'port': int(get_streamlit_secret('SMTP_PORT', '587')),
        'user': get_streamlit_secret('SMTP_USER', ''),
        'password': get_streamlit_secret('SMTP_PASSWORD', '')
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


def email_prospection(lien_inscription="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/"):
    """Email de prospection/lancement pour inviter de nouveaux joueurs"""

    content = f'''
    <h2 style="color: #FFD700; text-align: center;">L'heritage de Gillou continue :<br>Elite Pronos passe au niveau superieur !</h2>

    <p>Bonjour a tous les passionnes,</p>

    <p>Pendant plus de <strong style="color: #FFD700;">10 ans</strong>, Gillou, notre maitre du jeu,
    a fait vibrer cette communaute. Entre les sacres des grands champions, la complicite des duos
    de pronostiqueurs et les batailles acharnees pour grimper sur le podium, nous avons vecu des
    moments inoubliables.</p>

    <p>Aujourd'hui, pour honorer cet heritage et faire perdurer l'esprit de competition qu'il a
    instaure, j'ai le plaisir de vous annoncer la naissance de la nouvelle version :
    <strong style="color: #FFD700;">Elite Pronos</strong>.</p>

    <div class="highlight-box">
        <div class="big-text">Le jeu que vous avez aime, modernise</div>
        <p style="margin: 10px 0 0 0; color: #cccccc;">
            Nous avons garde l'essence meme de ce qui faisait le succes de nos tournois,
            mais avec une nouveaute majeure : <strong style="color: #FFD700;">une application dediee</strong>.
        </p>
    </div>

    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #333; width: 40px; text-align: center;">
                <span style="font-size: 1.5em;">⚡</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333; color: #cccccc;">
                <strong style="color: #FFD700;">Fini la gestion manuelle</strong><br>
                Tout est automatise pour une gestion simplifiee.
            </td>
        </tr>
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #333; width: 40px; text-align: center;">
                <span style="font-size: 1.5em;">🔥</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333; color: #cccccc;">
                <strong style="color: #FFD700;">L'adrenaline intacte</strong><br>
                Retrouvez les classements en direct et les defis qui ont fait notre reputation.
            </td>
        </tr>
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #333; width: 40px; text-align: center;">
                <span style="font-size: 1.5em;">🤝</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333; color: #cccccc;">
                <strong style="color: #FFD700;">L'esprit de groupe</strong><br>
                Que vous soyez un loup solitaire du prono ou que vous aimiez jouer en duo,
                le podium vous attend !
            </td>
        </tr>
    </table>

    <div class="highlight-box">
        <div style="font-size: 1.2em; color: #FFD700; font-weight: bold;">
            Reprenez votre place dans l'arene !
        </div>
        <p style="margin: 10px 0 0 0; color: #cccccc;">
            Le jeu a ete revisite pour etre plus moderne et prenant que jamais.
            Il ne manque plus que les anciens champions et de nouveaux visages
            pour relancer la machine.
        </p>
    </div>

    <p style="text-align: center;">
        <a href="{lien_inscription}" class="button">Decouvrir l'application et s'inscrire</a>
    </p>

    <p style="color: #cccccc;">
        N'hesitez pas a inviter vos amis ou vos anciens partenaires de duo.
        Plus la communaute sera grande, plus la victoire sera belle.
    </p>

    <p style="text-align: center; font-size: 1.1em; margin-top: 25px;">
        <strong style="color: #FFD700;">Pour Gillou, pour le jeu, et pour la gagne !</strong>
    </p>

    <p style="color: #cccccc;">A tres vite sur l'appli,<br>
    <strong style="color: #FFD700;">L'equipe Elite Pronos</strong></p>
    '''

    return get_base_template(content, "Elite Pronos")


def envoyer_email_prospection(destinataires_emails):
    """
    Envoie l'email de prospection a une liste d'adresses email.
    destinataires_emails: liste de strings (adresses email)
    Retourne (nb_envoyes, nb_erreurs, details)
    """
    html = email_prospection()
    sujet = "L'heritage de Gillou continue : Elite Pronos passe au niveau superieur !"

    nb_ok = 0
    nb_err = 0
    details = []

    for email_addr in destinataires_emails:
        email_addr = email_addr.strip()
        if not email_addr:
            continue
        success, msg = send_email(email_addr, sujet, html)
        if success:
            nb_ok += 1
        else:
            nb_err += 1
        details.append((email_addr, success, msg))

    return nb_ok, nb_err, details


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

def email_synthese_paris(semaine_id, jokers_actifs=None, stats_matchs=None, commentaire_bot=""):
    """
    Email de synthese des paris de tous les joueurs
    Envoye 15min apres la deadline
    jokers_actifs: liste de dicts {pseudo, type_joker, cible_pseudo}
    stats_matchs: dict {equipes: {dom: %, nul: %, ext: %}}
    commentaire_bot: commentaire ironique du bot
    """
    if jokers_actifs is None:
        jokers_actifs = []
    if stats_matchs is None:
        stats_matchs = {}

    # === COMMENTAIRE DU BOT ===
    commentaire_html = ""
    if commentaire_bot:
        commentaire_html = f'''
        <div style="background: rgba(155, 89, 182, 0.1); border: 1px solid #9b59b6; border-radius: 10px; padding: 20px; margin: 20px 0;">
            <div style="display: flex; align-items: flex-start;">
                <div style="font-size: 32px; margin-right: 15px;">🤖</div>
                <div>
                    <div style="color: #9b59b6; font-weight: bold; font-size: 14px; margin-bottom: 8px;">Kingo - Le Bot Elite</div>
                    <p style="color: #cccccc; margin: 0; line-height: 1.6; font-style: italic;">{commentaire_bot}</p>
                </div>
            </div>
        </div>
        '''

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

    content = f'''
    <h2>Synthese des Paris - Semaine {semaine_id}</h2>
    <p>Les pronostics sont clos ! Voici le recapitulatif de la semaine.</p>

    {commentaire_html}

    {jokers_html}

    {stats_html}

    <div class="highlight-box">
        <p style="color: #FFD700; margin: 0;">Que le meilleur gagne !</p>
        <p style="color: #AAAAAA; font-size: 12px; margin: 5px 0 0 0;">
            Les resultats seront calcules automatiquement apres les matchs.
        </p>
    </div>
    '''

    return get_base_template(content, "Synthese des Paris")


def email_resultats_ironiques(semaine_id, classement, matchs_resultats, commentaire_bot=""):
    """
    Email de resultats avec debrief ironique du bot
    classement: liste de dicts {pseudo, points, rang, bons_pronos, scores_exacts, grand_chelem}
    matchs_resultats: liste de dicts {equipe_home, equipe_away, score_final_home, score_final_away}
    commentaire_bot: debrief ironique genere par Kingo
    """
    total_joueurs = len(classement)

    # === COMMENTAIRE DU BOT ===
    commentaire_html = ""
    if commentaire_bot:
        commentaire_html = f'''
        <div style="background: rgba(155, 89, 182, 0.1); border: 1px solid #9b59b6; border-radius: 10px; padding: 20px; margin: 20px 0;">
            <div style="display: flex; align-items: flex-start;">
                <div style="font-size: 32px; margin-right: 15px;">🤖</div>
                <div>
                    <div style="color: #9b59b6; font-weight: bold; font-size: 14px; margin-bottom: 8px;">Kingo - Le Debrief</div>
                    <p style="color: #cccccc; margin: 0; line-height: 1.8; font-style: italic;">{commentaire_bot}</p>
                </div>
            </div>
        </div>
        '''

    # === RESULTATS DES MATCHS ===
    matchs_html = ""
    if matchs_resultats:
        matchs_items = ""
        for m in matchs_resultats:
            matchs_items += f'''
            <div style="display: flex; align-items: center; padding: 10px; margin: 5px 0; background: #1a1a2e; border-radius: 8px;">
                <div style="flex: 1; text-align: right; color: #ccc; font-size: 13px;">{m['equipe_home']}</div>
                <div style="margin: 0 15px; padding: 5px 15px; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 5px; color: #0a0a1a; font-weight: bold; font-size: 16px;">{m['score_final_home']} - {m['score_final_away']}</div>
                <div style="flex: 1; text-align: left; color: #ccc; font-size: 13px;">{m['equipe_away']}</div>
            </div>
            '''
        matchs_html = f'''
        <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #FFD700; margin: 0 0 15px 0; font-size: 16px;">⚽ Resultats des Matchs</h3>
            {matchs_items}
        </div>
        '''

    # === CLASSEMENT ===
    classement_html = ""
    for joueur in classement:
        rang = joueur.get('rang', '?')
        pseudo = joueur.get('pseudo', 'Inconnu')
        points = joueur.get('points', 0)
        bons = joueur.get('bons_pronos', 0)
        se = joueur.get('scores_exacts', 0)

        # Couleur selon le rang
        if rang == 1:
            rang_style = "background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #0a0a1a;"
        elif rang == total_joueurs:
            rang_style = "background: #8B0000; color: #fff;"
        elif rang <= 3:
            rang_style = "background: #C0C0C0; color: #0a0a1a;"
        else:
            rang_style = "background: #333; color: #fff;"

        # Badges
        badges = ""
        if joueur.get('grand_chelem'):
            badges += ' <span style="background: #FFD700; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 10px;">GRAND CHELEM</span>'
        if se > 0:
            badges += f' <span style="background: #27ae60; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 10px;">{se} SE</span>'

        # Stats sous le pseudo
        stats_line = f"{bons}/4 corrects"
        if se > 0:
            stats_line += f" dont {se} score(s) exact(s)"

        classement_html += f'''
        <div style="display: flex; align-items: center; padding: 15px; margin: 10px 0; background: #1a1a2e; border-radius: 10px; border: 1px solid #333;">
            <div style="{rang_style} width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; margin-right: 15px; flex-shrink: 0;">{rang}</div>
            <div style="flex: 1;">
                <div style="color: #FFD700; font-weight: bold;">@{pseudo}{badges}</div>
                <div style="color: #888; font-size: 12px; margin-top: 4px;">{stats_line}</div>
            </div>
            <div style="text-align: right; flex-shrink: 0;">
                <div style="color: #fff; font-size: 18px; font-weight: bold;">{points} pts</div>
            </div>
        </div>
        '''

    content = f'''
    <h2>Resultats Semaine {semaine_id}</h2>
    <p>Les matchs sont termines ! Voici qui a brille... et qui s'est plante.</p>

    {commentaire_html}

    {matchs_html}

    <div style="margin: 25px 0;">
        <h3 style="color: #FFD700; margin: 0 0 15px 0; font-size: 16px;">🏆 Classement de la Semaine</h3>
        {classement_html}
    </div>

    <p style="text-align: center;">
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/" class="button">Voir le classement complet</a>
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


def _generer_commentaire_email(stats):
    """
    Genere un commentaire ironique du bot pour l'email de synthese.
    Avant deadline (matchs_termines == 0): evasif, pas de noms.
    Apres deadline: peut reveler des infos.
    """
    commentaires = []
    deadline_passee = stats.get('matchs_termines', 0) > 0
    nb = stats.get('nb_joueurs', 0)

    if nb == 0:
        return "Personne n'a encore joue cette semaine. Vous attendez quoi ? Que les matchs se jouent sans vous ?"
    elif nb == 1:
        commentaires.append("Un seul brave a ose jouer pour l'instant. Les autres ont peur ou quoi ?")
    elif nb < 5:
        commentaires.append(f"Seulement {nb} joueurs ont fait leurs pronos. Les absents ont toujours tort !")
    else:
        commentaires.append(f"{nb} pronostiqueurs en lice cette semaine. Que le spectacle commence !")

    # Grosses mises
    if stats.get('grosses_mises'):
        if deadline_passee:
            gros = stats['grosses_mises'][0]
            commentaires.append(f"{gros['pseudo']} a mise gros ({gros['mise']} pts) sur {gros['match']}. Confiance ou folie ?")
        else:
            phrases = [
                "Quelqu'un a sorti l'artillerie lourde cette semaine... Mais qui ?",
                "Une grosse mise a ete placee. Le suspense reste entier !",
                "Des paris audacieux ont ete enregistres. Je ne dirai rien de plus !",
            ]
            commentaires.append(random.choice(phrases))

    # Jokers
    if stats.get('jokers'):
        nb_jokers = len(stats['jokers'])
        if deadline_passee:
            joker = stats['jokers'][0]
            if joker['type'] == 'DOUBLE':
                commentaires.append(f"{joker['pseudo']} a joue son joker Points Doubles. Ca passe ou ca casse !")
            else:
                commentaires.append(f"{joker['pseudo']} a utilise le vol de pronostics. Strategie ou desespoir ?")
        else:
            if nb_jokers == 1:
                commentaires.append("Un joker a ete active... Lequel et par qui ? Mystere !")
            else:
                commentaires.append(f"{nb_jokers} jokers actives cette semaine ! Ca va chauffer...")

    # Tendances unanimes
    for m in stats.get('matchs', []):
        if m['pct_home'] >= 70:
            commentaires.append(f"{m['pct_home']}% voient {m['home']} gagner. Unanimite ou piege ?")
            break
        elif m['pct_away'] >= 70:
            commentaires.append(f"{m['pct_away']}% misent sur {m['away']}. Et si c'etait trop beau ?")
            break
        elif m['pct_nul'] >= 50:
            commentaires.append(f"{m['pct_nul']}% predisent un nul pour {m['home']} vs {m['away']}. Le foot est impredictible !")
            break

    return " ".join(commentaires)


def envoyer_synthese_paris(semaine_id):
    """
    Envoie la synthese des paris a tous les joueurs
    A appeler 15min apres la deadline
    Version Supabase
    """
    from modules.supabase_db import get_supabase
    supabase = get_supabase()

    # Recuperer les matchs de la semaine
    matchs = supabase._request('GET', f'matches?semaine_id=eq.{semaine_id}&is_active=eq.true&select=id,equipe_home,equipe_away,score_final_home') or []
    match_ids = [m['id'] for m in matchs]
    match_map = {m['id']: m for m in matchs}

    if not match_ids:
        return []

    # Recuperer toutes les predictions pour ces matchs
    predictions = supabase._request('GET', f'predictions?match_id=in.({",".join(map(str, match_ids))})&select=user_id,match_id,score_prono_home,score_prono_away,mise_points') or []

    # Recuperer les utilisateurs
    users = supabase._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo') or []
    user_map = {u['id']: u['pseudo'] for u in users}

    # === RECUPERER LES JOKERS ACTIFS ===
    jokers_data = supabase._request('GET', f'jokers_historique?semaine_id=eq.{semaine_id}&select=utilisateur_id,type_joker') or []

    jokers_actifs = []
    for jrow in jokers_data:
        pseudo = user_map.get(jrow['utilisateur_id'], 'Inconnu')
        jokers_actifs.append({
            'pseudo': pseudo,
            'type_joker': jrow['type_joker'].lower(),
            'cible_pseudo': ''
        })

    # Calculer les tendances 1/N/2
    stats_brut = {}
    grosses_mises = []

    for p in predictions:
        match = match_map.get(p['match_id'])
        if not match:
            continue
        pseudo = user_map.get(p['user_id'], 'Inconnu')
        match_key = f"{match['equipe_home']} vs {match['equipe_away']}"
        prono_h = p['score_prono_home']
        prono_a = p['score_prono_away']
        mise = p.get('mise_points', 0) or 0

        if match_key not in stats_brut:
            stats_brut[match_key] = {'dom': 0, 'nul': 0, 'ext': 0, 'total': 0}

        stats_brut[match_key]['total'] += 1
        if prono_h > prono_a:
            stats_brut[match_key]['dom'] += 1
        elif prono_h == prono_a:
            stats_brut[match_key]['nul'] += 1
        else:
            stats_brut[match_key]['ext'] += 1

        # Tracker les grosses mises pour le commentaire
        if mise >= 40:
            grosses_mises.append({'pseudo': pseudo, 'mise': mise, 'match': match_key})

    # Convertir en pourcentages
    stats_matchs = {}
    stats_for_comment = []  # Pour generer le commentaire du bot
    for match_key, counts in stats_brut.items():
        total = counts['total']
        if total > 0:
            pct_dom = round(counts['dom'] * 100 / total)
            pct_nul = round(counts['nul'] * 100 / total)
            pct_ext = round(counts['ext'] * 100 / total)
            diff = 100 - (pct_dom + pct_nul + pct_ext)
            if diff:
                pct_nul += diff
            stats_matchs[match_key] = {'dom': pct_dom, 'nul': pct_nul, 'ext': pct_ext}

            # Extraire les equipes pour le commentaire
            parts = match_key.split(' vs ')
            stats_for_comment.append({
                'home': parts[0] if len(parts) > 0 else '?',
                'away': parts[1] if len(parts) > 1 else '?',
                'pct_home': pct_dom,
                'pct_away': pct_ext,
                'pct_nul': pct_nul
            })

    # Generer le commentaire ironique du bot
    nb_joueurs = len(set(p['user_id'] for p in predictions))
    matchs_termines = sum(1 for m in matchs if m.get('score_final_home') is not None)

    grosses_mises.sort(key=lambda x: x['mise'], reverse=True)

    stats_comment = {
        'nb_joueurs': nb_joueurs,
        'nb_pronostics': len(predictions),
        'matchs_termines': matchs_termines,
        'total_matchs': len(matchs),
        'matchs': stats_for_comment,
        'jokers': [{'pseudo': j['pseudo'], 'type': j['type_joker'].upper()} for j in jokers_actifs],
        'grosses_mises': grosses_mises[:3]
    }

    commentaire_bot = _generer_commentaire_email(stats_comment)

    # Envoyer a tous les utilisateurs
    utilisateurs = get_utilisateurs_emails()
    resultats = []

    html = email_synthese_paris(semaine_id, jokers_actifs, stats_matchs, commentaire_bot)

    for user in utilisateurs:
        success, msg = send_email(
            user['email'],
            f"Elite Pronos - Synthese des Paris (Semaine {semaine_id})",
            html
        )
        resultats.append({'user': user['pseudo'], 'success': success, 'message': msg})

    return resultats


def _generer_debrief_resultats(classement, matchs_resultats, jokers_actifs):
    """
    Genere le debrief ironique de Kingo pour l'email des resultats.
    Parle de la meilleure perf, des bons scores (3+), moque gentiment le dernier.
    """
    if not classement:
        return ""

    lignes = []
    total = len(classement)
    premier = classement[0]
    dernier = classement[-1] if total > 1 else None
    nb_matchs = len(matchs_resultats)

    # --- Le champion de la semaine ---
    phrases_premier = [
        f"Chapeau bas a <strong>@{premier['pseudo']}</strong> qui ecrase tout le monde avec <strong>{premier['points']} pts</strong> cette semaine !",
        f"<strong>@{premier['pseudo']}</strong> survole les debats avec <strong>{premier['points']} pts</strong>. On applaudit... ou on verifie ses sources.",
        f"<strong>@{premier['pseudo']}</strong> en mode extraterrestre : <strong>{premier['points']} pts</strong> ! Les autres peuvent ranger leurs boules de cristal.",
        f"Standing ovation pour <strong>@{premier['pseudo']}</strong> et ses <strong>{premier['points']} pts</strong>. Le talent... ou un pacte avec le diable ?",
    ]
    lignes.append(random.choice(phrases_premier))

    # --- Grand Chelem ---
    gc_joueurs = [j for j in classement if j.get('grand_chelem')]
    if gc_joueurs:
        noms = ", ".join(f"@{j['pseudo']}" for j in gc_joueurs)
        phrases_gc = [
            f"<br><br>🏆 <strong>GRAND CHELEM</strong> pour <strong>{noms}</strong> ! 4/4 corrects, c'est limite suspect... On verifie les cameras !",
            f"<br><br>🏆 <strong>{noms}</strong> signe un <strong>GRAND CHELEM</strong> ! Meme Nostradamus serait jaloux.",
            f"<br><br>🏆 <strong>GRAND CHELEM</strong> pour <strong>{noms}</strong> ! Le sans-faute... profitez, ca n'arrivera plus de sitot.",
        ]
        lignes.append(random.choice(phrases_gc))

    # --- Joueurs avec 3+ bons pronos ---
    bons_joueurs = [j for j in classement if j.get('bons_pronos', 0) >= 3 and not j.get('grand_chelem')]
    if bons_joueurs:
        noms = ", ".join(f"@{j['pseudo']}" for j in bons_joueurs)
        nb = len(bons_joueurs)
        if nb == 1:
            phrases_bons = [
                f"<br><br>Belle perf aussi pour <strong>{noms}</strong> avec 3 bons pronos sur {nb_matchs}. Tu commences a comprendre le football !",
                f"<br><br><strong>{noms}</strong> s'en sort bien avec 3 bons resultats. Un jour tu auras le Grand Chelem... un jour.",
            ]
        else:
            phrases_bons = [
                f"<br><br>Mention bien pour <strong>{noms}</strong> avec 3 bons pronos chacun. Pas mal, mais on attend mieux la prochaine fois !",
                f"<br><br><strong>{noms}</strong> s'en sortent avec les honneurs (3/{nb_matchs}). C'est presque bien !",
            ]
        lignes.append(random.choice(phrases_bons))

    # --- Scores exacts ---
    se_joueurs = [j for j in classement if j.get('scores_exacts', 0) > 0]
    if se_joueurs:
        for j in se_joueurs:
            phrases_se = [
                f"<br><br>🎯 <strong>@{j['pseudo']}</strong> a tape un score exact ! Precision chirurgicale ou coup de bol monumental ?",
                f"<br><br>🎯 Score exact pour <strong>@{j['pseudo']}</strong> ! Tu devrais jouer au loto tant que t'es chaud.",
                f"<br><br>🎯 <strong>@{j['pseudo']}</strong> avec le score exact ! Meme le bookmaker est impressionne.",
            ]
            lignes.append(random.choice(phrases_se))
            break  # Un seul commentaire SE suffit

    # --- Jokers ---
    for j in jokers_actifs:
        if j['type_joker'] == 'double':
            # Verifier si ca a paye
            joueur_data = next((c for c in classement if c['pseudo'] == j['pseudo']), None)
            if joueur_data and joueur_data.get('rang', 99) <= 2:
                lignes.append(f"<br><br>🃏 <strong>@{j['pseudo']}</strong> avait active le x2 et ca a paye ! Stratege de genie... ou chanceux fini ?")
            else:
                lignes.append(f"<br><br>🃏 <strong>@{j['pseudo']}</strong> avait mis le x2... Dommage, doubler un petit score ca reste petit.")
        elif j['type_joker'] == 'vol':
            lignes.append(f"<br><br>🃏 <strong>@{j['pseudo']}</strong> avait vole des pronos. Le crime a-t-il paye ? A vous de juger.")

    # --- Le dernier (reconfort + moquerie) ---
    if dernier and total > 1:
        phrases_dernier = [
            f"<br><br>Quant a <strong>@{dernier['pseudo']}</strong>... {dernier['points']} pts. Allez, c'est pas grave, on a tous des mauvaises semaines. Enfin, toi plus que les autres.",
            f"<br><br>Et pour finir, un mot pour <strong>@{dernier['pseudo']}</strong> ({dernier['points']} pts) : le foot c'est pas une science exacte, et toi t'en es la preuve vivante. Courage !",
            f"<br><br>Un petit calin virtuel pour <strong>@{dernier['pseudo']}</strong> qui ferme la marche avec {dernier['points']} pts. T'inquiete, meme les grands sont tombes... mais rarement aussi bas.",
            f"<br><br><strong>@{dernier['pseudo']}</strong>, {dernier['points']} pts... Le fond du classement te connait bien maintenant. Mais bon, quelqu'un doit bien fermer la marche. Merci pour ton sacrifice !",
        ]
        lignes.append(random.choice(phrases_dernier))

    # --- Phrase de cloture ---
    phrases_fin = [
        "<br><br>Rendez-vous la semaine prochaine, et n'oubliez pas : meme un singe avec des flechettes pourrait vous battre. Prouvez-moi le contraire !",
        "<br><br>A la semaine prochaine ! D'ici la, essayez de regarder du football au lieu de deviner au hasard.",
        "<br><br>C'est tout pour cette semaine. Pleurez un bon coup si necessaire, puis revenez plus forts. Ou pas.",
        "<br><br>Fin du debrief ! Si vous n'etes pas contents de vos resultats, c'est peut-etre le moment de changer de sport.",
    ]
    lignes.append(random.choice(phrases_fin))

    return "".join(lignes)


def envoyer_resultats_ironiques(semaine_id):
    """
    Envoie le recapitulatif des resultats avec debrief ironique de Kingo
    A appeler apres le calcul des points
    Version Supabase
    """
    from modules.supabase_db import get_supabase
    supabase = get_supabase()

    # Recuperer les matchs de la semaine avec scores
    matchs = supabase._request('GET', f'matches?semaine_id=eq.{semaine_id}&is_active=eq.true&select=id,equipe_home,equipe_away,score_final_home,score_final_away') or []
    match_ids = [m['id'] for m in matchs]
    match_map = {m['id']: m for m in matchs}

    if not match_ids:
        return []

    # Recuperer les utilisateurs actifs
    users = supabase._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo') or []
    user_map = {u['id']: u['pseudo'] for u in users}

    # Recuperer les predictions avec details
    predictions = supabase._request('GET', f'predictions?match_id=in.({",".join(map(str, match_ids))})&select=user_id,match_id,score_prono_home,score_prono_away,mise_points,points_gagnes') or []

    # Recuperer les jokers
    jokers_data = supabase._request('GET', f'jokers_historique?semaine_id=eq.{semaine_id}&select=utilisateur_id,type_joker') or []
    jokers_actifs = [{'pseudo': user_map.get(j['utilisateur_id'], 'Inconnu'), 'type_joker': j['type_joker'].lower()} for j in jokers_data]

    # Calculer les stats par joueur
    stats_joueur = {}
    for p in predictions:
        uid = p['user_id']
        match = match_map.get(p['match_id'])
        if not match or match.get('score_final_home') is None:
            continue

        if uid not in stats_joueur:
            stats_joueur[uid] = {'points': 0, 'bons_pronos': 0, 'scores_exacts': 0}

        stats_joueur[uid]['points'] += (p.get('points_gagnes') or 0)

        # Verifier 1N2 correct
        prono_res = '1' if p['score_prono_home'] > p['score_prono_away'] else ('2' if p['score_prono_home'] < p['score_prono_away'] else 'N')
        real_res = '1' if match['score_final_home'] > match['score_final_away'] else ('2' if match['score_final_home'] < match['score_final_away'] else 'N')
        if prono_res == real_res:
            stats_joueur[uid]['bons_pronos'] += 1

        # Verifier score exact
        if (p['score_prono_home'] == match['score_final_home'] and
            p['score_prono_away'] == match['score_final_away']):
            stats_joueur[uid]['scores_exacts'] += 1

    # Ajouter les joueurs sans predictions (0 pts)
    for u in users:
        if u['id'] not in stats_joueur:
            stats_joueur[u['id']] = {'points': 0, 'bons_pronos': 0, 'scores_exacts': 0}

    # Trier par points
    sorted_users = sorted(stats_joueur.items(), key=lambda x: x[1]['points'], reverse=True)
    nb_matchs = sum(1 for m in matchs if m.get('score_final_home') is not None)

    # Construire le classement
    classement = []
    for i, (uid, stats) in enumerate(sorted_users, 1):
        grand_chelem = stats['bons_pronos'] == nb_matchs and nb_matchs >= 4
        classement.append({
            'rang': i,
            'pseudo': user_map.get(uid, 'Inconnu'),
            'points': stats['points'],
            'bons_pronos': stats['bons_pronos'],
            'scores_exacts': stats['scores_exacts'],
            'grand_chelem': grand_chelem
        })

    # Matchs avec resultats pour affichage
    matchs_resultats = [m for m in matchs if m.get('score_final_home') is not None]

    # Generer le debrief ironique
    commentaire_bot = _generer_debrief_resultats(classement, matchs_resultats, jokers_actifs)

    # Envoyer a tous les utilisateurs
    utilisateurs = get_utilisateurs_emails()
    resultats = []

    html = email_resultats_ironiques(semaine_id, classement, matchs_resultats, commentaire_bot)

    for user in utilisateurs:
        success, msg = send_email(
            user['email'],
            f"Elite Pronos - Resultats Semaine {semaine_id}",
            html
        )
        resultats.append({'user': user['pseudo'], 'success': success, 'message': msg})

    return resultats


# ============================================
# EMAIL ADMIN : TABLEAU COMPLET DES PRONOS
# ============================================

def email_tableau_pronos_admin(semaine_id, matchs, joueurs_tries, pronos_par_uid, jokers_par_uid):
    """
    Email admin avec tableau identique a celui de l'accueil.
    matchs: liste de dicts {id, equipe_home, equipe_away, cote_home, cote_draw, cote_away}
    joueurs_tries: liste de tuples (uid, pseudo, rang) tries par rang
    pronos_par_uid: dict {uid: {match_id: {score, mise}}}
    jokers_par_uid: dict {uid: type_joker}
    """

    # Header avec les matchs + cotes integrees
    match_headers = ""
    for m in matchs:
        home_s = m['equipe_home'][:8]
        away_s = m['equipe_away'][:8]
        c1 = m.get('cote_home') or '-'
        cn = m.get('cote_draw') or '-'
        c2 = m.get('cote_away') or '-'
        match_headers += f'''
        <th style="padding:6px 4px; background:#D4AF37; color:#001529; font-size:10px; text-align:center; min-width:65px;">
            {home_s}<br>vs<br>{away_s}
            <div style="font-size:9px; color:#333; margin-top:2px;">{c1} | {cn} | {c2}</div>
        </th>
        '''

    # Lignes par joueur (tries par rang)
    joueur_rows = ""
    for uid, pseudo, rang in joueurs_tries:
        bg = "#001529" if rang % 2 != 0 else "#0d1b2a"

        # Rang avec medailles
        if rang == 1:
            rang_display = "&#129351;"
        elif rang == 2:
            rang_display = "&#129352;"
        elif rang == 3:
            rang_display = "&#129353;"
        else:
            rang_display = f'<span style="color:#888;">{rang}</span>'

        # Joker
        joker_type = jokers_par_uid.get(uid, '')
        if joker_type == 'double':
            joker_cell = '<span style="color:#FFD700; font-weight:bold;">&#9889;</span>'
        elif joker_type == 'vol':
            joker_cell = '<span style="color:#9b59b6; font-weight:bold;">&#127919;</span>'
        else:
            joker_cell = '<span style="color:#444;">-</span>'

        # Cellules par match
        match_cells = ""
        for m in matchs:
            prono_data = pronos_par_uid.get(uid, {}).get(m['id'])
            if prono_data:
                match_cells += f'''
                <td style="padding:6px 4px; border-bottom:1px solid #222; text-align:center; background:{bg};">
                    <span style="color:#4488FF; font-weight:bold; font-size:12px;">{prono_data['score']}</span>
                    <br><span style="color:#FFD700; font-size:10px;">{prono_data['mise']}pts</span>
                </td>
                '''
            else:
                match_cells += f'''
                <td style="padding:6px 4px; border-bottom:1px solid #222; text-align:center; background:{bg};">
                    <span style="color:#666; font-size:11px;">-</span>
                </td>
                '''

        joueur_rows += f'''
        <tr>
            <td style="padding:6px 4px; border-bottom:1px solid #222; text-align:center; background:{bg}; font-size:12px;">{rang_display}</td>
            <td style="padding:6px 6px; border-bottom:1px solid #222; background:{bg}; white-space:nowrap;">
                <span style="color:#fff; font-weight:bold; font-size:12px;">{pseudo}</span>
            </td>
            <td style="padding:6px 4px; border-bottom:1px solid #222; text-align:center; background:{bg};">{joker_cell}</td>
            {match_cells}
        </tr>
        '''

    content = f'''
    <h2>Recap des Pronostics - Semaine {semaine_id}</h2>
    <p style="color: #AAAAAA;">Tous les pronostics des joueurs apres la deadline.</p>

    <div style="overflow-x: auto;">
        <table style="width:100%; border-collapse:collapse; margin:10px 0;">
            <tr>
                <th style="padding:6px 4px; background:#D4AF37; color:#001529; font-size:10px; text-align:center; width:30px;">#</th>
                <th style="padding:6px 6px; background:#D4AF37; color:#001529; font-size:11px; text-align:left;">Pseudo</th>
                <th style="padding:6px 4px; background:#D4AF37; color:#001529; font-size:10px; text-align:center; width:30px;">&#127183;</th>
                {match_headers}
            </tr>
            {joueur_rows}
        </table>
    </div>

    <div class="highlight-box">
        <p style="color: #FFD700; margin: 0;">Que le meilleur gagne !</p>
    </div>
    '''

    return get_base_template(content, "Recap des Pronos")


def envoyer_tableau_pronos_admin(semaine_id):
    """
    Envoie le tableau complet des pronostics uniquement aux admins.
    Meme format que le tableau affiche sur l'accueil.
    A appeler apres la deadline.
    """
    from modules.supabase_db import get_supabase
    from modules.classement_st import get_classement_general_complet
    supabase = get_supabase()

    # Recuperer les matchs avec cotes
    matchs = supabase._request('GET',
        f'matches?semaine_id=eq.{semaine_id}&is_active=eq.true&select=id,equipe_home,equipe_away,cote_home,cote_draw,cote_away&order=id'
    ) or []
    match_ids = [m['id'] for m in matchs]

    if not match_ids:
        return []

    # Recuperer toutes les predictions
    predictions = supabase._request('GET',
        f'predictions?match_id=in.({",".join(map(str, match_ids))})&select=user_id,match_id,score_prono_home,score_prono_away,mise_points'
    ) or []

    # Recuperer les utilisateurs actifs
    users = supabase._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo') or []
    user_map = {u['id']: u['pseudo'] for u in users}

    # Recuperer les jokers
    jokers_data = supabase._request('GET',
        f'jokers_historique?semaine_id=eq.{semaine_id}&select=utilisateur_id,type_joker'
    ) or []
    jokers_par_uid = {j['utilisateur_id']: j['type_joker'].lower() for j in jokers_data}

    # Organiser les pronos par uid
    pronos_par_uid = {}
    for p in predictions:
        uid = p['user_id']
        if uid not in user_map:
            continue
        if uid not in pronos_par_uid:
            pronos_par_uid[uid] = {}
        mise = p.get('mise_points', 0) or 0
        pronos_par_uid[uid][p['match_id']] = {'score': f"{p['score_prono_home']}-{p['score_prono_away']}", 'mise': mise}

    # Classement general pour le rang
    classement = get_classement_general_complet()
    rang_map = {j['user_id']: j['place'] for j in classement}

    # Trier les joueurs par rang
    joueurs_tries = sorted(
        [(uid, pseudo, rang_map.get(uid, 999)) for uid, pseudo in user_map.items()],
        key=lambda x: x[2]
    )

    # Generer le HTML
    html = email_tableau_pronos_admin(semaine_id, matchs, joueurs_tries, pronos_par_uid, jokers_par_uid)

    # Envoyer uniquement aux admins
    admins = supabase._request('GET', 'utilisateurs?is_admin=eq.true&select=id,pseudo,email') or []

    resultats = []
    for admin in admins:
        if not admin.get('email'):
            continue
        success, msg = send_email(
            admin['email'],
            f"Elite Pronos - Recap Pronos Semaine {semaine_id}",
            html
        )
        resultats.append({'user': admin['pseudo'], 'success': success, 'message': msg})

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
