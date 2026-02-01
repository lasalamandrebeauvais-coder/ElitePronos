"""
Scheduler Resultats - Elite Pronos
OBSOLETE: Remplace par GitHub Actions (auto_update_scores.py)
Ce fichier conserve uniquement get_scheduler_status() pour l'affichage
"""
from datetime import datetime

def get_scheduler_status():
    """
    Retourne le statut du systeme de mise a jour automatique.
    Note: La mise a jour est geree par GitHub Actions (toutes les 15 min)
    """
    return {
        'actif': True,
        'message': 'Auto-update via GitHub Actions',
        'couleur': '#00FF00',
        'derniere_verification': datetime.now().strftime('%H:%M')
    }


def demarrer_scheduler():
    """
    OBSOLETE - Le scheduler est maintenant gere par GitHub Actions.
    Cette fonction ne fait plus rien mais est conservee pour compatibilite.
    """
    pass


def arreter_scheduler():
    """OBSOLETE - Conserve pour compatibilite."""
    pass
