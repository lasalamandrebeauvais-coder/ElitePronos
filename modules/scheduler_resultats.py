"""
Scheduler Resultats - Elite Pronos
Lance automatiquement le bot de resultats toutes les 10 minutes
pendant les jours de match
"""
import threading
import time
import sqlite3
import os
from datetime import datetime, timedelta, timezone

# Import du bot
from modules.bot_resultats import recuperer_et_mettre_a_jour_scores

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Variable globale pour le thread
_scheduler_thread = None
_scheduler_running = False


def est_jour_de_match():
    """
    Verifie si aujourd'hui est un jour de match
    Retourne True si au moins un match est prevu aujourd'hui ou demain
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Recuperer la saison active
        cursor.execute("SELECT id FROM saisons WHERE is_active = 1")
        saison_row = cursor.fetchone()
        if not saison_row:
            conn.close()
            return False
        saison_id = saison_row[0]

        # Recuperer la journee courante
        cursor.execute("SELECT MAX(semaine_id) FROM matches WHERE saison_id = ? AND is_active = 1", (saison_id,))
        journee_row = cursor.fetchone()
        if not journee_row or not journee_row[0]:
            conn.close()
            return False
        journee_courante = journee_row[0]

        # Verifier si des matchs sont dans les prochaines 24h ou ont eu lieu dans les 3h
        now = datetime.now(timezone.utc)
        trois_heures_avant = now - timedelta(hours=3)
        vingt_quatre_heures_apres = now + timedelta(hours=24)

        cursor.execute("""
            SELECT COUNT(*) FROM matches
            WHERE saison_id = ? AND semaine_id = ? AND is_active = 1
            AND status != 'FINISHED'
        """, (saison_id, journee_courante))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    except Exception as e:
        print(f"Erreur verification jour de match: {e}")
        return False


def matchs_en_attente_de_score():
    """
    Verifie s'il y a des matchs qui attendent un score
    (match commence depuis +50min sans score mi-temps ou +120min sans score final)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM saisons WHERE is_active = 1")
        saison_row = cursor.fetchone()
        if not saison_row:
            conn.close()
            return False
        saison_id = saison_row[0]

        cursor.execute("SELECT MAX(semaine_id) FROM matches WHERE saison_id = ? AND is_active = 1", (saison_id,))
        journee_row = cursor.fetchone()
        if not journee_row or not journee_row[0]:
            conn.close()
            return False
        journee_courante = journee_row[0]

        cursor.execute("""
            SELECT date_match, score_mi_temps_home, score_final_home, status
            FROM matches
            WHERE saison_id = ? AND semaine_id = ? AND is_active = 1
        """, (saison_id, journee_courante))

        matchs = cursor.fetchall()
        conn.close()

        now = datetime.now(timezone.utc)

        for date_match, mi_h, final_h, status in matchs:
            if status == 'FINISHED':
                continue

            if not date_match:
                continue

            # Parser la date
            try:
                if isinstance(date_match, str):
                    if 'T' in date_match:
                        dt_match = datetime.fromisoformat(date_match.replace('Z', '+00:00'))
                    else:
                        dt_match = datetime.strptime(date_match, '%Y-%m-%d %H:%M:%S')
                        dt_match = dt_match.replace(tzinfo=timezone.utc)
                else:
                    dt_match = date_match
                    if dt_match.tzinfo is None:
                        dt_match = dt_match.replace(tzinfo=timezone.utc)

                minutes = int((now - dt_match).total_seconds() / 60)

                # Match a +50min sans mi-temps ou +120min sans final
                if minutes >= 50 and mi_h is None:
                    return True
                if minutes >= 120 and final_h is None:
                    return True

            except:
                continue

        return False

    except Exception as e:
        print(f"Erreur verification matchs en attente: {e}")
        return False


def _scheduler_loop():
    """
    Boucle principale du scheduler
    Verifie toutes les 10 minutes si des scores doivent etre mis a jour
    """
    global _scheduler_running

    print("[SCHEDULER] Demarrage du scheduler de resultats")

    while _scheduler_running:
        try:
            # Verifier si c'est un jour de match et si des scores sont attendus
            if est_jour_de_match() and matchs_en_attente_de_score():
                print(f"[SCHEDULER] {datetime.now().strftime('%H:%M')} - Lancement mise a jour des scores...")
                recuperer_et_mettre_a_jour_scores()
            else:
                print(f"[SCHEDULER] {datetime.now().strftime('%H:%M')} - Pas de mise a jour necessaire")

        except Exception as e:
            print(f"[SCHEDULER] Erreur: {e}")

        # Attendre 10 minutes (600 secondes)
        # On decoupe en petits intervals pour pouvoir arreter proprement
        for _ in range(60):  # 60 x 10 secondes = 10 minutes
            if not _scheduler_running:
                break
            time.sleep(10)

    print("[SCHEDULER] Arret du scheduler")


def demarrer_scheduler():
    """
    Demarre le scheduler en arriere-plan
    """
    global _scheduler_thread, _scheduler_running

    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        print("[SCHEDULER] Deja en cours d'execution")
        return False

    _scheduler_running = True
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()
    print("[SCHEDULER] Scheduler demarre")
    return True


def arreter_scheduler():
    """
    Arrete le scheduler
    """
    global _scheduler_running

    _scheduler_running = False
    print("[SCHEDULER] Demande d'arret...")


def est_scheduler_actif():
    """
    Retourne True si le scheduler est actif
    """
    global _scheduler_thread, _scheduler_running

    return _scheduler_running and _scheduler_thread is not None and _scheduler_thread.is_alive()


def get_scheduler_status():
    """
    Retourne le statut du scheduler pour affichage
    """
    if est_scheduler_actif():
        return {
            'actif': True,
            'message': 'Bot actif - MAJ toutes les 10 min',
            'couleur': '#00FF00'
        }
    else:
        return {
            'actif': False,
            'message': 'Bot inactif',
            'couleur': '#FF4444'
        }
