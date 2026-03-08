"""
Module Notifier pour Elite Pronos
Gestion des emails automatises via SMTP
Design Elite: Bleu Nuit & Dore
"""
import smtplib
import os
import re
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


def _is_valid_email(email):
    """Verifie le format d'une adresse email"""
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def send_email(destinataire, sujet, html_content):
    """
    Envoie un email via SMTP
    Retourne (success, message)
    """
    # Validation du format email
    if not destinataire or not _is_valid_email(destinataire):
        return False, f"Adresse email invalide: {destinataire}"

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
        "Tu brilles tellement que les autres portent des lunettes de soleil pour lire le classement.",
        "Premier ! Ne t'habitue pas, la chute est proportionnelle a l'altitude.",
        "On devrait renommer le trophee en ton nom... puis te le retirer la semaine prochaine.",
        "Messi, Ronaldo, et maintenant toi. L'un de ces trois n'a rien a faire dans la liste.",
    ],
    'dernier': [
        "Au moins, tu es constant dans la mediocrite !",
        "Tu devrais peut-etre essayer les echecs a la place ?",
        "Ton joker aurait ete plus utile que tes pronostics...",
        "Meme un singe avec des flechettes aurait fait mieux !",
        "Le fond du classement te dit merci pour ta fidelite.",
        "Tu collectionnes les defaites comme d'autres les timbres.",
        "On a tous un talent cache. Le tien c'est de finir dernier avec une regularite impressionnante.",
        "Tu es la preuve vivante que la passion ne suffit pas. Il faut aussi un cerveau.",
        "Le pire c'est que t'as VRAIMENT essaye. Imagine si t'avais pas essaye.",
        "Si on donnait des points pour la perseverance dans l'echec, tu serais premier.",
    ],
    'progresse': [
        "Tiens, tu as enfin trouve comment marche le foot ?",
        "Belle remontee ! Tu lisais des tutos sur YouTube ?",
        "Miracle ! Il y a de l'espoir pour toi finalement.",
        "Tu as change de lunettes ou quoi ?",
        "Enfin reveille ! On commencait a s'inquieter.",
        "Progression detectee ! Je repete : ce n'est PAS un exercice.",
        "Tu montes ! Bon, tu partais de tres tres bas, mais quand meme.",
        "Quelqu'un a enfin compris qu'il y avait 2 equipes dans un match. Bravo.",
    ],
    'regresse': [
        "La chute est rude ! Tu etais en vacances mentales ?",
        "De heros a zero en une semaine, chapeau !",
        "Retour sur Terre brutal... ca fait mal ?",
        "Tu redescends aussi vite que tu es monte.",
        "L'ascenseur etait en panne ? Tu as pris l'escalier... vers le bas.",
        "Icare aussi volait haut avant de se crasher. Tu as des ailes en cire toi aussi ?",
        "Tu regressas si vite que meme mon processeur n'a pas eu le temps de calculer.",
        "Dechéance royale. Shakespeare aurait pas ecrit mieux.",
    ],
    'stable': [
        "Stable comme un diesel... qui ne demarre pas.",
        "Ni bon ni mauvais, juste... la.",
        "La regularite dans la mediocrite, c'est presque un talent.",
        "Tu fais du surplace, mais au moins tu ne recules pas.",
        "Comme un meuble : present mais pas remarque.",
        "Tu es le beige du classement. Ni chaud, ni froid. Juste... tiede.",
        "Stable. Previsible. Ennuyeux. Mais present, c'est deja ca.",
        "On t'appelle Monsieur Moyenne. C'est pas un compliment.",
    ],
    'grand_chelem': [
        "4/4 ! Tu as vendu ton ame au diable ou tu savais vraiment ?",
        "GRAND CHELEM ! Meme Nostradamus est jaloux !",
        "Perfection ! C'est louche... on verifie les cameras.",
        "4 sur 4 ! Tu as des informateurs dans les vestiaires ?",
        "Le sans-faute ! Profite, ca n'arrivera plus avant longtemps.",
        "Grand Chelem ! Ta boule de cristal fonctionne encore ?",
        "LEGENDAIRE ! On devrait t'appeler Madame Irma.",
        "4/4 ! La probabilite etait de 1 sur 81. Tu as battu les maths. Respect.",
        "Grand Chelem ! Je lance une enquete interne. Personne n'est aussi bon sans tricher.",
        "Le sans-faute absolu. Meme moi, le bot omniscient, je suis impressionne. Et un peu vexe.",
    ],
    'score_exact': [
        "Score exact ! Tu as un don ou c'est de la triche ?",
        "Dans le mille ! Meme le bookmaker est impressionne.",
        "Score parfait ! Tu as soudoye l'arbitre ?",
        "Precision chirurgicale ! On t'engage comme consultant.",
        "Score exact ! La chance sourit aux audacieux... ou aux tricheurs.",
        "Bullseye ! Tu devrais jouer aux flechettes aussi.",
        "Score exact ! Tu as un abonnement premium a l'avenir ou quoi ?",
        "Tes pronos sont tellement precis que la NASA veut t'embaucher pour calculer des trajectoires.",
        "Score exact ! Dis-moi, tu as un cousin arbitre ? Un oncle commentateur ? Un chat voyant ?",
    ],
    'joker_vole_reussi': [
        "Ton vol a paye ! Le crime parfait existe donc.",
        "Braquage reussi ! Ta victime doit s'en mordre les doigts.",
        "Points voles avec succes ! Tel un pickpocket de genie.",
        "Le casse du siecle ! Ocean's Eleven peut aller se rhabiller.",
        "Vol qualifie et assume ! Pas de remords, que des points.",
        "Tu as vole ses pronos ET sa dignite. Bien joue !",
        "Arsene Lupin applaudit depuis sa tombe. Le gentleman cambrioleur du prono.",
        "Vol reussi ! Ta victime est en PLS et toi tu sirotes un cocktail au sommet du classement.",
    ],
    'joker_vole_rate': [
        "Tu as vole les pronos d'un nul... Bien joue, genie !",
        "Bravo, tu as copie sur le plus mauvais de la classe !",
        "Vol rate ! Tu aurais du choisir une meilleure cible...",
        "Felicitations, tu as herite des pires pronos. Karma ?",
        "Comme voler une voiture en panne... Quelle strategie !",
        "Tu as vole a l'aveugle et tu es tombe sur un borgne.",
        "Le voleur vole ! La cible etait encore plus nulle que toi.",
        "Tu as braque une banque... qui etait deja en faillite. Magnifique strategie.",
        "Vol catastrophique. Tu as pris ses pronos ET ses problemes. Double peine.",
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
        "Lanterne rouge a vie. On va bientot renommer la derniere place en ton honneur.",
        "Meme le plancher a peur que tu passes a travers. C'est dire.",
    ],
    'oubli_prono': [
        "Oubli de pronos ! Le systeme t'a attribue ceux du dernier. Malin !",
        "Pas de pronos ? Felicitations, tu herites des pires predictions !",
        "Tu as oublie de jouer... Le Bot a joue pour toi. Spoiler : c'est pas fou.",
        "Absence injustifiee ! Tu as les pronos du bonnet d'ane maintenant.",
        "Oups ! Oubli de deadline = cadeau empoisonne automatique.",
        "Le reveil n'a pas sonne ? Pas grave, le dernier du classement t'a prete ses pronos.",
        "Memoire de poisson rouge ! Le systeme t'a mis d'office les pires pronos.",
        "Tu as oublie tes pronos. Le systeme ne t'a pas oublie, lui. -1 joker. Bonne journee.",
        "Absent sans excuse ! Le tribunal du prono t'a condamne a mes predictions. La peine maximale.",
        "L'oubli est humain. Mais repete chaque semaine, ca devient un talent.",
    ],
    'holdup': [
        "HOLD-UP ! Tu as braque la banque des pronos !",
        "Le casse du siecle ! Ta victime ne s'en remettra pas.",
        "Braquage en regle ! Ocean's Eleven peut aller se rhabiller.",
        "Hold-up reussi ! Le crime parfait, ca existe.",
        "Tu as cambriole les pronos comme un pro. Respect... ou pas.",
        "HOLD-UP MAGISTRAL ! La cible n'a rien vu venir.",
        "Braquage de haute voltige ! La police du prono est depassee.",
        "Tu as vole le match et le show. Standing ovation du gang des pronostiqueurs.",
    ],
    'joker_double_gagnant': [
        "Joker x2 au bon moment ! Tu as double la mise et le butin !",
        "Points doubles actives et ca paye ! Stratege ou chanceux ?",
        "Le x2 etait parfait ! Tu as fait sauter la banque.",
        "Joker double bien place ! Les autres peuvent pleurer.",
        "Multiplication des points ! Ta semaine est en or.",
        "x2 gagnant ! Warren Buffett du pronostic. L'investissement du siecle.",
        "Tu as double tes points comme on double la mise au casino. Sauf que toi, tu as gagne.",
    ],
    'joker_double_perdant': [
        "Joker x2 sur une semaine pourrie... Double peine !",
        "Tu as double... tes echecs. Bravo champion !",
        "Le x2 sur une catastrophe, c'etait vraiment l'idee du siecle ?",
        "Points doubles sur zero points = toujours zero. Les maths, c'est cruel.",
        "Joker gaspille ! Tu aurais du le garder pour une bonne semaine.",
        "Tu as joue ton x2 comme on joue au loto : avec beaucoup d'espoir et zero resultat.",
        "Doubler ses pertes, fallait oser. Toi tu l'as fait. Avec panache.",
        "Le x2 sur une semaine catastrophique, c'est comme mettre de l'essence sur un feu. Bravo l'artiste.",
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
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/" class="button">Se connecter</a>
    </p>

    <p><strong>Rappel des regles :</strong></p>
    <ul style="color: #cccccc;">
        <li>4 matchs a pronostiquer chaque semaine</li>
        <li>100 points de budget a repartir</li>
        <li>2 jokers a utiliser strategiquement</li>
        <li>Grand Chelem (4/4 corrects) : +40 pts de budget la semaine suivante</li>
    </ul>

    <p>Que la meilleure strategie gagne !</p>
    '''

    return get_base_template(content, "Nouvelle Saison")


def email_prospection(lien_inscription="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/"):
    """Email de prospection/lancement pour inviter de nouveaux joueurs"""

    # --- Bloc Tendances (barres colorees imitant l'app) ---
    tendances_html = '''
    <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #FFD700; margin: 0 0 4px 0; font-size: 15px;">📊 Tendances des Pronos</h3>
        <p style="color: #666; font-size: 11px; margin: 0 0 14px 0;">Repartition 1 / N / 2 par match</p>

        <!-- Match 1 -->
        <div style="margin: 10px 0; padding: 12px; background: #1a1a2e; border-radius: 8px;">
            <div style="color: #ccc; font-size: 12px; margin-bottom: 7px;">RC Strasbourg Alsace vs Racing Club de Lens</div>
            <div style="display: flex; height: 22px; border-radius: 4px; overflow: hidden; background: #333;">
                <div style="width: 100%; background: linear-gradient(135deg, #27ae60, #2ecc71); display: flex; align-items: center; justify-content: center;">
                    <span style="color: #fff; font-size: 11px; font-weight: bold;">100%</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 10px; color: #666;">
                <span>🏠 Dom</span><span>🤝 Nul</span><span>✈️ Ext</span>
            </div>
        </div>

        <!-- Match 2 -->
        <div style="margin: 10px 0; padding: 12px; background: #1a1a2e; border-radius: 8px;">
            <div style="color: #ccc; font-size: 12px; margin-bottom: 7px;">Stade Rennais FC 1901 vs Toulouse FC</div>
            <div style="display: flex; height: 22px; border-radius: 4px; overflow: hidden; background: #333;">
                <div style="width: 100%; background: linear-gradient(135deg, #27ae60, #2ecc71); display: flex; align-items: center; justify-content: center;">
                    <span style="color: #fff; font-size: 11px; font-weight: bold;">100%</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 10px; color: #666;">
                <span>🏠 Dom</span><span>🤝 Nul</span><span>✈️ Ext</span>
            </div>
        </div>

        <!-- Match 3 -->
        <div style="margin: 10px 0; padding: 12px; background: #1a1a2e; border-radius: 8px;">
            <div style="color: #ccc; font-size: 12px; margin-bottom: 7px;">Olympique de Marseille vs Olympique Lyonnais</div>
            <div style="display: flex; height: 22px; border-radius: 4px; overflow: hidden; background: #333;">
                <div style="width: 67%; background: linear-gradient(135deg, #27ae60, #2ecc71); display: flex; align-items: center; justify-content: center;">
                    <span style="color: #fff; font-size: 11px; font-weight: bold;">67%</span>
                </div>
                <div style="width: 33%; background: linear-gradient(135deg, #7f8c8d, #95a5a6); display: flex; align-items: center; justify-content: center;">
                    <span style="color: #fff; font-size: 11px; font-weight: bold;">33%</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 10px; color: #666;">
                <span>🏠 Dom</span><span>🤝 Nul</span><span>✈️ Ext</span>
            </div>
        </div>

        <!-- Match 4 -->
        <div style="margin: 10px 0; padding: 12px; background: #1a1a2e; border-radius: 8px;">
            <div style="color: #ccc; font-size: 12px; margin-bottom: 7px;">AS Roma vs Juventus FC</div>
            <div style="display: flex; height: 22px; border-radius: 4px; overflow: hidden; background: #333;">
                <div style="width: 100%; background: linear-gradient(135deg, #27ae60, #2ecc71); display: flex; align-items: center; justify-content: center;">
                    <span style="color: #fff; font-size: 11px; font-weight: bold;">100%</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 10px; color: #666;">
                <span>🏠 Dom</span><span>🤝 Nul</span><span>✈️ Ext</span>
            </div>
        </div>
    </div>
    '''

    # --- Bloc Recap des paris (tableau rivaux) ---
    recap_html = '''
    <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0; overflow-x: auto;">
        <h3 style="color: #FFD700; margin: 0 0 12px 0; font-size: 15px;">🕵️ Recap des Paris — les mises de vos rivaux</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <thead>
                <tr style="background: linear-gradient(135deg, #D4AF37, #B8960C);">
                    <th style="padding: 8px 6px; color: #001a35; text-align: left; border-radius: 4px 0 0 0;">#</th>
                    <th style="padding: 8px 6px; color: #001a35; text-align: left;">Pseudo</th>
                    <th style="padding: 8px 6px; color: #001a35; text-align: center;">🃏</th>
                    <th style="padding: 8px 6px; color: #001a35; text-align: center;">Strasbourg<br>vs Lens</th>
                    <th style="padding: 8px 6px; color: #001a35; text-align: center;">Rennes<br>vs Toulouse</th>
                    <th style="padding: 8px 6px; color: #001a35; text-align: center;">OM<br>vs OL</th>
                    <th style="padding: 8px 6px; color: #001a35; text-align: center; border-radius: 0 4px 0 0;">Roma<br>vs Juve</th>
                </tr>
            </thead>
            <tbody>
                <tr style="background: #002040;">
                    <td style="padding: 7px 6px; color: #FFD700; font-weight: bold;">1</td>
                    <td style="padding: 7px 6px; color: #fff; font-weight: bold;">baggio</td>
                    <td style="padding: 7px 6px; text-align: center; color: #FFD700;">x2</td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">2-0<br><span style="color: #e74c3c; font-size: 10px;">(30)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">1-0<br><span style="color: #e74c3c; font-size: 10px;">(25)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">2-1<br><span style="color: #e74c3c; font-size: 10px;">(30)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">1-0<br><span style="color: #e74c3c; font-size: 10px;">(15)</span></td>
                </tr>
                <tr style="background: #001a35;">
                    <td style="padding: 7px 6px; color: #aaa;">2</td>
                    <td style="padding: 7px 6px; color: #ccc;">jey</td>
                    <td style="padding: 7px 6px; text-align: center; color: #666;">—</td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">1-1<br><span style="color: #e74c3c; font-size: 10px;">(20)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">2-0<br><span style="color: #e74c3c; font-size: 10px;">(35)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">1-0<br><span style="color: #e74c3c; font-size: 10px;">(25)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">0-1<br><span style="color: #e74c3c; font-size: 10px;">(20)</span></td>
                </tr>
                <tr style="background: #002040;">
                    <td style="padding: 7px 6px; color: #aaa;">3</td>
                    <td style="padding: 7px 6px; color: #ccc;">jbdb</td>
                    <td style="padding: 7px 6px; text-align: center; color: #9b59b6;">🎭</td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">3-1<br><span style="color: #e74c3c; font-size: 10px;">(15)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">1-0<br><span style="color: #e74c3c; font-size: 10px;">(40)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">2-0<br><span style="color: #e74c3c; font-size: 10px;">(20)</span></td>
                    <td style="padding: 7px 6px; text-align: center; color: #ccc;">1-1<br><span style="color: #e74c3c; font-size: 10px;">(25)</span></td>
                </tr>
                <tr style="background: #001a35;">
                    <td style="padding: 7px 6px; color: #aaa;">?</td>
                    <td style="padding: 7px 6px; color: #FFD700; font-style: italic;">Vous ?</td>
                    <td style="padding: 7px 6px; text-align: center; color: #666;">—</td>
                    <td colspan="4" style="padding: 7px 6px; text-align: center; color: #888; font-style: italic;">Inscrivez-vous pour jouer !</td>
                </tr>
            </tbody>
        </table>
    </div>
    '''

    # --- Bloc Classement general ---
    classement_html = '''
    <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #FFD700; margin: 0 0 12px 0; font-size: 15px;">🏆 Classement General</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead>
                <tr style="background: linear-gradient(135deg, #D4AF37, #B8960C);">
                    <th style="padding: 8px 10px; color: #001a35; text-align: left;">Rang</th>
                    <th style="padding: 8px 10px; color: #001a35; text-align: left;">Pseudo</th>
                    <th style="padding: 8px 10px; color: #001a35; text-align: right;">Points</th>
                    <th style="padding: 8px 10px; color: #001a35; text-align: center;">Bons</th>
                    <th style="padding: 8px 10px; color: #001a35; text-align: center;">Exacts</th>
                </tr>
            </thead>
            <tbody>
                <tr style="background: #002040;">
                    <td style="padding: 9px 10px; color: #FFD700; font-size: 16px;">🥇</td>
                    <td style="padding: 9px 10px; color: #FFD700; font-weight: bold;">baggio</td>
                    <td style="padding: 9px 10px; color: #FFD700; font-weight: bold; text-align: right;">1135.5</td>
                    <td style="padding: 9px 10px; color: #ccc; text-align: center;">13</td>
                    <td style="padding: 9px 10px; color: #ccc; text-align: center;">2</td>
                </tr>
                <tr style="background: #001a35;">
                    <td style="padding: 9px 10px; color: #C0C0C0; font-size: 16px;">🥈</td>
                    <td style="padding: 9px 10px; color: #ccc; font-weight: bold;">jey</td>
                    <td style="padding: 9px 10px; color: #ccc; font-weight: bold; text-align: right;">774.1</td>
                    <td style="padding: 9px 10px; color: #ccc; text-align: center;">10</td>
                    <td style="padding: 9px 10px; color: #ccc; text-align: center;">0</td>
                </tr>
                <tr style="background: #002040;">
                    <td style="padding: 9px 10px; color: #CD7F32; font-size: 16px;">🥉</td>
                    <td style="padding: 9px 10px; color: #ccc; font-weight: bold;">jbdb</td>
                    <td style="padding: 9px 10px; color: #ccc; font-weight: bold; text-align: right;">592.0</td>
                    <td style="padding: 9px 10px; color: #ccc; text-align: center;">12</td>
                    <td style="padding: 9px 10px; color: #ccc; text-align: center;">1</td>
                </tr>
                <tr style="background: #001a35; border-top: 1px dashed #444;">
                    <td style="padding: 9px 10px; color: #888; font-size: 13px;">?</td>
                    <td style="padding: 9px 10px; color: #FFD700; font-style: italic;">Vous ?</td>
                    <td colspan="3" style="padding: 9px 10px; color: #888; font-style: italic; text-align: center;">Votre place vous attend</td>
                </tr>
            </tbody>
        </table>
    </div>
    '''

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

    {tendances_html}

    {recap_html}

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

    {classement_html}

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
        <p style="font-size: 2em; font-weight: 900; color: #FFD700; text-align: center; margin: 10px 0 5px 0;">50 &euro;</p>
        <ul style="color: #ffffff; font-size: 1em; list-style: none; padding: 0; text-align: center;">
            <li style="margin: 5px 0; color: #AAAAAA;">dont 5 &euro; frais techniques et maintenance &mdash; 45 &euro; reverses en cagnotte</li>
        </ul>
        <p style="color: #AAAAAA; margin-top: 10px; font-size: 0.9em;">
            <strong style="color: #FFD700;">Modes de paiement acceptes :</strong>
            Cheque &bull; Virement bancaire &bull; Especes &bull; Crypto-monnaie
        </p>
        <p style="color: #00FF00; margin-top: 15px; padding-top: 15px; border-top: 1px solid #333;">
            Votre compte sera active par <strong>Baggio</strong> des reception de votre reglement.
        </p>
    </div>

    <!-- REPARTITION DES RECOMPENSES -->
    <div style="background: #f9f6e8; border: 2px solid #B8860B; border-radius: 10px; padding: 20px; margin: 25px 0;">
        <h3 style="color: #B8860B; margin-top: 0;">Repartition des Recompenses</h3>
        <p style="color: #555555; font-style: italic;">Cagnotte nette = nombre de joueurs x 45 euros, apres deduction des prix fixes.</p>

        <p style="color: #333333; margin-top: 15px;"><strong>Prix Fixes (preleves en premier) :</strong></p>
        <ul style="color: #333333; margin-left: 20px;">
            <li style="margin: 8px 0;"><strong>Meilleur score d'une journee :</strong> 50 euros</li>
            <li style="margin: 8px 0;"><strong>Plus de paris reussis sur la saison :</strong> 25 euros</li>
        </ul>

        <!-- TOP 3 -->
        <p style="color: #B8860B; margin-top: 20px;"><strong>Jusqu'a 20 joueurs - 3 joueurs recompenses</strong></p>
        <p style="color: #333333; margin: 8px 0 0 15px; line-height: 2.2;">
            1er place : <strong style="font-size: 1.05em;">50%</strong><br>
            2e place : <strong style="font-size: 1.05em;">30%</strong><br>
            3e place : <strong style="font-size: 1.05em;">20%</strong>
        </p>

        <!-- TOP 5 -->
        <p style="color: #B8860B; margin-top: 20px;"><strong>De 21 a 40 joueurs - 5 joueurs recompenses</strong></p>
        <p style="color: #333333; margin: 8px 0 0 15px; line-height: 2.2;">
            1er place : <strong style="font-size: 1.05em;">le reste de la cagnotte</strong><br>
            2e place : <strong style="font-size: 1.05em;">25%</strong><br>
            3e place : <strong style="font-size: 1.05em;">20%</strong><br>
            4e place : <strong style="font-size: 1.05em;">10%</strong><br>
            5e place : <strong style="font-size: 1.05em;">50 euros garantis</strong>
        </p>

        <!-- TOP 7 -->
        <p style="color: #B8860B; margin-top: 20px;"><strong>41 joueurs et plus - 7 joueurs recompenses</strong></p>
        <p style="color: #333333; margin: 8px 0 0 15px; line-height: 2.2;">
            1er place : <strong style="font-size: 1.05em;">le reste de la cagnotte</strong><br>
            2e place : <strong style="font-size: 1.05em;">20%</strong><br>
            3e place : <strong style="font-size: 1.05em;">15%</strong><br>
            4e place : <strong style="font-size: 1.05em;">12%</strong><br>
            5e place : <strong style="font-size: 1.05em;">9%</strong><br>
            6e place : <strong style="font-size: 1.05em;">6%</strong><br>
            7e place : <strong style="font-size: 1.05em;">50 euros garantis</strong>
        </p>

        <p style="color: #555555; font-size: 0.95em; margin-top: 20px; padding-top: 15px; border-top: 1px solid #cccccc;">
            Le versement de vos gains s'effectuera <strong style="color: #B8860B;">15 jours</strong> apres le coup de sifflet final du championnat.
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
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 2 - Kingo, le Pronostiqueur Officiel</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                <strong style="color: #FFD700;">Kingo</strong> est le pronostiqueur officiel et l'intelligence du club Elite Pronos.
                Veritable expert du ballon rond, il analyse chaque semaine les cotes, les statistiques et les confrontations
                pour etablir ses pronostics.<br><br>
                <strong>Son role au sein du club :</strong><br><br>
                &#x2022; <strong>Pronostics de reference :</strong> Kingo est le seul membre du club a pronostiquer
                sur tous les matchs chaque semaine, sans exception. Ses predictions servent de reference collective.<br><br>
                &#x2022; <strong>Filet de securite :</strong> tout membre qui oublie de soumettre ses pronostics avant la
                deadline se voit automatiquement attribuer les pronostics de Kingo pour la semaine en cours.
                Ce n'est pas un avantage &mdash; c'est une penalite deguisee !<br><br>
                &#x2022; <strong>Voix du club :</strong> Kingo commente chaque journee, anime la page d'accueil, analyse
                les performances et tient la chronique des exploits (et des catastrophes) de chaque joueur.<br><br>
                &#x2022; <strong>Classement :</strong> Kingo figure au classement general a titre indicatif uniquement.
                Il ne peut ni gagner ni percevoir de recompenses.<br><br>
                <span style="color: #FFD700; font-style: italic;">Battre Kingo chaque semaine devient vite un objectif en soi !</span>
            </p>
        </div>

        <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 3 - Pronostics Hebdomadaires</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                4 matchs par semaine. Budget de 100 points a repartir (mise min. 10 pts, max. 60 pts par match).
                Deadline : 1h avant le premier match.<br>
                <strong>Defaut de pronostic :</strong> les pronostics de <strong style="color: #FFD700;">Kingo</strong> sont attribues automatiquement.
            </p>
        </div>

        <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 4 - Systeme de Points</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                <strong>Formule :</strong> Points = Mise x Cote (si 1N2 correct).<br>
                <strong>Bonus score exact :</strong> +10 points fixes.<br>
                <strong>Grand Chelem (4/4 corrects) :</strong> +40 points appliques la semaine suivante.
            </p>
        </div>

        <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 5 - Les Jokers</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                Chaque joueur dispose de <strong>3 Jokers Points Doubles</strong> et <strong>2 Jokers Points Voles</strong> par saison.<br><br>
                <strong>Points Doubles :</strong> x2 sur tous les gains de la semaine.<br>
                <strong>Points Voles :</strong> Copie les pronostics d'un adversaire choisi.<br><br>
                Activation avant la deadline, non annulable. Jokers non utilises perdus en fin de saison.
            </p>
        </div>

        <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #333;">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 6 - Defis Hebdomadaires</h4>
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                Chaque semaine, 3 defis sont proposes. Reussir les <strong>3 defis dans la meme semaine</strong> rapporte
                <strong style="color: #9b59b6;">+1 Joker Points Voles</strong> bonus :<br><br>
                <strong style="color: #FFD700;">Defi 1 &mdash; Score de feu :</strong> Marquer 200 points ou plus dans la semaine.<br>
                <strong style="color: #FFD700;">Defi 2 &mdash; Sniper :</strong> Reussir au moins 2 scores exacts dans la semaine.<br>
                <strong style="color: #FFD700;">Defi 3 &mdash; Audacieux :</strong> Remporter un pari avec une mise d'au moins 40 points.<br><br>
                <span style="color: #AAAAAA; font-style: italic;">Les 3 defis doivent etre accomplis la meme semaine. Une seule recompense par joueur par semaine.</span>
            </p>
        </div>

        <div>
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">Article 7 - Classement et Recompenses</h4>
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
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/" class="button">Se connecter</a>
    </p>

    <p style="color: #FFD700; font-weight: bold; text-align: right; margin-top: 30px;">
        L'Admin Elite Pronos
    </p>
    '''

    return get_base_template(content, "Bienvenue dans le Club")


def _analyser_match_kingo(home, away, cote_h, cote_n, cote_a):
    """Kingo analyse un match et explique pourquoi il est interessant.
    Retourne un commentaire base sur les cotes et les equipes."""
    import random

    try:
        ch = float(cote_h) if cote_h and cote_h != '-' else 2.0
        cn = float(cote_n) if cote_n and cote_n != '-' else 3.0
        ca = float(cote_a) if cote_a and cote_a != '-' else 2.0
    except (ValueError, TypeError):
        ch, cn, ca = 2.0, 3.0, 2.0

    ecart = abs(ch - ca)
    favori = home if ch < ca else away
    outsider = away if ch < ca else home
    cote_favori = min(ch, ca)

    # === DERBY / CLASSIQUE ===
    DERBYS = {
        ('paris saint-germain fc', 'olympique de marseille'): "Le Classique ! PSG-OM, la guerre des ego. Tout le monde a un avis, personne n'a raison.",
        ('olympique de marseille', 'paris saint-germain fc'): "OM-PSG au Velodrome ! L'ambiance va etre electrique et les pronostics impossibles.",
        ('olympique lyonnais', 'as saint-etienne'): "Le Derby ! OL-ASSE, la haine cordiale du Rhone. Les cotes mentent forcement.",
        ('as saint-etienne', 'olympique lyonnais'): "ASSE-OL, le Chaudron va bruler. Quand c'est le derby, les cotes ne veulent plus rien dire.",
        ('rc lens', 'losc lille'): "Le Derby du Nord ! Lens-Lille, passion et intensite. Un match ou tout peut basculer.",
        ('losc lille', 'rc lens'): "Lille-Lens ! Le Nord va trembler. Les bookmakers n'ont jamais compris ce derby.",
        ('ogc nice', 'as monaco fc'): "Le Derby de la Cote d'Azur ! Nice-Monaco, soleil et tension. Un piege a pronostics.",
        ('as monaco fc', 'ogc nice'): "Monaco-Nice, la Riviera s'enflamme. Attention aux surprises.",
        ('stade rennais fc 1901', 'fc nantes'): "Le Derby breton ! Rennes-Nantes. La Bretagne contre la Loire, ca ne pardonne pas.",
        ('fc nantes', 'stade rennais fc 1901'): "Nantes-Rennes ! Le derby de l'Ouest. Rien n'est jamais acquis dans cette rivalite.",
        ('olympique lyonnais', 'olympique de marseille'): "OL-OM ! Le choc des Olympiques. Un classique qui fait toujours des degats dans les classements.",
        ('olympique de marseille', 'olympique lyonnais'): "OM-OL au Velodrome ! Deux institutions, un seul vainqueur. Kingo adore ce genre de piege.",
        # Chocs europeens
        ('fc barcelona', 'real madrid cf'): "EL CLASICO ! Barca-Real. Le match le plus regarde de la planete. Et le plus impredictible.",
        ('real madrid cf', 'fc barcelona'): "Real-Barca au Bernabeu ! Le Clasico, rien de moins. Bon courage pour vos pronos.",
        ('manchester united fc', 'liverpool fc'): "Man United-Liverpool ! Le choc de l'Angleterre. La Premier League dans toute sa splendeur.",
        ('liverpool fc', 'manchester united fc'): "Liverpool-United ! Anfield va rugir. Les cotes ne veulent rien dire ici.",
        ('arsenal fc', 'tottenham hotspur fc'): "Le North London Derby ! Arsenal-Tottenham. La rivalite la plus feroce de Londres.",
        ('tottenham hotspur fc', 'arsenal fc'): "Tottenham-Arsenal ! Le derby de Londres. Les pronostics vont voler en eclats.",
        ('ac milan', 'fc internazionale milano'): "Le Derby della Madonnina ! Milan-Inter, San Siro va exploser.",
        ('fc internazionale milano', 'ac milan'): "Inter-Milan ! Le Derby de Milan. Kingo tremble d'excitation.",
        ('juventus fc', 'ssc napoli'): "Juve-Napoli ! Le choc du Calcio. Nord contre Sud, toujours explosif.",
        ('ssc napoli', 'juventus fc'): "Napoli-Juve ! Le Maradona va s'enflammer. Un match qui defie la logique.",
        ('fc bayern münchen', 'borussia dortmund'): "Der Klassiker ! Bayern-Dortmund. Le choc absolu du foot allemand.",
        ('borussia dortmund', 'fc bayern münchen'): "Dortmund-Bayern ! Le Mur Jaune contre la machine bavaroise.",
        ('atlético de madrid', 'real madrid cf'): "Le Derby de Madrid ! Atletico-Real. Simeone contre le Real, c'est toujours electrique.",
        ('real madrid cf', 'atlético de madrid'): "Real-Atletico ! Le derby madrilene. Deux philosophies, un seul survivant.",
    }

    key = (home.lower(), away.lower())
    if key in DERBYS:
        return DERBYS[key]

    # === GROS FAVORI (ecart > 1.5) ===
    PHRASES_GROS_FAVORI = [
        f"Les bookmakers voient {favori} ecraser {outsider}. Trop facile ? C'est la que le piege se referme.",
        f"{favori} est ultra-favori a {cote_favori}. Mais Kingo sait que les certitudes, c'est fait pour etre detruites.",
        f"Sur le papier, {outsider} n'a aucune chance. Mais le papier, ca ne joue pas au foot.",
        f"{favori} favori ecrasant ? Attention, les upsets font les legendes... et les -20 pts aussi.",
        f"Cote a {cote_favori} pour {favori}. Facile ? C'est exactement ce que pensaient ceux qui ont fini derniers.",
        f"{outsider} donne perdant par tout le monde. Tout le monde sauf Kingo, qui voit le piege.",
        f"Match desequilibre sur le papier. Miser gros sur {favori} ? Kingo ricane d'avance.",
        f"{favori} enorme favori. Le genre de match qui transforme les certitudes en cauchemars.",
    ]

    # === MATCH SERRE (ecart < 0.3) ===
    PHRASES_MATCH_SERRE = [
        f"50/50 entre {home} et {away}. Le genre de match qui separe les vrais pronostiqueurs des touristes.",
        f"{home}-{away} : impossible a departager. Les cotes sont identiques, les avis aussi. Pile ou face ?",
        f"Match ultra-serre ! {home} et {away} au coude a coude. C'est ici que les champions se revelent.",
        f"Les bookmakers n'arrivent pas a departager {home} et {away}. Kingo adore ce genre de casse-tete.",
        f"{home} vs {away} : l'incertitude totale. C'est le match qui va faire la difference au classement.",
        f"Quasi-egalite dans les cotes ! {home}-{away} c'est le match piege par excellence.",
        f"Les cotes sont presque identiques. Ce match va faire exploser les certitudes de tout le monde.",
        f"{home}-{away}, personne ne sait. Et c'est justement pour ca que Kingo a choisi ce match.",
    ]

    # === NUL PROBABLE (cote nul < 3.0) ===
    PHRASES_NUL_PROBABLE = [
        f"Attention au nul ! {home}-{away}, les cotes sentent le 0-0 ou le 1-1 a plein nez.",
        f"Le nul rode a {cn}. {home}-{away}, le genre de match ou ceux qui osent le nul peuvent tout rafler.",
        f"Kingo flaire le nul dans {home}-{away}. Mais qui aura le courage de miser dessus ?",
        f"{home}-{away} : le nul est tentant a {cn}. Le genre de pari qui separe les audacieux des moutons.",
    ]

    # === LEGER FAVORI (ecart entre 0.3 et 1.0) ===
    PHRASES_LEGER_FAVORI = [
        f"{favori} leger favori mais {outsider} peut creer la surprise. Le genre de match qui rend fou.",
        f"Avantage {favori}, mais rien n'est joue. {outsider} a les armes pour renverser la table.",
        f"{favori} devant dans les cotes mais pas de quoi pavoiser. {outsider} est capable du meilleur comme du pire.",
        f"Les cotes penchent vers {favori}. Mais Kingo sait que le foot se joue sur le terrain, pas sur les probabilites.",
        f"{favori} favori sur le papier. Mais {outsider} n'a rien a perdre, et c'est ca le danger.",
        f"Leger avantage {favori}. Le genre de match ou la mise fait toute la difference.",
        f"{home}-{away} : un match equilibre avec un petit avantage {favori}. La cle ? La gestion de la mise.",
        f"Match ouvert entre {home} et {away}. {favori} part devant mais tout peut arriver.",
    ]

    # === COTE ELEVEE OUTSIDER (cote > 4.5) ===
    PHRASES_OUTSIDER = [
        f"{outsider} a {max(ch, ca)} ! Un pari fou qui peut rapporter gros. Mais qui osera ?",
        f"Personne ne croit en {outsider}. Et si c'etait justement le bon moment d'y croire ?",
        f"{outsider} donne a {max(ch, ca)}. Le genre de coup qui fait basculer un classement entier.",
        f"Les cotes de {outsider} font rever les audacieux. Kingo dit : qui ne tente rien n'a rien.",
    ]

    # Selection selon le profil du match
    if ecart > 1.5:
        phrases = PHRASES_GROS_FAVORI
        if max(ch, ca) > 4.5:
            phrases = phrases + PHRASES_OUTSIDER
    elif ecart < 0.3:
        phrases = PHRASES_MATCH_SERRE
        if cn < 3.0:
            phrases = phrases + PHRASES_NUL_PROBABLE
    else:
        phrases = PHRASES_LEGER_FAVORI
        if cn < 3.0:
            phrases = phrases + PHRASES_NUL_PROBABLE

    return random.choice(phrases)


def email_lancement_journee(utilisateur, semaine_id, matchs=None, deadline_dt=None):
    """Email d'annonce de la nouvelle journee : 4 matchs + cotes + deadline + commentaire Kingo"""
    import random
    from datetime import datetime

    prenom = utilisateur.get('prenom') or utilisateur.get('pseudo')

    PHRASES_KINGO = [
        f"Nouvelle semaine, nouvelles humiliations. Kingo a deja ses pronostics. Et toi {prenom}, tu dors encore ?",
        f"J{semaine_id} : Kingo a analyse, Kingo a pronostique, Kingo va gagner. Toi {prenom}, on verra.",
        f"Allez {prenom}, c'est l'heure de montrer si tu merites ta place ou si tu fais juste de la figuration.",
        f"Les matchs sont la, les cotes sont la, il ne manque que tes pronostics {prenom}. Enfin... si tu oses.",
        f"C'est reparti {prenom} ! N'oublie pas : le dernier herite des pronos de Kingo. Motivation suffisante ?",
        f"Nouvelle journee, nouveau carnage annonce. {prenom}, tu es prevenu(e). Kingo regarde.",
        f"J{semaine_id} au programme ! Kingo a sorti la loupe, le cafe, et ses pronostics en or. Toi ?",
        f"{prenom}, les matchs viennent de tomber. Kingo les a deja decortiques. A toi de jouer.",
    ]

    kingo_comment = random.choice(PHRASES_KINGO)

    # Cartes match : equipes + cotes + date/heure
    matchs_html = ""
    if matchs:
        for i, m in enumerate(matchs):
            home = m.get('equipe_home', '???')
            away = m.get('equipe_away', '???')
            cote_h = m.get('cote_home', '-')
            cote_n = m.get('cote_draw', '-')
            cote_a = m.get('cote_away', '-')

            date_str = ""
            if m.get('date_match'):
                try:
                    dt = datetime.fromisoformat(str(m['date_match']).replace('Z', '').replace('+00:00', ''))
                    jours = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
                    date_str = f"{jours[dt.weekday()]} {dt.day:02d}/{dt.month:02d} — {dt.hour}h{dt.minute:02d}"
                except Exception:
                    pass

            matchs_html += f'''
            <div style="background: #f0f4ff; border: 2px solid #D4AF37; border-radius: 10px; padding: 15px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="color: #B8960C; font-size: 11px; font-weight: bold; letter-spacing: 1px;">MATCH {i+1}</span>
                    <span style="color: #445; font-size: 11px;">{date_str}</span>
                </div>
                <div style="text-align: center; padding: 8px 0;">
                    <div style="color: #0d1b3e; font-size: 15px; font-weight: bold;">{home}</div>
                    <div style="color: #B8960C; font-size: 13px; font-weight: bold; margin: 6px 0;">VS</div>
                    <div style="color: #0d1b3e; font-size: 15px; font-weight: bold;">{away}</div>
                </div>
                <div style="display: flex; justify-content: center; gap: 20px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #d0d8f0;">
                    <div style="text-align: center;">
                        <div style="color: #445; font-size: 10px; margin-bottom: 3px;">Domicile</div>
                        <div style="color: #007a3d; font-size: 16px; font-weight: bold;">{cote_h}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #445; font-size: 10px; margin-bottom: 3px;">Nul</div>
                        <div style="color: #B8960C; font-size: 16px; font-weight: bold;">{cote_n}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #445; font-size: 10px; margin-bottom: 3px;">Exterieur</div>
                        <div style="color: #cc2200; font-size: 16px; font-weight: bold;">{cote_a}</div>
                    </div>
                </div>
            </div>
            '''

    # Bloc deadline avec temps restant
    deadline_html = ""
    if deadline_dt:
        try:
            jours_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            date_label = f"{jours_fr[deadline_dt.weekday()]} {deadline_dt.day:02d}/{deadline_dt.month:02d} a {deadline_dt.hour}h{deadline_dt.minute:02d}"

            delta = deadline_dt - datetime.now()
            total_sec = int(delta.total_seconds())
            if total_sec > 0:
                jours_r = total_sec // 86400
                heures_r = (total_sec % 86400) // 3600
                if jours_r > 0:
                    restant = f"dans {jours_r}j {heures_r}h"
                else:
                    minutes_r = (total_sec % 3600) // 60
                    restant = f"dans {heures_r}h{minutes_r:02d}"
            else:
                restant = "deadline depassee"
        except Exception:
            date_label = str(deadline_dt)
            restant = ""

        deadline_html = f'''
        <div style="background: linear-gradient(135deg, #3d0000 0%, #5c0000 100%); border: 2px solid #FF4444; border-radius: 10px; padding: 18px; margin: 20px 0; text-align: center;">
            <div style="font-size: 24px; margin-bottom: 6px;">⏰</div>
            <div style="color: #FF4444; font-weight: bold; font-size: 12px; letter-spacing: 2px; margin-bottom: 6px;">DEADLINE</div>
            <div style="color: #FFFFFF; font-size: 20px; font-weight: bold; margin-bottom: 4px;">{date_label}</div>
            <div style="color: #FFAAAA; font-size: 14px; font-weight: bold;">{restant}</div>
        </div>
        '''

    content = f'''
    <h2>Journee {semaine_id} — Les pronostics sont ouverts !</h2>
    <p>Bonjour <strong>{prenom}</strong>,</p>

    {deadline_html}

    <h3 style="color: #D4AF37; margin-top: 25px;">⚽ Les 4 matchs de la J{semaine_id}</h3>
    {matchs_html}

    <div style="background: rgba(212, 175, 55, 0.1); border-left: 3px solid #D4AF37; padding: 12px 15px; margin: 20px 0; border-radius: 5px;">
        <p style="color: #D4AF37; margin: 0; font-style: italic;">"{kingo_comment}"</p>
        <p style="color: #888; font-size: 11px; margin: 5px 0 0 0; text-align: right;">— Kingo 🤖</p>
    </div>

    <p style="color: #ff6b6b; margin-top: 20px;"><strong>⚠️ Attention :</strong> Si vous ne saisissez pas vos pronostics avant la deadline, le systeme vous attribuera automatiquement les pronostics de Kingo (joker VOL consomme) — ou une penalite de <strong>-100 pts</strong> si vous n'avez plus de joker.</p>

    <p style="text-align: center; margin-top: 25px;">
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/" class="button" style="font-size: 16px; padding: 14px 32px;">🎯 Poser mes pronostics</a>
    </p>
    '''

    return get_base_template(content, f"J{semaine_id} — Posez vos pronostics !")


def email_rappel_j7(utilisateur):
    """DEPRECATED - Redirige vers email_lancement_journee pour compatibilite"""
    return email_lancement_journee(utilisateur, 1)


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
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/" class="button" style="background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);">
            Se connecter
        </a>
    </p>

    <p style="color: #AAAAAA; font-size: 12px; text-align: center;">
        Vous avez jusqu'au coup d'envoi du premier match.
    </p>
    '''

    return get_base_template(content, "Dernier Rappel")


# ============================================
# ENVOI NOUVELLE JOURNEE (TOUS LES JOUEURS)
# ============================================

def envoyer_lancement_journee(semaine_id):
    """
    Envoie l'email d'annonce de la nouvelle journee a tous les joueurs actifs.
    Affiche les 4 matchs actifs avec l'analyse Kingo + la deadline (1h avant le 1er match).
    """
    from modules.supabase_db import get_supabase
    from datetime import datetime, timedelta

    supabase = get_supabase()

    # Recuperer les matchs actifs de la semaine, tries par date
    matchs = supabase._request('GET',
        f'matches?semaine_id=eq.{semaine_id}&is_active=eq.true&select=id,equipe_home,equipe_away,date_match,cote_home,cote_draw,cote_away&order=date_match'
    ) or []

    if not matchs:
        return [], "Aucun match actif pour cette semaine"

    # Calculer la deadline = 1h avant le 1er match
    deadline_dt = None
    try:
        premiere_date = matchs[0].get('date_match')
        if premiere_date:
            dt = datetime.fromisoformat(str(premiere_date).replace('Z', '').replace('+00:00', ''))
            deadline_dt = dt - timedelta(hours=1)
    except Exception:
        pass

    # Envoyer a tous les utilisateurs actifs
    utilisateurs = get_utilisateurs_emails()
    resultats = []

    for user in utilisateurs:
        html = email_lancement_journee(user, semaine_id, matchs, deadline_dt)
        success, msg = send_email(
            user['email'],
            f"Elite Pronos — J{semaine_id} : Posez vos pronostics !",
            html
        )
        resultats.append({'user': user['pseudo'], 'success': success, 'message': msg})

    return resultats, f"{len(resultats)} email(s) envoye(s)"


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

    <p style="text-align: center;">
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/" class="button">Se connecter</a>
    </p>
    '''

    return get_base_template(content, "Synthese des Paris")


def email_resultats_ironiques(semaine_id, classement, matchs_resultats, commentaire_bot="", highlights=None):
    """
    Email de resultats avec debrief ironique du bot
    classement: liste de dicts {pseudo, points, rang, bons_pronos, scores_exacts, grand_chelem}
    matchs_resultats: liste de dicts {equipe_home, equipe_away, score_final_home, score_final_away}
    commentaire_bot: debrief ironique genere par Kingo
    highlights: dict {grand_chelem, jokers, plus_gros_score, meilleure_remontee, plus_grosse_chute}
    """
    if highlights is None:
        highlights = {}

    # === COMMENTAIRE DU BOT ===
    commentaire_html = ""
    if commentaire_bot:
        commentaire_html = f'''
        <div style="background: #e8d5f5; border: 1px solid #9b59b6; border-radius: 10px; padding: 20px; margin: 20px 0;">
            <div style="display: flex; align-items: flex-start;">
                <div style="font-size: 32px; margin-right: 15px;">🤖</div>
                <div>
                    <div style="color: #6a0dad; font-weight: bold; font-size: 14px; margin-bottom: 8px;">Kingo - Le Debrief</div>
                    <p style="color: #1a1a3e; margin: 0; line-height: 1.8; font-style: italic;">{commentaire_bot}</p>
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
                <div style="margin: 0 15px; padding: 5px 15px; background: linear-gradient(135deg, #1a3a5c 0%, #0d2a45 100%); border: 1px solid #D4AF37; border-radius: 5px; color: #ffffff; font-weight: bold; font-size: 16px;">{m['score_final_home']} - {m['score_final_away']}</div>
                <div style="flex: 1; text-align: left; color: #ccc; font-size: 13px;">{m['equipe_away']}</div>
            </div>
            '''
        matchs_html = f'''
        <div style="background: #0a0a1a; border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #FFD700; margin: 0 0 15px 0; font-size: 16px;">⚽ Resultats des Matchs</h3>
            {matchs_items}
        </div>
        '''

    # === HIGHLIGHTS ===
    highlights_html = ""

    # Grand Chelem
    gc_joueurs = highlights.get('grand_chelem', [])
    if gc_joueurs:
        noms_gc = ", ".join(f"<strong>@{j['pseudo']}</strong>" for j in gc_joueurs)
        highlights_html += f'''
        <div style="background: linear-gradient(135deg, #1a1200 0%, #2a2000 100%); border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin: 10px 0; text-align: center;">
            <div style="font-size: 28px; margin-bottom: 6px;">🏆</div>
            <div style="color: #FFD700; font-weight: bold; font-size: 15px; margin-bottom: 4px;">GRAND CHELEM !</div>
            <div style="color: #fff; font-size: 13px;">{noms_gc} — 4/4 corrects cette semaine !</div>
        </div>
        '''

    # Jokers
    jokers = highlights.get('jokers', [])
    for joker in jokers:
        pseudo = joker.get('pseudo', '?')
        type_j = joker.get('type_joker', '')
        pts_joueur = joker.get('points_semaine', 0)
        pts_color = "#00FF00" if pts_joueur > 0 else "#FF4444"
        pts_sign = "+" if pts_joueur > 0 else ""

        if type_j == 'double':
            highlights_html += f'''
            <div style="background: #0a0a1a; border: 1px solid #FFD700; border-radius: 10px; padding: 12px; margin: 10px 0; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span style="font-size: 20px;">⚡</span>
                    <span style="color: #FFD700; font-weight: bold; margin-left: 8px;">Joker DOUBLE</span>
                    <span style="color: #ccc; font-size: 13px; margin-left: 6px;">@{pseudo}</span>
                </div>
                <div style="color: {pts_color}; font-weight: bold; font-size: 15px;">{pts_sign}{round(pts_joueur, 1)} pts</div>
            </div>
            '''
        elif type_j == 'vol':
            cible = joker.get('cible_pseudo', '?')
            highlights_html += f'''
            <div style="background: #0a0a1a; border: 1px solid #9b59b6; border-radius: 10px; padding: 12px; margin: 10px 0; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span style="font-size: 20px;">🃏</span>
                    <span style="color: #9b59b6; font-weight: bold; margin-left: 8px;">Joker VOL</span>
                    <span style="color: #ccc; font-size: 13px; margin-left: 6px;">@{pseudo} a vole @{cible}</span>
                </div>
                <div style="color: {pts_color}; font-weight: bold; font-size: 15px;">{pts_sign}{round(pts_joueur, 1)} pts</div>
            </div>
            '''

    # Plus gros score
    top = highlights.get('plus_gros_score')
    if top:
        highlights_html += f'''
        <div style="background: #0a0a1a; border: 1px solid #27ae60; border-radius: 10px; padding: 12px; margin: 10px 0; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="font-size: 20px;">🥇</span>
                <span style="color: #27ae60; font-weight: bold; margin-left: 8px;">Plus gros score</span>
                <span style="color: #ccc; font-size: 13px; margin-left: 6px;">@{top['pseudo']} — {top['bons_pronos']}/4 corrects</span>
            </div>
            <div style="color: #00FF00; font-weight: bold; font-size: 15px;">+{round(top['points'], 1)} pts</div>
        </div>
        '''

    # Meilleure remontee
    remontee = highlights.get('meilleure_remontee')
    if remontee and remontee['delta'] > 0:
        highlights_html += f'''
        <div style="background: #0a0a1a; border: 1px solid #3498db; border-radius: 10px; padding: 12px; margin: 10px 0; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="font-size: 20px;">📈</span>
                <span style="color: #3498db; font-weight: bold; margin-left: 8px;">Meilleure remontee</span>
                <span style="color: #ccc; font-size: 13px; margin-left: 6px;">@{remontee['pseudo']}</span>
            </div>
            <div style="color: #3498db; font-weight: bold; font-size: 15px;">#{remontee['rang_avant']} → #{remontee['rang_apres']} <span style="color: #00FF00;">(+{remontee['delta']})</span></div>
        </div>
        '''

    # Plus grosse chute
    chute = highlights.get('plus_grosse_chute')
    if chute and chute['delta'] < 0:
        highlights_html += f'''
        <div style="background: #0a0a1a; border: 1px solid #e74c3c; border-radius: 10px; padding: 12px; margin: 10px 0; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="font-size: 20px;">📉</span>
                <span style="color: #e74c3c; font-weight: bold; margin-left: 8px;">Plus grosse chute</span>
                <span style="color: #ccc; font-size: 13px; margin-left: 6px;">@{chute['pseudo']}</span>
            </div>
            <div style="color: #e74c3c; font-weight: bold; font-size: 15px;">#{chute['rang_avant']} → #{chute['rang_apres']} <span style="color: #FF4444;">({chute['delta']})</span></div>
        </div>
        '''

    # Triple defi accompli (3/3)
    defis_list = highlights.get('defis', [])
    if defis_list:
        lignes_defis = ""
        for d in defis_list:
            lignes_defis += f'<div style="color:#ccc; font-size:13px; margin:4px 0;">🏆 @<strong>{d["pseudo"]}</strong> a reussi les 3 defis → <span style="color:#FFD700;">+1 🃏 Joker VOL</span></div>'
        highlights_html += f'''
        <div style="background: #0a0a1a; border: 1px solid #FFD700; border-radius: 10px; padding: 15px; margin: 10px 0;">
            <div style="margin-bottom: 10px;">
                <span style="font-size: 20px;">🎯</span>
                <span style="color: #FFD700; font-weight: bold; margin-left: 8px;">Triple Defi accompli !</span>
            </div>
            {lignes_defis}
        </div>
        '''

    content = f'''
    <h2>Resultats Semaine {semaine_id}</h2>
    <p>Les matchs sont termines ! Voici le verdict.</p>

    {commentaire_html}

    {matchs_html}

    {highlights_html}

    <p style="text-align: center; margin-top: 25px;">
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
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/" class="button">Se connecter</a>
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


def email_confirmation_code(destinataire, pseudo, code):
    """
    Envoie un email avec le code de verification a 6 caracteres
    lors de l'inscription.
    Retourne (success, message)
    """
    content = f'''
    <div style="
        background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 100%);
        border: 2px solid #D4AF37;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    ">
        <h2 style="color: #D4AF37; margin-top: 0;">Verification de votre email</h2>
        <p style="color: #FFFFFF; font-size: 1em;">
            Bonjour <strong style="color: #FFD700;">{pseudo}</strong>,
        </p>
        <p style="color: #CCCCCC;">
            Pour finaliser votre inscription sur Elite Pronos,<br>
            saisissez le code ci-dessous dans le formulaire :
        </p>
        <div style="
            background: #0a0a1a;
            border: 2px solid #FFD700;
            border-radius: 10px;
            padding: 20px;
            margin: 20px auto;
            max-width: 250px;
        ">
            <span style="
                font-size: 2.5em;
                font-weight: bold;
                color: #FFD700;
                letter-spacing: 8px;
                font-family: monospace;
            ">{code}</span>
        </div>
        <p style="color: #AAAAAA; font-size: 0.85em;">
            Ce code est valable 10 minutes.<br>
            Si vous n'avez pas demande d'inscription, ignorez cet email.
        </p>
    </div>
    '''
    html = get_base_template(content, "Verification Email")
    return send_email(destinataire, "Elite Pronos - Code de verification", html)


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

    # Recuperer les 4 matchs actifs de la journee
    matchs = supabase._request('GET', f'matches?semaine_id=eq.{semaine_id}&is_active=eq.true&select=id,equipe_home,equipe_away,score_final_home&order=date_match') or []
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

    # Recuperer les matchs ACTIFS de la semaine avec scores
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

    # Recuperer les jokers (avec cible pour VOL)
    jokers_data = supabase._request('GET', f'jokers_historique?semaine_id=eq.{semaine_id}&select=utilisateur_id,type_joker,cible_vol_id') or []
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

    # Recuperer les voleurs (exclus du GC)
    jokers_vol_data = supabase._request('GET',
        f'jokers_historique?semaine_id=eq.{semaine_id}&type_joker=eq.VOL&select=utilisateur_id'
    ) or []
    voleurs = {j['utilisateur_id'] for j in jokers_vol_data}

    # Construire le classement
    classement = []
    for i, (uid, stats) in enumerate(sorted_users, 1):
        # GC: 4/4 corrects sur matchs actifs, non voleur
        grand_chelem = stats['bons_pronos'] >= 4 and nb_matchs >= 4 and uid not in voleurs
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

    # === HIGHLIGHTS ===

    # 1) Grand Chelem
    gc_joueurs = [{'pseudo': c['pseudo']} for c in classement if c.get('grand_chelem')]

    # 2) Plus gros score de la semaine
    plus_gros_score = None
    if sorted_users:
        top_uid, top_stats = sorted_users[0]
        plus_gros_score = {
            'pseudo': user_map.get(top_uid, 'Inconnu'),
            'points': top_stats['points'],
            'bons_pronos': top_stats['bons_pronos']
        }

    # 3) Jokers enrichis avec cible_pseudo et points_semaine
    jokers_highlights = []
    for j in jokers_data:
        uid = j['utilisateur_id']
        type_j = j['type_joker'].lower()
        pts_joueur = stats_joueur.get(uid, {}).get('points', 0)
        joker_info = {
            'pseudo': user_map.get(uid, 'Inconnu'),
            'type_joker': type_j,
            'points_semaine': pts_joueur
        }
        if type_j == 'vol':
            cible_id = j.get('cible_vol_id')
            joker_info['cible_pseudo'] = user_map.get(cible_id, '?') if cible_id else '?'
        jokers_highlights.append(joker_info)

    # 4) Rang avant / apres pour remontees et chutes
    meilleure_remontee = None
    plus_grosse_chute = None
    try:
        all_preds = supabase._request('GET',
            'predictions?select=user_id,points_gagnes,matches(semaine_id)'
        ) or []
        before_pts = {}
        after_pts = {}
        for p in all_preds:
            uid = p['user_id']
            pts = p.get('points_gagnes') or 0
            s_id = (p.get('matches') or {}).get('semaine_id')
            if s_id is not None:
                after_pts[uid] = after_pts.get(uid, 0) + pts
                if s_id < semaine_id:
                    before_pts[uid] = before_pts.get(uid, 0) + pts

        before_rank = sorted(after_pts.keys(), key=lambda u: before_pts.get(u, 0), reverse=True)
        before_pos = {uid: i + 1 for i, uid in enumerate(before_rank)}
        after_rank_sorted = sorted(after_pts.items(), key=lambda x: x[1], reverse=True)
        after_pos = {uid: i + 1 for i, (uid, _) in enumerate(after_rank_sorted)}

        rank_changes = []
        for uid in after_pos:
            avant = before_pos.get(uid, len(after_pos))
            apres = after_pos[uid]
            delta = avant - apres  # positif = remonté
            rank_changes.append({
                'pseudo': user_map.get(uid, 'Inconnu'),
                'rang_avant': avant,
                'rang_apres': apres,
                'delta': delta
            })

        remontees = [r for r in rank_changes if r['delta'] > 0]
        chutes = [r for r in rank_changes if r['delta'] < 0]
        if remontees:
            meilleure_remontee = max(remontees, key=lambda x: x['delta'])
        if chutes:
            plus_grosse_chute = min(chutes, key=lambda x: x['delta'])
    except Exception as e:
        print(f"Erreur calcul rang changes: {e}")

    highlights = {
        'grand_chelem': gc_joueurs,
        'jokers': jokers_highlights,
        'plus_gros_score': plus_gros_score,
        'meilleure_remontee': meilleure_remontee,
        'plus_grosse_chute': plus_grosse_chute
    }

    # Generer le debrief ironique
    commentaire_bot = _generer_debrief_resultats(classement, matchs_resultats, jokers_actifs)

    # Envoyer a tous les utilisateurs
    utilisateurs = get_utilisateurs_emails()
    resultats = []

    html = email_resultats_ironiques(semaine_id, classement, matchs_resultats, commentaire_bot, highlights)

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
                    <span style="color:#FFD700; font-size:10px;">{prono_data['mise']}</span>
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
        f'matches?semaine_id=eq.{semaine_id}&select=id,equipe_home,equipe_away,cote_home,cote_draw,cote_away&order=id'
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
# EMAIL RAPPEL RETARDATAIRES (H-4 avant deadline)
# ============================================

PHRASES_KINGO_RETARDATAIRES = [
    "Tu sais que meme un poulpe ferait ses pronos plus vite que toi ? Et il a 8 bras pour trouver des excuses.",
    "Allo ? Y'a quelqu'un ? J'ai cru voir une tumbleweed passer devant tes pronostics vides...",
    "Je commence a croire que tu attends que les matchs soient finis pour pronostiquer. Strategie audacieuse.",
    "Meme mon algorithme a eu le temps de faire ses pronos, prendre un cafe et ecrire un roman. Toi ? Rien. Nada. Le vide.",
    "ALERTE DISPARITION : Les pronostics de {pseudo} n'ont toujours pas ete retrouves. Si vous avez des informations, contactez Elite Pronos.",
    "Tu sais ce qui est plus vide que tes pronostics ? Rien. Absolument rien.",
    "J'ai verifie 3 fois. Puis 4. Puis 5. Toujours aucun prono de ta part. Tu testes ma patience ou quoi ?",
    "On m'a dit que tu avais une excuse. Et puis finalement non. Meme pas une excuse.",
    "Les autres ont deja pronos, joker, et se la coulent douce. Et toi ? Tu fais quoi la exactement ?",
    "Je suis un bot et meme MOI j'ai plus d'instinct football que quelqu'un qui ne pronostique pas.",
    "Tick-tock, tick-tock... Tu entends ca ? C'est le son de la deadline qui se rapproche pendant que tu ne fais RIEN.",
    "Fun fact : 100% des joueurs qui ne font pas leurs pronos finissent avec mes pronos a moi. Et crois-moi, je suis genereux... mais pas gentil.",
    "Si l'oubli etait un sport olympique, tu serais deja triple champion du monde.",
    "Je ne dis pas que tu es en retard... mais meme l'escargot de la Journee 1 est arrive avant toi.",
    "BREAKING NEWS : {pseudo} est officiellement porte(e) disparu(e) de la plateforme. La police du prono est en route.",
    "J'ai demande a ChatGPT ce qu'il pensait de ton absence. Il m'a repondu : 'Meme moi j'aurais pronostique.' Aie.",
    "Ton profil est tellement inactif que j'ai failli le classer comme compte fantome. Tu respires au moins ?",
    "Les matchs approchent, ton formulaire est vide, et moi je perds espoir en l'humanite. Merci {pseudo}.",
    "J'ai lance une recherche Google sur 'joueur qui ne fait jamais ses pronos'. Ta photo est apparue en premier resultat.",
    "Tu sais qu'il y a des gens qui paient pour avoir le droit de pronostiquer ? Toi tu l'as et tu t'en fiches. Ingrat.",
    "On raconte que {pseudo} aurait ete apercu(e) pour la derniere fois... tres loin d'Elite Pronos.",
    "Si tu mettais autant d'energie a faire tes pronos qu'a les eviter, tu serais premier du classement.",
    "La deadline arrive plus vite que toi le matin. Et c'est pas peu dire.",
    "Je me suis permis de consulter ton historique. Verdict : tu es un serial oublieur. Recidiviste du neant.",
    "Pendant que tu procrastines, les autres joueurs calculent leurs cotes, affinent leurs strategies, et toi... tu fais la sieste ?",
]

PHRASES_KINGO_CONSEQUENCES = [
    "Si tu ne fais rien, je te colle MES pronostics et je te vole un joker. Oui oui, automatiquement. Sans pitie.",
    "Rappel : pas de pronos = vol automatique d'un joker + tu herites de mes predictions. Et je suis un bot, pas Nostradamus.",
    "Tu veux vraiment que je choisisse pour toi ? Je suis programme pour etre mediocre, pas pour te faire gagner.",
    "Sans tes pronos, c'est VOL AUTO garanti : adieu un joker, bonjour mes predictions de robot.",
    "Le systeme va te voler un joker et copier mes pronos. C'est pas une menace, c'est une promesse algorithmique.",
    "Mes pronos sont generes par un algorithme qui a ete entraine sur... rien du tout. Bonne chance avec ca.",
    "Je vais te filer mes pronos et t'enlever un joker. C'est comme un cadeau d'anniversaire, mais en pire.",
    "Vol auto dans 4 heures : un joker en moins + mes pronos de bot desabuse. Tu veux vraiment vivre ca ?",
    "Imagine : tu ouvres tes resultats et tu vois MES pronos a la place des tiens. L'horreur absolue. Et c'est ce qui va arriver.",
    "Le reglement est formel : oubli = vol auto. Et mes pronos sont aussi fiables qu'un GPS en pleine foret.",
]

PHRASES_KINGO_MOTIVATION = [
    "Allez, il te reste encore un peu de temps. Montre-moi que t'es pas qu'un fantome dans le classement !",
    "4 petits pronos, c'est tout ce qu'on te demande. Meme ton chat pourrait le faire (bon, peut-etre pas).",
    "Saisis tes pronos maintenant et prouve que tu merites ta place parmi l'Elite !",
    "Il n'est pas trop tard pour sauver l'honneur. Clique, pronostique, et redeviens un champion.",
    "Ton classement te remercie d'avance. Enfin... si tu bouges.",
    "Tes adversaires n'attendent que ton absence pour prendre tes points. Tu vas les laisser faire ?",
    "Quelque part au fond de toi, il y a un pronostiqueur qui sommeille. REVEILLE-LE.",
    "T'as 4 heures pour passer de 'fantome du classement' a 'legende vivante'. Au boulot.",
    "Rappelle-toi pourquoi tu t'es inscrit : pour l'honneur, la gloire, et surtout pour ne pas te faire humilier par un bot.",
    "C'est maintenant ou jamais. Enfin surtout maintenant, parce que dans 4 heures c'est trop tard.",
]


def email_rappel_retardataires(pseudo, semaine_id):
    """
    Email de rappel envoye 4h avant la deadline aux joueurs
    qui n'ont pas encore fait leurs pronostics.
    Kingo est creatif et provoque amicalement les retardataires.
    """
    # Choisir des phrases aleatoires pour chaque section
    phrase_provoc = random.choice(PHRASES_KINGO_RETARDATAIRES).replace("{pseudo}", pseudo)
    phrase_consequence = random.choice(PHRASES_KINGO_CONSEQUENCES)
    phrase_motivation = random.choice(PHRASES_KINGO_MOTIVATION)

    content = f'''
    <h2 style="color: #ff6b6b;">Hep {pseudo} ! T'as oublie quelque chose...</h2>

    <!-- Message de Kingo -->
    <div style="background: rgba(155, 89, 182, 0.15); border: 1px solid #9b59b6; border-radius: 12px; padding: 20px; margin: 20px 0;">
        <div style="display: flex; align-items: flex-start;">
            <div style="font-size: 36px; margin-right: 15px;">🤖</div>
            <div>
                <div style="color: #9b59b6; font-weight: bold; font-size: 15px; margin-bottom: 10px;">
                    Kingo - Le Bot Elite
                </div>
                <p style="color: #e0e0e0; margin: 0; line-height: 1.7; font-size: 15px; font-style: italic;">
                    {phrase_provoc}
                </p>
            </div>
        </div>
    </div>

    <!-- Countdown urgence -->
    <div class="highlight-box" style="border-color: #ff6b6b; background: rgba(255, 107, 107, 0.1);">
        <div class="big-text" style="color: #ff6b6b;">&#9200; H - 4</div>
        <p style="margin: 10px 0 0 0; color: #ff6b6b; font-size: 16px; font-weight: bold;">
            Plus que quelques heures avant la deadline de la Journee {semaine_id} !
        </p>
    </div>

    <!-- Consequences -->
    <div style="background: rgba(231, 76, 60, 0.1); border-left: 4px solid #e74c3c; border-radius: 8px; padding: 15px; margin: 20px 0;">
        <p style="color: #e74c3c; font-weight: bold; margin: 0 0 8px 0;">&#9888; Ce qui t'attend si tu ne bouges pas :</p>
        <p style="color: #cccccc; margin: 0; line-height: 1.6;">
            {phrase_consequence}
        </p>
    </div>

    <!-- Bouton CTA -->
    <p style="text-align: center; margin: 30px 0;">
        <a href="https://elitepronos-thnb3wvag3b8szfkoapp7yh.streamlit.app/"
           class="button" style="background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%); font-size: 16px; padding: 18px 45px;">
            Se connecter
        </a>
    </p>

    <!-- Motivation -->
    <div style="text-align: center; margin: 20px 0;">
        <p style="color: #FFD700; font-size: 14px; font-style: italic;">
            &laquo; {phrase_motivation} &raquo;
        </p>
        <p style="color: #666; font-size: 11px;">- Kingo, ton bot prefere (ou pas)</p>
    </div>
    '''

    return get_base_template(content, "Rappel Retardataire")


def envoyer_rappel_retardataires(semaine_id):
    """
    Envoie un email de rappel aux joueurs qui n'ont pas fait leurs pronostics.
    A appeler ~4h avant la deadline (premier match - 5h).
    Retourne la liste des resultats d'envoi.
    """
    from modules.supabase_db import get_supabase
    supabase = get_supabase()

    # Recuperer les utilisateurs actifs
    users = supabase._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo,email') or []
    user_map = {u['id']: u for u in users}

    # Recuperer les matchs de la semaine
    matchs = supabase._request('GET', f'matches?semaine_id=eq.{semaine_id}&select=id') or []
    match_ids = [m['id'] for m in matchs]

    if not match_ids:
        return []

    # Recuperer les predictions existantes
    predictions = supabase._request('GET',
        f'predictions?match_id=in.({",".join(map(str, match_ids))})&select=user_id'
    ) or []

    # Identifier les joueurs qui ont deja pronos
    users_avec_pronos = set(p['user_id'] for p in predictions)

    # Exclure Kingo (le bot)
    kingo_id = None
    for u in users:
        if u['pseudo'] == 'Kingo':
            kingo_id = u['id']
            break

    resultats = []
    for uid, user in user_map.items():
        # Ignorer Kingo et ceux qui ont deja fait leurs pronos
        if uid == kingo_id:
            continue
        if uid in users_avec_pronos:
            continue
        if not user.get('email'):
            continue

        pseudo = user['pseudo']
        html = email_rappel_retardataires(pseudo, semaine_id)

        success, msg = send_email(
            user['email'],
            f"Elite Pronos - Kingo te cherche ! Journee {semaine_id}",
            html
        )
        resultats.append({
            'user': pseudo,
            'email': user['email'],
            'success': success,
            'message': msg
        })

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
        ("Rappel Retardataire", email_rappel_retardataires("TestUser", 21)),
        ("Synthese Paris", email_synthese_paris(1, data_paris_test)),
        ("Resultats Ironiques", email_resultats_ironiques(1, classement_test, {}))
    ]

    for name, html in templates:
        print(f"[OK] Template '{name}' genere ({len(html)} caracteres)")

    print("\n=== FIN TEST ===")
    return True


# ============================================
# EMAIL RECAP REGLEMENT → ADMINS
# ============================================

def email_recap_reglement_admins():
    """
    Envoie aux admins un tableau recap des joueurs regles / non regles.
    Appele automatiquement a chaque validation de reglement.
    Retourne liste de resultats d'envoi.
    """
    from modules.supabase_db import get_supabase
    from datetime import datetime as _dt

    supabase = get_supabase()
    users = supabase._request(
        'GET',
        'utilisateurs?statut=eq.Actif&is_bot=eq.false&select=id,pseudo,prenom,email,reglement_accepte&order=pseudo.asc'
    ) or []

    regles = [u for u in users if u.get('reglement_accepte')]
    non_regles = [u for u in users if not u.get('reglement_accepte')]

    date_str = _dt.now().strftime("%d/%m/%Y %H:%M")

    def _ligne(u, couleur_bg, icone):
        return f"""
        <tr style="background:{couleur_bg};">
            <td style="padding:8px 12px;color:#FFFFFF;">{icone}</td>
            <td style="padding:8px 12px;color:#FFD700;font-weight:bold;">{u.get('pseudo','?')}</td>
            <td style="padding:8px 12px;color:#CCCCCC;">{u.get('prenom') or '-'}</td>
            <td style="padding:8px 12px;color:#AAAAAA;font-size:0.85em;">{u.get('email') or '-'}</td>
        </tr>"""

    lignes_regles = ''.join(_ligne(u, '#0a1f0a', '✅') for u in regles) or \
        '<tr><td colspan="4" style="color:#666;padding:10px;text-align:center;">Aucun</td></tr>'
    lignes_non = ''.join(_ligne(u, '#1f0a0a', '❌') for u in non_regles) or \
        '<tr><td colspan="4" style="color:#666;padding:10px;text-align:center;">Aucun</td></tr>'

    thead = """
    <tr style="background:linear-gradient(90deg,#D4AF37,#B8960C);">
        <th style="padding:8px 12px;color:#000;text-align:left;width:30px;"></th>
        <th style="padding:8px 12px;color:#000;text-align:left;">Pseudo</th>
        <th style="padding:8px 12px;color:#000;text-align:left;">Prenom</th>
        <th style="padding:8px 12px;color:#000;text-align:left;">Email</th>
    </tr>"""

    content = f"""
    <div style="text-align:center;margin-bottom:20px;">
        <h2 style="color:#D4AF37;">Etat du Reglement — {date_str}</h2>
        <div style="display:inline-flex;gap:30px;margin-top:10px;">
            <div style="background:#0a1f0a;border:1px solid #4CAF50;border-radius:8px;padding:12px 24px;">
                <div style="color:#4CAF50;font-size:2em;font-weight:bold;">{len(regles)}</div>
                <div style="color:#CCCCCC;font-size:0.85em;">Reglement valide ✅</div>
            </div>
            <div style="background:#1f0a0a;border:1px solid #FF4444;border-radius:8px;padding:12px 24px;">
                <div style="color:#FF4444;font-size:2em;font-weight:bold;">{len(non_regles)}</div>
                <div style="color:#CCCCCC;font-size:0.85em;">En attente ❌</div>
            </div>
        </div>
    </div>

    <h3 style="color:#4CAF50;margin:20px 0 8px 0;">✅ Joueurs qui ont regle ({len(regles)})</h3>
    <table style="width:100%;border-collapse:collapse;border-radius:8px;overflow:hidden;">
        {thead}{lignes_regles}
    </table>

    <h3 style="color:#FF4444;margin:24px 0 8px 0;">❌ Joueurs qui n'ont pas regle ({len(non_regles)})</h3>
    <table style="width:100%;border-collapse:collapse;border-radius:8px;overflow:hidden;">
        {thead}{lignes_non}
    </table>
    """

    html = get_base_template(content, "Recap Reglement")

    admins = supabase._request('GET', 'utilisateurs?is_admin=eq.true&select=pseudo,email') or []
    resultats = []
    for admin in admins:
        if not admin.get('email'):
            continue
        ok, msg = send_email(admin['email'], f"Elite Pronos — Recap Reglement ({len(regles)}/{len(regles)+len(non_regles)})", html)
        resultats.append({'admin': admin['pseudo'], 'success': ok, 'message': msg})

    return resultats


# ============================================
# EMAIL RELANCE REGLEMENT → JOUEURS NON REGLES
# ============================================

PHRASES_KINGO_RELANCE_REGLEMENT = [
    "Les delais ne sont pas une suggestion, {prenom}. Le championnat commence dans moins d'une semaine et ton reglement n'est toujours pas valide. Une simple lecture suffit. Kingo attend.",
    "{prenom}, le coup d'envoi approche a grands pas. Tout le monde est pret... sauf toi. Valide ton reglement avant qu'il ne soit trop tard pour participer.",
    "Ah, {prenom}. Kingo pensait que tu avais oublie. Et visiblement, c'est le cas. Le debut du championnat est dans 7 jours. Ton reglement n'est pas valide. Contacte vite un admin.",
    "Message urgent de Kingo a {prenom} : le championnat commence bientot et ta participation est suspendue. Prends le temps de valider ton reglement — c'est maintenant ou jamais.",
]


def envoyer_relance_non_regles():
    """
    Envoie un email de relance a chaque joueur actif qui n'a pas valide son reglement.
    A appeler manuellement depuis le panel admin, idealement 1 semaine avant J1.
    Retourne (nb_ok, nb_err, details).
    """
    import random
    from modules.supabase_db import get_supabase

    supabase = get_supabase()
    users = supabase._request(
        'GET',
        'utilisateurs?statut=eq.Actif&reglement_accepte=eq.false&select=id,pseudo,prenom,email'
    ) or []

    nb_ok, nb_err, details = 0, 0, []

    for u in users:
        email = u.get('email')
        prenom = u.get('prenom') or u.get('pseudo', '')
        pseudo = u.get('pseudo', '')

        if not email:
            continue

        phrase = random.choice(PHRASES_KINGO_RELANCE_REGLEMENT).format(prenom=prenom)

        content = f"""
        <div style="
            background:linear-gradient(135deg,#0d1117 0%,#1a1a2e 100%);
            border:2px solid #FF4444;border-radius:12px;padding:0;overflow:hidden;margin-bottom:20px;
        ">
            <div style="background:linear-gradient(90deg,#FF4444,#CC0000);padding:8px 18px;
                        display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#FFF;font-size:1.1em;font-weight:900;letter-spacing:1px;">
                    ⚠️ RELANCE REGLEMENT
                </span>
                <span style="color:#FFF;font-size:0.75em;">Elite Pronos</span>
            </div>
            <div style="padding:20px;">
                <div style="color:#FF6666;font-size:1em;font-weight:bold;margin-bottom:8px;">
                    Bonjour {prenom},
                </div>
                <div style="color:#e6edf3;font-size:1em;line-height:1.7;margin-bottom:16px;">
                    {phrase}
                </div>
                <div style="background:#0a0a1a;border:1px solid #FF4444;border-radius:8px;
                            padding:14px;text-align:center;">
                    <div style="color:#CCCCCC;font-size:0.9em;">
                        Pour valider votre participation, contactez un administrateur Elite Pronos.<br>
                        Votre compte <strong style="color:#FFD700;">@{pseudo}</strong> est actuellement
                        en <strong style="color:#FF4444;">lecture seule</strong>.
                    </div>
                </div>
            </div>
        </div>
        """
        html = get_base_template(content, "Relance Reglement")
        ok, msg = send_email(email, "Elite Pronos — Valide ton reglement avant le coup d'envoi !", html)

        if ok:
            nb_ok += 1
        else:
            nb_err += 1
        details.append({'pseudo': pseudo, 'email': email, 'success': ok, 'message': msg})

    return nb_ok, nb_err, details


if __name__ == "__main__":
    test_email_template()
