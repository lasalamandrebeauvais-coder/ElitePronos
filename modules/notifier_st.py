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
    get_utilisateurs_sans_pronos_j1,
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
        <li>Bonus Grand Chelem : +50 pts si 4/4 corrects</li>
    </ul>

    <p>Que la meilleure strategie gagne !</p>
    '''

    return get_base_template(content, "Nouvelle Saison")


def email_bienvenue(utilisateur):
    """Email de bienvenue pour un nouvel inscrit"""
    prenom = utilisateur.get('prenom') or utilisateur.get('pseudo')
    pseudo = utilisateur.get('pseudo')

    content = f'''
    <h2>Bienvenue dans l'Elite !</h2>
    <p>Bonjour <strong>{prenom}</strong>,</p>
    <p>Votre inscription a Elite Pronos est confirmee.
    Vous faites desormais partie de la ligue des experts !</p>

    <div class="highlight-box">
        <p style="color: #FFD700; margin: 0;">Votre pseudo</p>
        <div class="big-text">@{pseudo}</div>
    </div>

    <p><strong>Vos avantages :</strong></p>
    <ul style="color: #cccccc;">
        <li>1 Joker Points Doubles (x2 sur vos gains)</li>
        <li>1 Joker Points Voles (copiez les pronos d'un rival)</li>
        <li>Acces au classement en temps reel</li>
        <li>Defis entre amis</li>
    </ul>

    <p style="text-align: center;">
        <a href="#" class="button">Commencer a jouer</a>
    </p>

    <p>Bonne chance pour cette saison !</p>
    '''

    return get_base_template(content, "Bienvenue")


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

    <p style="color: #888; font-size: 12px; text-align: center;">
        Vous avez jusqu'au coup d'envoi du premier match.
    </p>
    '''

    return get_base_template(content, "Dernier Rappel")


# ============================================
# ENVOI DE CAMPAGNES
# ============================================

def envoyer_campagne_lancement():
    """Envoie l'email de lancement a tous les utilisateurs"""
    utilisateurs = get_utilisateurs_emails()
    resultats = []

    for user in utilisateurs:
        html = email_lancement_saison(user)
        success, msg = send_email(
            user['email'],
            f"Elite Pronos - La saison {get_saison_label(get_saison_actuelle())} commence !",
            html
        )
        resultats.append({'user': user['pseudo'], 'success': success, 'message': msg})

    return resultats


def envoyer_email_bienvenue(utilisateur):
    """Envoie l'email de bienvenue a un nouvel inscrit"""
    html = email_bienvenue(utilisateur)
    return send_email(
        utilisateur['email'],
        "Bienvenue dans Elite Pronos !",
        html
    )


def envoyer_rappels_j7():
    """Envoie les rappels J-7 aux joueurs sans pronostics"""
    utilisateurs = get_utilisateurs_sans_pronos_j1()
    resultats = []

    for user in utilisateurs:
        html = email_rappel_j7(user)
        success, msg = send_email(
            user['email'],
            "Elite Pronos - Plus que 7 jours !",
            html
        )
        resultats.append({'user': user['pseudo'], 'success': success, 'message': msg})

    return resultats


def envoyer_rappels_j1():
    """Envoie les rappels J-1 aux joueurs sans pronostics"""
    utilisateurs = get_utilisateurs_sans_pronos_j1()
    resultats = []

    for user in utilisateurs:
        html = email_rappel_j1(user)
        success, msg = send_email(
            user['email'],
            "URGENT - Dernier jour pour vos pronostics !",
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

    print("=== TEST TEMPLATES EMAIL ===\n")

    templates = [
        ("Lancement Saison", email_lancement_saison(user_test)),
        ("Bienvenue", email_bienvenue(user_test)),
        ("Rappel J-7", email_rappel_j7(user_test)),
        ("Rappel J-1", email_rappel_j1(user_test))
    ]

    for name, html in templates:
        print(f"[OK] Template '{name}' genere ({len(html)} caracteres)")

    print("\n=== FIN TEST ===")
    return True


if __name__ == "__main__":
    test_email_template()
