"""
Database Manager pour Elite Pronos
Gestion centralisée de la base de données, saisons et jokers
Phase Finale: Support pluriannuel et automatisation
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Creer le dossier database s'il n'existe pas
DB_DIR = os.path.dirname(DB_PATH)
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)


# ============================================
# GESTION DES SAISONS
# ============================================

def get_saison_actuelle():
    """Retourne l'ID de la saison actuelle (ex: 2024 pour 2024-2025)"""
    now = datetime.now()
    # La saison commence en août
    if now.month >= 8:
        return now.year
    return now.year - 1


def get_saison_label(saison_id):
    """Retourne le label de la saison (ex: '2024-2025')"""
    return f"{saison_id}-{saison_id + 1}"


def get_connection():
    """Retourne une connexion à la base de données"""
    return sqlite3.connect(DB_PATH)


# ============================================
# GESTION DES TABLES
# ============================================

def init_database():
    """Initialise toutes les tables nécessaires"""
    conn = get_connection()
    cursor = conn.cursor()

    # Table des saisons
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saisons (
            id INTEGER PRIMARY KEY,
            label TEXT NOT NULL,
            date_debut DATE,
            date_fin DATE,
            is_active BOOLEAN DEFAULT 0
        )
    ''')

    # Table des paramètres application
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            cle TEXT PRIMARY KEY,
            valeur TEXT,
            description TEXT
        )
    ''')

    # Initialiser les paramètres par défaut
    cursor.execute('''
        INSERT OR IGNORE INTO app_settings (cle, valeur, description)
        VALUES ('is_officiel', 'False', 'Mode officiel - Active envoi emails reels')
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO app_settings (cle, valeur, description)
        VALUES ('smtp_host', '', 'Serveur SMTP')
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO app_settings (cle, valeur, description)
        VALUES ('smtp_port', '587', 'Port SMTP')
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO app_settings (cle, valeur, description)
        VALUES ('smtp_user', '', 'Utilisateur SMTP')
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO app_settings (cle, valeur, description)
        VALUES ('smtp_password', '', 'Mot de passe SMTP')
    ''')

    # Table stock_jokers (avec saison_id)
    # Verifier si la table existe et a besoin de migration
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_jokers'")
    if cursor.fetchone():
        # Table existe - verifier si saison_id existe
        cursor.execute("PRAGMA table_info(stock_jokers)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'saison_id' not in columns:
            # Migration necessaire - recreer la table
            cursor.execute("ALTER TABLE stock_jokers RENAME TO stock_jokers_old")
            cursor.execute('''
                CREATE TABLE stock_jokers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    utilisateur_id INTEGER NOT NULL,
                    saison_id INTEGER NOT NULL DEFAULT 2024,
                    jokers_doubles_disponibles INTEGER DEFAULT 1,
                    jokers_voles_disponibles INTEGER DEFAULT 1,
                    derniere_mise_a_jour TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(utilisateur_id, saison_id),
                    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
                )
            ''')
            # Migrer les donnees
            cursor.execute('''
                INSERT INTO stock_jokers (utilisateur_id, saison_id, jokers_doubles_disponibles, jokers_voles_disponibles)
                SELECT utilisateur_id, 2024, jokers_doubles_disponibles, jokers_voles_disponibles
                FROM stock_jokers_old
            ''')
            cursor.execute("DROP TABLE stock_jokers_old")
    else:
        # Creer la table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_jokers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                utilisateur_id INTEGER NOT NULL,
                saison_id INTEGER NOT NULL DEFAULT 2024,
                jokers_doubles_disponibles INTEGER DEFAULT 1,
                jokers_voles_disponibles INTEGER DEFAULT 1,
                derniere_mise_a_jour TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(utilisateur_id, saison_id),
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
            )
        ''')

    # Table historique des jokers utilisés
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jokers_historique (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER NOT NULL,
            semaine_id INTEGER NOT NULL,
            saison_id INTEGER,
            type_joker TEXT NOT NULL,
            cible_vol_id INTEGER,
            date_utilisation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
            FOREIGN KEY (cible_vol_id) REFERENCES utilisateurs(id)
        )
    ''')

    # Migration: Ajouter saison_id aux tables existantes si manquant
    try:
        cursor.execute("ALTER TABLE matches ADD COLUMN saison_id INTEGER DEFAULT 2024")
    except sqlite3.OperationalError:
        pass  # Colonne existe déjà

    try:
        cursor.execute("ALTER TABLE predictions ADD COLUMN saison_id INTEGER DEFAULT 2024")
    except sqlite3.OperationalError:
        pass  # Colonne existe déjà

    # Initialiser la saison actuelle
    saison = get_saison_actuelle()
    cursor.execute('''
        INSERT OR IGNORE INTO saisons (id, label, is_active)
        VALUES (?, ?, 1)
    ''', (saison, get_saison_label(saison)))

    # Initialiser le stock pour les utilisateurs existants (saison actuelle)
    cursor.execute('''
        INSERT OR IGNORE INTO stock_jokers (utilisateur_id, saison_id, jokers_doubles_disponibles, jokers_voles_disponibles)
        SELECT id, ?, 1, 1 FROM utilisateurs WHERE statut = 'Actif'
    ''', (saison,))

    conn.commit()
    conn.close()


def get_setting(cle):
    """Récupère un paramètre de l'application"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valeur FROM app_settings WHERE cle = ?", (cle,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def set_setting(cle, valeur):
    """Modifie un paramètre de l'application"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE app_settings SET valeur = ? WHERE cle = ?", (valeur, cle))
    conn.commit()
    conn.close()


def is_mode_officiel():
    """Vérifie si l'application est en mode officiel"""
    # Priorite: BDD > Streamlit secrets > Env > False
    db_setting = get_setting('is_officiel')
    if db_setting:
        return db_setting == 'True'

    # Verifier Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'IS_OFFICIEL' in st.secrets:
            return st.secrets['IS_OFFICIEL'] == 'True'
    except:
        pass

    # Verifier variable d'environnement
    import os
    return os.environ.get('IS_OFFICIEL', 'False') == 'True'


# ============================================
# GESTION DU STOCK DE JOKERS
# ============================================

def get_stock_jokers(utilisateur_id, saison_id=None):
    """Récupère le stock de jokers d'un utilisateur pour une saison"""
    if saison_id is None:
        saison_id = get_saison_actuelle()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT jokers_doubles_disponibles, jokers_voles_disponibles
        FROM stock_jokers
        WHERE utilisateur_id = ? AND saison_id = ?
    ''', (utilisateur_id, saison_id))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'doubles': result[0],
            'voles': result[1]
        }
    return {'doubles': 0, 'voles': 0}


def reset_jokers_nouvelle_saison(saison_id):
    """Réinitialise le stock de jokers pour une nouvelle saison"""
    conn = get_connection()
    cursor = conn.cursor()

    # Créer le stock pour tous les utilisateurs actifs
    cursor.execute('''
        INSERT OR REPLACE INTO stock_jokers
        (utilisateur_id, saison_id, jokers_doubles_disponibles, jokers_voles_disponibles)
        SELECT id, ?, 1, 1 FROM utilisateurs WHERE statut = 'Actif'
    ''', (saison_id,))

    conn.commit()
    conn.close()
    return True


def utiliser_joker_double(utilisateur_id, semaine_id):
    """Utilise un joker Points Doubles"""
    conn = get_connection()
    cursor = conn.cursor()

    # Vérifier le stock
    stock = get_stock_jokers(utilisateur_id)
    if stock['doubles'] <= 0:
        conn.close()
        return False, "Pas de joker Points Doubles disponible"

    # Décrémenter le stock
    cursor.execute('''
        UPDATE stock_jokers
        SET jokers_doubles_disponibles = jokers_doubles_disponibles - 1,
            derniere_mise_a_jour = CURRENT_TIMESTAMP
        WHERE utilisateur_id = ?
    ''', (utilisateur_id,))

    # Enregistrer dans l'historique
    cursor.execute('''
        INSERT INTO jokers_historique (utilisateur_id, semaine_id, type_joker)
        VALUES (?, ?, 'DOUBLE')
    ''', (utilisateur_id, semaine_id))

    conn.commit()
    conn.close()
    return True, "Joker Points Doubles activé!"


def utiliser_joker_vol(utilisateur_id, semaine_id, cible_id):
    """Utilise un joker Points Volés"""
    conn = get_connection()
    cursor = conn.cursor()

    # Vérifier le stock
    stock = get_stock_jokers(utilisateur_id)
    if stock['voles'] <= 0:
        conn.close()
        return False, "Pas de joker Points Volés disponible"

    # Vérifier que la cible est éligible (budget = 100, pas 140)
    eligible, msg = verifier_cible_eligible(cible_id, semaine_id)
    if not eligible:
        conn.close()
        return False, msg

    # Décrémenter le stock
    cursor.execute('''
        UPDATE stock_jokers
        SET jokers_voles_disponibles = jokers_voles_disponibles - 1,
            derniere_mise_a_jour = CURRENT_TIMESTAMP
        WHERE utilisateur_id = ?
    ''', (utilisateur_id,))

    # Enregistrer dans l'historique
    cursor.execute('''
        INSERT INTO jokers_historique (utilisateur_id, semaine_id, type_joker, cible_vol_id)
        VALUES (?, ?, 'VOL', ?)
    ''', (utilisateur_id, semaine_id, cible_id))

    conn.commit()
    conn.close()
    return True, "Joker Points Volés activé!"


def verifier_cible_eligible(cible_id, semaine_id):
    """Vérifie si une cible est éligible pour le vol (budget = 100)"""
    conn = get_connection()
    cursor = conn.cursor()

    # Calculer le budget utilisé par la cible cette semaine
    cursor.execute('''
        SELECT COALESCE(SUM(p.mise_points), 0)
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        WHERE p.user_id = ? AND m.semaine_id = ?
    ''', (cible_id, semaine_id))

    budget_utilise = cursor.fetchone()[0]
    conn.close()

    # Budget normal = 100, budget avec joker double d'une autre personne = 140
    # On n'accepte que les cibles avec budget standard
    if budget_utilise > 100:
        return False, "Cette cible a un budget modifié (140 pts)"

    return True, "Cible éligible"


def get_joker_actif_semaine(utilisateur_id, semaine_id):
    """Récupère le joker actif pour un utilisateur cette semaine"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT type_joker, cible_vol_id
        FROM jokers_historique
        WHERE utilisateur_id = ? AND semaine_id = ?
        ORDER BY date_utilisation DESC
        LIMIT 1
    ''', (utilisateur_id, semaine_id))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'type': result[0],
            'cible_id': result[1]
        }
    return None


# ============================================
# RÉSOLUTION DES CHAÎNES DE VOL (ÉTAPE 45)
# ============================================

def resoudre_chaine_vol(utilisateur_id, semaine_id, visited=None):
    """
    Résout la chaîne de vol récursive.
    Si A vole B qui vole C, retourne les pronostics de C.
    Détecte les boucles infinies.
    """
    if visited is None:
        visited = set()

    # Détection de boucle
    if utilisateur_id in visited:
        return None, "Boucle détectée dans la chaîne de vol"

    visited.add(utilisateur_id)

    # Vérifier si cet utilisateur a volé quelqu'un
    joker = get_joker_actif_semaine(utilisateur_id, semaine_id)

    if joker and joker['type'] == 'VOL' and joker['cible_id']:
        # Récursion: vérifier si la cible a aussi volé
        return resoudre_chaine_vol(joker['cible_id'], semaine_id, visited)

    # Fin de la chaîne: retourner cet utilisateur comme source des pronostics
    return utilisateur_id, "Source trouvée"


def get_pronostics_effectifs(utilisateur_id, semaine_id):
    """
    Retourne les pronostics effectifs d'un utilisateur.
    Prend en compte les vols et les chaînes de vol.
    """
    # Résoudre la chaîne de vol
    source_id, msg = resoudre_chaine_vol(utilisateur_id, semaine_id)

    if source_id is None:
        # Boucle détectée - fallback sur ses propres pronos
        source_id = utilisateur_id

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.match_id, p.score_prono_home, p.score_prono_away, p.mise_points
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        WHERE p.user_id = ? AND m.semaine_id = ?
    ''', (source_id, semaine_id))

    pronostics = cursor.fetchall()
    conn.close()

    return {
        'source_id': source_id,
        'pronostics': pronostics,
        'est_vol': source_id != utilisateur_id
    }


# ============================================
# GESTION DES MATCHS
# ============================================

def get_matchs_semaine(semaine_id):
    """Récupère les matchs d'une semaine"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, championnat, equipe_home, equipe_away,
               cote_home, cote_draw, cote_away,
               score_final_home, score_final_away, is_active
        FROM matches
        WHERE semaine_id = ?
    ''', (semaine_id,))

    matchs = cursor.fetchall()
    conn.close()
    return matchs


def tous_matchs_termines(semaine_id):
    """Vérifie si tous les matchs de la semaine sont terminés (Status FT)"""
    conn = get_connection()
    cursor = conn.cursor()

    # Compter les matchs de la semaine
    cursor.execute('''
        SELECT COUNT(*) FROM matches WHERE semaine_id = ?
    ''', (semaine_id,))
    total = cursor.fetchone()[0]

    # Compter les matchs terminés (score_final non NULL)
    cursor.execute('''
        SELECT COUNT(*) FROM matches
        WHERE semaine_id = ?
          AND score_final_home IS NOT NULL
          AND score_final_away IS NOT NULL
    ''', (semaine_id,))
    termines = cursor.fetchone()[0]

    conn.close()

    # On attend 4 matchs terminés
    return total >= 4 and termines >= 4


# ============================================
# CLASSEMENT GÉNÉRAL
# ============================================

def get_classement_general():
    """Récupère le classement général complet"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.id, u.pseudo, COALESCE(SUM(p.points_gagnes), 0) as total
        FROM utilisateurs u
        LEFT JOIN predictions p ON u.id = p.user_id
        WHERE u.statut = 'Actif'
        GROUP BY u.id, u.pseudo
        ORDER BY total DESC
    ''')

    classement = cursor.fetchall()
    conn.close()
    return classement


def get_dernier_classement():
    """Récupère le dernier du classement (pour le vol automatique)"""
    classement = get_classement_general()
    if classement:
        return classement[-1]  # (id, pseudo, total)
    return None


# ============================================
# GESTION DE L'OUBLI (ÉTAPE 48)
# ============================================

def get_utilisateurs_sans_pronostics(semaine_id):
    """Récupère les utilisateurs qui n'ont pas fait de pronostics cette semaine"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.id, u.pseudo
        FROM utilisateurs u
        WHERE u.statut = 'Actif'
          AND u.id NOT IN (
              SELECT DISTINCT p.user_id
              FROM predictions p
              JOIN matches m ON p.match_id = m.id
              WHERE m.semaine_id = ?
          )
    ''', (semaine_id,))

    oublieurs = cursor.fetchall()
    conn.close()
    return oublieurs


def trouver_cible_vol_auto(semaine_id, exclu_ids=None):
    """
    Trouve une cible éligible pour le vol automatique.
    Commence par le dernier du classement, remonte si nécessaire.
    """
    if exclu_ids is None:
        exclu_ids = set()

    classement = get_classement_general()

    # Parcourir du dernier au premier
    for user_id, pseudo, total in reversed(classement):
        if user_id in exclu_ids:
            continue

        # Vérifier si cette personne a des pronostics
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*)
            FROM predictions p
            JOIN matches m ON p.match_id = m.id
            WHERE p.user_id = ? AND m.semaine_id = ?
        ''', (user_id, semaine_id))

        nb_pronos = cursor.fetchone()[0]
        conn.close()

        if nb_pronos > 0:
            return user_id, pseudo

    return None, None


def activer_vol_automatique(utilisateur_id, semaine_id):
    """
    Active automatiquement le joker Points Volés pour un utilisateur qui a oublié.
    """
    # Trouver une cible valide
    oublieurs = get_utilisateurs_sans_pronostics(semaine_id)
    oublieur_ids = {u[0] for u in oublieurs}
    oublieur_ids.add(utilisateur_id)  # S'exclure soi-même

    cible_id, cible_pseudo = trouver_cible_vol_auto(semaine_id, oublieur_ids)

    if cible_id is None:
        return False, "Aucune cible valide trouvée"

    conn = get_connection()
    cursor = conn.cursor()

    # Enregistrer le vol automatique (sans décrémenter le stock - c'est une pénalité)
    cursor.execute('''
        INSERT INTO jokers_historique (utilisateur_id, semaine_id, type_joker, cible_vol_id)
        VALUES (?, ?, 'VOL_AUTO', ?)
    ''', (utilisateur_id, semaine_id, cible_id))

    conn.commit()
    conn.close()

    return True, f"Vol automatique activé: pronostics copiés de {cible_pseudo}"


# ============================================
# UTILITAIRES
# ============================================

def get_semaine_actuelle():
    """Retourne le numéro de la semaine actuelle"""
    return datetime.now().isocalendar()[1]


def ajouter_jokers_nouvel_utilisateur(utilisateur_id):
    """Ajoute le stock de jokers pour un nouvel utilisateur"""
    saison = get_saison_actuelle()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO stock_jokers (utilisateur_id, saison_id, jokers_doubles_disponibles, jokers_voles_disponibles)
        VALUES (?, ?, 1, 1)
    ''', (utilisateur_id, saison))

    conn.commit()
    conn.close()


# ============================================
# GESTION J1 ET COUNTDOWN
# ============================================

def get_date_j1(saison_id=None):
    """Récupère la date du premier match de la J1 de la saison"""
    if saison_id is None:
        saison_id = get_saison_actuelle()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT MIN(date_match) FROM matches
        WHERE saison_id = ? AND semaine_id = 1
    ''', (saison_id,))

    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        return datetime.fromisoformat(result[0].replace('Z', '+00:00'))
    return None


def get_date_ouverture_inscriptions(saison_id=None):
    """Retourne la date d'ouverture des inscriptions (J1 - 30 jours)"""
    date_j1 = get_date_j1(saison_id)
    if date_j1:
        return date_j1 - timedelta(days=30)
    return None


def inscriptions_ouvertes(saison_id=None):
    """Vérifie si les inscriptions sont ouvertes"""
    date_ouverture = get_date_ouverture_inscriptions(saison_id)
    if date_ouverture is None:
        return True  # Pas de J1 définie = mode test
    return datetime.now() >= date_ouverture


def get_countdown_j1(saison_id=None):
    """Retourne le temps restant avant la J1"""
    date_j1 = get_date_j1(saison_id)
    if date_j1 is None:
        return None

    now = datetime.now()
    if now >= date_j1:
        return {'days': 0, 'hours': 0, 'minutes': 0, 'passed': True}

    delta = date_j1 - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'passed': False,
        'date_j1': date_j1.strftime('%d/%m/%Y %H:%M')
    }


def get_utilisateurs_emails():
    """Récupère tous les utilisateurs avec leur email"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, pseudo, prenom, email FROM utilisateurs
        WHERE statut = 'Actif' AND email IS NOT NULL AND email != ''
    ''')

    users = cursor.fetchall()
    conn.close()

    return [{'id': u[0], 'pseudo': u[1], 'prenom': u[2], 'email': u[3]} for u in users]


def get_utilisateurs_sans_pronos_j1(saison_id=None):
    """Récupère les utilisateurs qui n'ont pas validé leurs pronos pour la J1"""
    if saison_id is None:
        saison_id = get_saison_actuelle()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.id, u.pseudo, u.prenom, u.email
        FROM utilisateurs u
        WHERE u.statut = 'Actif'
          AND u.email IS NOT NULL
          AND u.id NOT IN (
              SELECT DISTINCT p.user_id
              FROM predictions p
              JOIN matches m ON p.match_id = m.id
              WHERE m.saison_id = ? AND m.semaine_id = 1
          )
    ''', (saison_id,))

    users = cursor.fetchall()
    conn.close()

    return [{'id': u[0], 'pseudo': u[1], 'prenom': u[2], 'email': u[3]} for u in users]
