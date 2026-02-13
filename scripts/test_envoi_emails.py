"""
Script de test : envoie tous les templates email a une adresse de test.
Usage : python scripts/test_envoi_emails.py
"""
import sys
import os
import time

# Ajouter le dossier racine au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Forcer le mode officiel pour envoyer vraiment
os.environ['IS_OFFICIEL'] = 'true'

from modules.notifier_st import (
    send_email,
    email_lancement_saison,
    email_prospection,
    email_bienvenue,
    email_rappel_j7,
    email_rappel_j1,
    email_rappel_retardataires,
    email_synthese_paris,
    email_resultats_ironiques,
    email_alerte_nouvel_inscrit,
)

DESTINATAIRE = "stephanetonsart@yahoo.fr"

user_test = {
    'id': 1,
    'pseudo': 'Stephane',
    'prenom': 'Stephane',
    'email': DESTINATAIRE
}

# Donnees de test pour la synthese
stats_matchs_test = {
    'PSG vs Marseille': {'dom': 65, 'nul': 15, 'ext': 20},
    'Lyon vs Monaco': {'dom': 40, 'nul': 30, 'ext': 30},
    'Lens vs Lille': {'dom': 50, 'nul': 25, 'ext': 25},
    'Nice vs Rennes': {'dom': 35, 'nul': 35, 'ext': 30},
}

jokers_test = [
    {'pseudo': 'Baggio10', 'type_joker': 'double', 'cible_pseudo': ''},
    {'pseudo': 'Zidane98', 'type_joker': 'vol', 'cible_pseudo': 'Henry14'},
]

commentaire_test = "12 pronostiqueurs en lice cette semaine. Que le spectacle commence ! Baggio10 a mise gros (45 pts) sur PSG vs Marseille. Confiance ou folie ? 2 jokers actives cette semaine ! Ca va chauffer... 65% voient PSG gagner. Unanimite ou piege ?"

# Donnees de test pour les resultats ironiques
classement_test = [
    {'rang': 1, 'pseudo': 'Baggio10', 'points': 95, 'bons_pronos': 4, 'scores_exacts': 1, 'grand_chelem': True},
    {'rang': 2, 'pseudo': 'Zidane98', 'points': 72, 'bons_pronos': 3, 'scores_exacts': 0, 'grand_chelem': False},
    {'rang': 3, 'pseudo': 'Henry14', 'points': 65, 'bons_pronos': 2, 'scores_exacts': 0, 'grand_chelem': False},
    {'rang': 4, 'pseudo': 'Platini10', 'points': 48, 'bons_pronos': 2, 'scores_exacts': 0, 'grand_chelem': False},
    {'rang': 5, 'pseudo': 'Cantona7', 'points': -12, 'bons_pronos': 0, 'scores_exacts': 0, 'grand_chelem': False},
]

matchs_resultats_test = [
    {'equipe_home': 'PSG', 'equipe_away': 'Marseille', 'score_final_home': 2, 'score_final_away': 1},
    {'equipe_home': 'Lyon', 'equipe_away': 'Monaco', 'score_final_home': 1, 'score_final_away': 1},
    {'equipe_home': 'Lens', 'equipe_away': 'Lille', 'score_final_home': 0, 'score_final_away': 2},
    {'equipe_home': 'Nice', 'equipe_away': 'Rennes', 'score_final_home': 3, 'score_final_away': 0},
]

commentaire_resultats_test = "Chapeau bas a <strong>@Baggio10</strong> qui ecrase tout le monde avec <strong>95 pts</strong> cette semaine !<br><br>\U0001f3c6 <strong>GRAND CHELEM</strong> pour <strong>@Baggio10</strong> ! 4/4 corrects, c'est limite suspect... On verifie les cameras !<br><br>\U0001f3af Score exact pour <strong>@Baggio10</strong> ! Precision chirurgicale ou coup de bol monumental ?<br><br>\U0001f3ad <strong>@Zidane98</strong> avait vole des pronos. Le crime a-t-il paye ? A vous de juger.<br><br>Quant a <strong>@Cantona7</strong>... -12 pts. Allez, c'est pas grave, on a tous des mauvaises semaines. Enfin, toi plus que les autres.<br><br>A la semaine prochaine ! D'ici la, essayez de regarder du football au lieu de deviner au hasard."


emails = [
    ("1/8 - Lancement Saison", "Elite Pronos - Nouvelle Saison", email_lancement_saison(user_test)),
    ("2/8 - Prospection", "Elite Pronos - Rejoignez l'aventure", email_prospection()),
    ("3/8 - Bienvenue", "Elite Pronos - Bienvenue dans le Club", email_bienvenue(user_test)),
    ("4/8 - Rappel J-7", "Elite Pronos - Rappel J-7", email_rappel_j7(user_test)),
    ("5/8 - Rappel J-1", "Elite Pronos - Rappel J-1 URGENT", email_rappel_j1(user_test)),
    ("6/8 - Rappel Retardataire", "Elite Pronos - Kingo te cherche ! Journee 23", email_rappel_retardataires("Stephane", 23)),
    ("7/8 - Synthese des Paris", "Elite Pronos - Synthese des Paris (Semaine 23)", email_synthese_paris(23, jokers_test, stats_matchs_test, commentaire_test)),
    ("8/8 - Resultats Ironiques", "Elite Pronos - Resultats Semaine 23", email_resultats_ironiques(23, classement_test, matchs_resultats_test, commentaire_resultats_test)),
]

print(f"=== ENVOI DE {len(emails)} EMAILS DE TEST ===")
print(f"Destinataire : {DESTINATAIRE}\n")

for label, sujet, html in emails:
    print(f"Envoi {label}...")
    success, msg = send_email(DESTINATAIRE, sujet, html)
    status = "OK" if success else "ECHEC"
    print(f"  [{status}] {msg}")
    time.sleep(2)  # Pause entre les envois pour ne pas spam

print(f"\n=== TERMINE - Verifiez la boite {DESTINATAIRE} ===")
