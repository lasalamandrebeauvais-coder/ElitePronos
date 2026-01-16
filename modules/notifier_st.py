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
# EMAILS ADMIN : SYNTHESE & RESULTATS
# ============================================

def email_synthese_paris(semaine_id, data_paris):
    """
    Email de synthese des paris de tous les joueurs
    Envoye 15min apres la deadline
    data_paris: liste de dicts {pseudo, matchs: [{equipes, prono, mise}]}
    """
    # Construire le tableau des pronostics
    rows_html = ""
    for joueur in data_paris:
        pseudo = joueur['pseudo']
        for i, match in enumerate(joueur.get('matchs', [])):
            equipes = match.get('equipes', 'Match inconnu')
            prono = f"{match.get('home', '?')}-{match.get('away', '?')}"
            mise = match.get('mise', 0)

            if i == 0:
                # Premiere ligne avec le pseudo
                rows_html += f'''
                <tr style="border-bottom: 1px solid #333;">
                    <td rowspan="{len(joueur.get('matchs', []))}" style="padding: 10px; color: #FFD700; font-weight: bold; vertical-align: top; border-right: 1px solid #333;">
                        @{pseudo}
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

    <div style="background: #0a0a1a; border-radius: 10px; padding: 15px; margin: 20px 0; overflow-x: auto;">
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
        <p style="color: #888; font-size: 12px; margin: 5px 0 0 0;">
            Les resultats seront calcules automatiquement apres les matchs.
        </p>
    </div>
    '''

    return get_base_template(content, "Synthese des Paris")


def email_resultats_ironiques(semaine_id, classement, commentaires):
    """
    Email de resultats avec commentaires ironiques
    classement: liste de dicts {pseudo, points, rang, evolution}
    commentaires: dict {pseudo: commentaire_ironique}
    """
    # Phrases ironiques predefinies
    phrases_ironiques = {
        'premier': [
            "Le roi de la semaine ! Enfin, jusqu'a ce qu'il se plante lamentablement...",
            "Bravo champion ! Les debutants ont parfois de la chance...",
            "Impressionnant ! Tu as du regarder les matchs au lieu de deviner ?",
        ],
        'dernier': [
            "Au moins, tu es constant dans la mediocrite !",
            "Tu devrais peut-etre essayer les echecs a la place ?",
            "Ton joker aurait ete plus utile que tes pronostics...",
            "Meme un singe avec des flechettes aurait fait mieux !",
        ],
        'progresse': [
            "Tiens, tu as enfin trouve comment marche le foot ?",
            "Belle remontee ! Tu lisais des tutos sur YouTube ?",
        ],
        'regresse': [
            "La chute est rude ! Tu etais en vacances mentales ?",
            "De heros a zero en une semaine, chapeau !",
        ],
        'stable': [
            "Stable comme un diesel... qui ne demarre pas.",
            "Ni bon ni mauvais, juste... la.",
        ]
    }

    import random

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
            evo_type = 'progresse'
        elif evolution < 0:
            evo_emoji = f"<span style='color: #FF4444;'>↓ {evolution}</span>"
            evo_type = 'regresse'
        else:
            evo_emoji = "<span style='color: #888;'>→ 0</span>"
            evo_type = 'stable'

        # Couleur selon le rang
        if rang == 1:
            rang_style = "background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #0a0a1a;"
            evo_type = 'premier'
        elif rang == len(classement):
            rang_style = "background: #8B0000; color: #fff;"
            evo_type = 'dernier'
        elif rang <= 3:
            rang_style = "background: #C0C0C0; color: #0a0a1a;"
        else:
            rang_style = "background: #333; color: #fff;"

        # Commentaire ironique
        commentaire = commentaires.get(pseudo, random.choice(phrases_ironiques.get(evo_type, phrases_ironiques['stable'])))

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

    <p style="color: #888; font-size: 12px; text-align: center;">
        Rendez-vous la semaine prochaine pour de nouveaux pronostics !
    </p>
    '''

    return get_base_template(content, "Resultats de la Semaine")


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


def envoyer_synthese_paris(semaine_id):
    """
    Envoie la synthese des paris a tous les joueurs
    A appeler 15min apres la deadline
    """
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Recuperer tous les pronostics de la semaine
    cursor.execute("""
        SELECT u.pseudo, m.equipe_home, m.equipe_away,
               p.score_prono_home, p.score_prono_away, p.mise_points
        FROM predictions p
        JOIN utilisateurs u ON p.user_id = u.id
        JOIN matches m ON p.match_id = m.id
        WHERE m.semaine_id = ?
        ORDER BY u.pseudo, m.id
    """, (semaine_id,))

    rows = cursor.fetchall()
    conn.close()

    # Organiser par joueur
    data_paris = {}
    for row in rows:
        pseudo, home, away, prono_h, prono_a, mise = row
        if pseudo not in data_paris:
            data_paris[pseudo] = {'pseudo': pseudo, 'matchs': []}
        data_paris[pseudo]['matchs'].append({
            'equipes': f"{home} vs {away}",
            'home': prono_h,
            'away': prono_a,
            'mise': mise
        })

    # Envoyer a tous les utilisateurs
    utilisateurs = get_utilisateurs_emails()
    resultats = []

    html = email_synthese_paris(semaine_id, list(data_paris.values()))

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
    """
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Calculer le classement de la semaine
    cursor.execute("""
        SELECT u.pseudo, COALESCE(SUM(p.points_gagnes), 0) as total_points
        FROM utilisateurs u
        LEFT JOIN predictions p ON p.user_id = u.id
        LEFT JOIN matches m ON p.match_id = m.id AND m.semaine_id = ?
        WHERE u.statut = 'Actif'
        GROUP BY u.id, u.pseudo
        ORDER BY total_points DESC
    """, (semaine_id,))

    rows = cursor.fetchall()
    conn.close()

    # Construire le classement
    classement = []
    for i, row in enumerate(rows, 1):
        pseudo, points = row
        classement.append({
            'rang': i,
            'pseudo': pseudo,
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
