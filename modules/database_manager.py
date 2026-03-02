"""
Database Manager pour Elite Pronos
Gestion centralisée de la base de données, saisons et jokers
Phase Finale: Support pluriannuel et automatisation
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')


def _get_football_api_token():
    """Recupere le token football-data.org depuis les secrets."""
    try:
        import streamlit as st
        return st.secrets.get("FOOTBALL_API_TOKEN", os.getenv("FOOTBALL_API_TOKEN", ""))
    except Exception:
        return os.getenv("FOOTBALL_API_TOKEN", "")

# Creer le dossier database s'il n'existe pas
DB_DIR = os.path.dirname(DB_PATH)
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)


# ============================================
# CONFIGURATION CALENDRIER LFP
# ============================================

# Calendrier officiel Ligue 1 par saison
# Format: {saison_id: {'debut': (mois, jour), 'fin': (mois, jour)}}
CALENDRIER_LFP = {
    2024: {'debut': (8, 16), 'fin': (5, 18)},   # 2024-2025
    2025: {'debut': (8, 15), 'fin': (5, 23)},   # 2025-2026
    2026: {'debut': (8, 23), 'fin': (5, 29)},   # 2026-2027 (demandé)
    2027: {'debut': (8, 13), 'fin': (5, 21)},   # 2027-2028 (estimation)
}

# Parametres de chronologie
JOURS_OUVERTURE_INSCRIPTIONS = 30  # J-30 avant debut championnat
JOURS_OUVERTURE_PRONOSTICS = 5     # J-5 avant chaque journee

# ============================================
# CONFIGURATION SAISON FORCEE
# ============================================
# Mettre a None pour detection automatique, ou forcer une saison specifique
SAISON_FORCEE = 2025  # Force la saison 2025-2026 (Phase Test)


# ============================================
# GESTION DES SAISONS
# ============================================

def get_saison_actuelle():
    """
    Retourne l'ID de la saison actuelle (ex: 2026 pour 2026-2027).
    Si SAISON_FORCEE est defini, utilise cette valeur.
    Sinon, detection automatique basee sur le calendrier LFP.
    Cache 1h (change 1x/an).
    """
    try:
        import streamlit as st
        @st.cache_data(ttl=3600)
        def _get():
            return _get_saison_actuelle_impl()
        return _get()
    except Exception:
        return _get_saison_actuelle_impl()


def _get_saison_actuelle_impl():
    """Implementation sans cache de get_saison_actuelle"""
    # Si une saison est forcee, l'utiliser
    if SAISON_FORCEE is not None:
        return SAISON_FORCEE

    now = datetime.now()

    # Chercher la saison active dans le calendrier
    for saison_id, dates in CALENDRIER_LFP.items():
        debut_mois, debut_jour = dates['debut']
        fin_mois, fin_jour = dates['fin']

        # Date de debut de la saison
        date_debut = datetime(saison_id, debut_mois, debut_jour)
        # Date de fin de la saison (annee suivante)
        date_fin = datetime(saison_id + 1, fin_mois, fin_jour)

        if date_debut <= now <= date_fin:
            return saison_id

    # Fallback: logique standard (aout = nouvelle saison)
    if now.month >= 8:
        return now.year
    return now.year - 1


def get_saison_label(saison_id):
    """Retourne le label de la saison (ex: '2026-2027')"""
    return f"{saison_id}-{saison_id + 1}"


def get_dates_saison(saison_id=None):
    """
    Retourne les dates officielles de debut et fin de saison.
    Basé sur le calendrier LFP.
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    if saison_id in CALENDRIER_LFP:
        dates = CALENDRIER_LFP[saison_id]
        debut = datetime(saison_id, dates['debut'][0], dates['debut'][1], 21, 0)  # 21h
        fin = datetime(saison_id + 1, dates['fin'][0], dates['fin'][1], 21, 0)
        return {'debut': debut, 'fin': fin}

    # Fallback: estimation standard (mi-aout a mi-mai)
    return {
        'debut': datetime(saison_id, 8, 15, 21, 0),
        'fin': datetime(saison_id + 1, 5, 20, 21, 0)
    }


def detecter_nouvelle_saison():
    """
    Detecte automatiquement si une nouvelle saison doit etre initialisee.
    A appeler au demarrage de l'application.
    """
    saison_actuelle = get_saison_actuelle()

    conn = get_connection()
    cursor = conn.cursor()

    # Verifier si la saison existe dans la BDD
    cursor.execute("SELECT id FROM saisons WHERE id = ?", (saison_actuelle,))
    existe = cursor.fetchone()

    if not existe:
        # Nouvelle saison detectee - initialiser
        dates = get_dates_saison(saison_actuelle)
        cursor.execute('''
            INSERT INTO saisons (id, label, date_debut, date_fin, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (saison_actuelle, get_saison_label(saison_actuelle),
              dates['debut'].strftime('%Y-%m-%d'),
              dates['fin'].strftime('%Y-%m-%d')))

        # Desactiver les anciennes saisons
        cursor.execute("UPDATE saisons SET is_active = 0 WHERE id != ?", (saison_actuelle,))

        # Reinitialiser les jokers pour tous les utilisateurs
        # Quota règlement: 3 Jokers Points Doubles + 2 Jokers Points Volés par saison
        cursor.execute('''
            INSERT OR IGNORE INTO stock_jokers (utilisateur_id, saison_id, jokers_doubles_disponibles, jokers_voles_disponibles)
            SELECT id, ?, 3, 2 FROM utilisateurs WHERE statut = 'Actif'
        ''', (saison_actuelle,))

        conn.commit()
        conn.close()
        return True, f"Nouvelle saison {get_saison_label(saison_actuelle)} initialisee"

    conn.close()
    return False, "Saison deja initialisee"


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
                    jokers_doubles_disponibles INTEGER DEFAULT 3,
                    jokers_voles_disponibles INTEGER DEFAULT 2,
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
                jokers_doubles_disponibles INTEGER DEFAULT 3,
                jokers_voles_disponibles INTEGER DEFAULT 2,
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

    # Migration: Ajouter colonne is_admin aux utilisateurs
    try:
        cursor.execute("ALTER TABLE utilisateurs ADD COLUMN is_admin BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Colonne existe déjà

    # Migration: Ajouter colonne parrain (qui vous a recommande)
    try:
        cursor.execute("ALTER TABLE utilisateurs ADD COLUMN parrain TEXT")
    except sqlite3.OperationalError:
        pass  # Colonne existe déjà

    # S'assurer que Baggio est admin
    cursor.execute("UPDATE utilisateurs SET is_admin = 1 WHERE pseudo = 'baggio'")

    # Initialiser la saison actuelle
    saison = get_saison_actuelle()
    cursor.execute('''
        INSERT OR IGNORE INTO saisons (id, label, is_active)
        VALUES (?, ?, 1)
    ''', (saison, get_saison_label(saison)))

    # Initialiser le stock pour les utilisateurs existants (saison actuelle)
    cursor.execute('''
        INSERT OR IGNORE INTO stock_jokers (utilisateur_id, saison_id, jokers_doubles_disponibles, jokers_voles_disponibles)
        SELECT id, ?, 3, 2 FROM utilisateurs WHERE statut = 'Actif'
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
    # Priorite: Streamlit secrets > Env > False
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'IS_OFFICIEL' in st.secrets:
            return st.secrets['IS_OFFICIEL'] == 'True'
    except:
        pass

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
    # Quota règlement: 3 Jokers Points Doubles + 2 Jokers Points Volés par saison
    cursor.execute('''
        INSERT OR REPLACE INTO stock_jokers
        (utilisateur_id, saison_id, jokers_doubles_disponibles, jokers_voles_disponibles)
        SELECT id, ?, 3, 2 FROM utilisateurs WHERE statut = 'Actif'
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
    try:
        from modules.supabase_db import get_supabase
        supabase = get_supabase()

        result = supabase._request('GET',
            f'jokers_historique?utilisateur_id=eq.{utilisateur_id}&semaine_id=eq.{semaine_id}&select=type_joker,cible_vol_id&order=date_utilisation.desc&limit=1'
        )

        if result and len(result) > 0:
            return {
                'type': result[0].get('type_joker'),
                'cible_id': result[0].get('cible_vol_id')
            }
        return None

    except Exception as e:
        print(f"Erreur get_joker_actif_semaine: {e}")
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

def get_mvp_semaine(semaine_id, saison_id=None):
    """
    Retourne le MVP (meilleur joueur) d'une semaine donnee. Cache 60s.
    Retourne: dict {'user_id', 'pseudo', 'points_journee'} ou None
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    try:
        import streamlit as st
        @st.cache_data(ttl=60)
        def _fetch(semaine_id, saison_id):
            return _get_mvp_semaine_impl(semaine_id, saison_id)
        return _fetch(semaine_id, saison_id)
    except Exception:
        return _get_mvp_semaine_impl(semaine_id, saison_id)


def _get_mvp_semaine_impl(semaine_id, saison_id):
    """Implementation sans cache"""
    from modules.supabase_db import get_supabase

    try:
        supabase = get_supabase()

        # Recuperer les matchs de la semaine
        matchs = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,score_final_home'
        ) or []

        if not matchs:
            return None

        # Verifier qu'au moins un match est termine
        matchs_termines = [m for m in matchs if m.get('score_final_home') is not None]
        if not matchs_termines:
            return None

        match_ids = [m['id'] for m in matchs]
        match_ids_str = ','.join(map(str, match_ids))

        # Recuperer toutes les predictions avec points
        predictions = supabase._request('GET',
            f'predictions?match_id=in.({match_ids_str})&points_gagnes=not.is.null&select=user_id,points_gagnes,utilisateurs(pseudo)'
        ) or []

        if not predictions:
            return None

        # Agreger par joueur
        joueurs_pts = {}
        for p in predictions:
            uid = p['user_id']
            pseudo = p['utilisateurs']['pseudo'] if p.get('utilisateurs') else 'Inconnu'
            if uid not in joueurs_pts:
                joueurs_pts[uid] = {'user_id': uid, 'pseudo': pseudo, 'points_journee': 0}
            joueurs_pts[uid]['points_journee'] += p.get('points_gagnes') or 0

        if not joueurs_pts:
            return None

        # Trouver le meilleur
        mvp = max(joueurs_pts.values(), key=lambda x: x['points_journee'])
        return mvp

    except Exception as e:
        print(f"Erreur get_mvp_semaine: {e}")
        return None


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


def get_kingo_user_id():
    """Retourne l'ID de Kingo (le bot)"""
    from modules.supabase_db import get_supabase
    supabase = get_supabase()
    result = supabase._request('GET', 'utilisateurs?pseudo=eq.Kingo&select=id')
    if result and len(result) > 0:
        return result[0]['id']
    return None


def appliquer_vol_auto_oublis(semaine_id, saison_id=None):
    """
    Pour tous les joueurs qui ont oublie leurs pronos:
    - Si joker VOL disponible : consomme 1 joker VOL, copie les pronos de Kingo
    - Si plus de joker VOL : penalite de -25 pts par match manquant (max -100)

    A appeler juste apres la deadline (avant le 1er match).
    Retourne la liste des joueurs traites.
    """
    from modules.supabase_db import get_supabase

    if saison_id is None:
        saison_id = get_saison_actuelle()

    supabase = get_supabase()
    traites = []

    try:
        # Recuperer l'ID de Kingo
        kingo_id = get_kingo_user_id()
        if not kingo_id:
            return [], "Kingo introuvable"

        # Recuperer TOUS les matchs de la semaine (pas seulement is_active=true)
        # car apres validation, is_active passe a False
        matchs = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id'
        ) or []
        all_match_ids = [m['id'] for m in matchs]

        if not all_match_ids:
            return [], "Pas de matchs pour cette semaine"

        all_match_ids_str = ','.join(map(str, all_match_ids))

        # Recuperer les pronos de Kingo pour determiner les matchs actifs
        # Kingo pronostique toujours sur TOUS les matchs actifs
        # => ses predictions definissent les matchs sur lesquels les joueurs devaient pronostiquer
        kingo_pronos = supabase._request('GET',
            f'predictions?user_id=eq.{kingo_id}&match_id=in.({all_match_ids_str})&select=match_id,score_prono_home,score_prono_away,mise_points'
        ) or []

        if not kingo_pronos:
            return [], "Kingo n'a pas de pronos"

        # Les matchs actifs = ceux sur lesquels Kingo a pronostique
        kingo_pronos_map = {p['match_id']: p for p in kingo_pronos}
        match_ids = list(kingo_pronos_map.keys())
        match_ids_str = ','.join(map(str, match_ids))

        # Recuperer tous les utilisateurs actifs (sauf Kingo)
        users = supabase._request('GET',
            f'utilisateurs?statut=eq.Actif&id=neq.{kingo_id}&select=id,pseudo'
        ) or []

        # Recuperer toutes les predictions existantes pour cette semaine
        existing_preds = supabase._request('GET',
            f'predictions?match_id=in.({match_ids_str})&select=user_id,match_id'
        ) or []

        # Compter les pronos par user
        pronos_par_user = {}
        for p in existing_preds:
            uid = p['user_id']
            pronos_par_user[uid] = pronos_par_user.get(uid, 0) + 1

        nb_matchs = len(match_ids)

        # Trouver les joueurs qui n'ont pas fait TOUS leurs pronos
        for user in users:
            user_id = user['id']
            pseudo = user['pseudo']
            nb_pronos = pronos_par_user.get(user_id, 0)

            if nb_pronos < nb_matchs:
                # Ce joueur a oublie (tout ou partie)

                # Verifier s'il a encore des jokers VOL
                stock = supabase._request('GET',
                    f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}&select=joker_vol'
                ) or []

                jokers_vol_dispo = stock[0].get('joker_vol', 0) if stock else 0

                if jokers_vol_dispo > 0:
                    # Consommer 1 joker VOL
                    supabase._request('PATCH',
                        f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}',
                        {'joker_vol': jokers_vol_dispo - 1}
                    )

                    # Supprimer tout doublon eventuel avant insertion
                    supabase._request('DELETE', f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{semaine_id}')
                    # Enregistrer le VOL automatique sur Kingo
                    supabase._request('POST', 'jokers_historique', {
                        'utilisateur_id': user_id,
                        'semaine_id': semaine_id,
                        'saison_id': saison_id,
                        'type_joker': 'VOL',
                        'cible_vol_id': kingo_id
                    })

                    # Copier les pronos manquants de Kingo
                    for match_id in match_ids:
                        # Verifier si le joueur a deja un prono pour ce match
                        existing = supabase._request('GET',
                            f'predictions?user_id=eq.{user_id}&match_id=eq.{match_id}&select=id'
                        ) or []

                        if not existing:
                            # Copier le prono de Kingo
                            kingo_p = kingo_pronos_map.get(match_id)
                            if kingo_p:
                                supabase._request('POST', 'predictions', {
                                    'user_id': user_id,
                                    'match_id': match_id,
                                    'saison_id': saison_id,
                                    'score_prono_home': kingo_p['score_prono_home'],
                                    'score_prono_away': kingo_p['score_prono_away'],
                                    'mise_points': kingo_p['mise_points']
                                })

                    traites.append({
                        'user_id': user_id,
                        'pseudo': pseudo,
                        'pronos_manquants': nb_matchs - nb_pronos,
                        'jokers_restants': jokers_vol_dispo - 1,
                        'action': 'VOL_AUTO_KINGO'
                    })
                else:
                    # Plus de joker VOL = penalite -25 pts par match manquant (max -100)
                    # Inserer des predictions penalite avec points_gagnes pre-fixes
                    # calcul_gains_semaine les skippera car points_gagnes != None
                    nb_inserted = 0
                    for match_id in match_ids:
                        existing = supabase._request('GET',
                            f'predictions?user_id=eq.{user_id}&match_id=eq.{match_id}&select=id'
                        ) or []
                        if not existing:
                            supabase._request('POST', 'predictions', {
                                'user_id': user_id,
                                'match_id': match_id,
                                'saison_id': saison_id,
                                'score_prono_home': 0,
                                'score_prono_away': 0,
                                'mise_points': 25,
                                'points_gagnes': -25
                            })
                            nb_inserted += 1
                    traites.append({
                        'user_id': user_id,
                        'pseudo': pseudo,
                        'pronos_manquants': nb_matchs - nb_pronos,
                        'jokers_restants': 0,
                        'action': f'PENALITE_{nb_inserted * 25}'
                    })

        return traites, f"{len(traites)} joueur(s) traite(s)"

    except Exception as e:
        return [], str(e)


# ============================================
# DEFIS HEBDOMADAIRES — ATTRIBUTION JOKERS VOL
# ============================================

def attribuer_jokers_defis(semaine_id, saison_id=None):
    """
    Si un joueur reussit les 3 defis dans la meme semaine,
    il remporte +1 joker VOL (defi_numero=0 dans defis_recompenses).
    Sans doublon : une seule attribution par joueur par semaine.
    Retourne la liste des attributions effectuees.
    """
    from modules.supabase_db import get_supabase

    if saison_id is None:
        saison_id = get_saison_actuelle()

    supabase = get_supabase()
    attributions = []

    try:
        # Recuperer les matchs actifs de la semaine
        matchs = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&is_active=eq.true&select=id'
        ) or []
        match_ids = [m['id'] for m in matchs]
        if not match_ids:
            return [], "Aucun match actif pour cette semaine"

        match_ids_str = ','.join(map(str, match_ids))

        # Recuperer tous les utilisateurs actifs (sauf Kingo)
        kingo_id = get_kingo_user_id()
        users = supabase._request('GET',
            f'utilisateurs?statut=eq.Actif&id=neq.{kingo_id}&select=id,pseudo'
        ) or []

        # Recuperer toutes les predictions de la semaine avec details
        preds = supabase._request('GET',
            f'predictions?match_id=in.({match_ids_str})&select=user_id,mise_points,points_gagnes,is_score_exact'
        ) or []

        # Agréger par joueur
        stats = {}
        for p in preds:
            uid = p['user_id']
            if uid not in stats:
                stats[uid] = {'total': 0, 'nb_exacts': 0, 'details': []}
            pts = p.get('points_gagnes') or 0
            stats[uid]['total'] += pts
            if p.get('is_score_exact'):
                stats[uid]['nb_exacts'] += 1
            stats[uid]['details'].append({
                'mise': p.get('mise_points') or 0,
                'points_gagnes': pts
            })

        # Recuperer les joueurs deja recompenses cette semaine (defi_numero=0)
        deja_recompenses = supabase._request('GET',
            f'defis_recompenses?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&defi_numero=eq.0&select=user_id'
        ) or []
        deja_set = {r['user_id'] for r in deja_recompenses}

        for user in users:
            uid = user['id']
            pseudo = user['pseudo']
            s = stats.get(uid, {'total': 0, 'nb_exacts': 0, 'details': []})

            # Les 3 defis doivent tous etre reussis
            defi1_ok = s['total'] >= 200
            defi2_ok = s['nb_exacts'] >= 2
            defi3_ok = any(d['mise'] >= 40 and d['points_gagnes'] > 0 for d in s['details'])

            if not (defi1_ok and defi2_ok and defi3_ok):
                continue  # Pas le triple

            if uid in deja_set:
                continue  # Deja recompense cette semaine

            # Enregistrer la recompense (defi_numero=0 = triple accompli)
            supabase._request('POST', 'defis_recompenses', {
                'user_id': uid,
                'semaine_id': semaine_id,
                'saison_id': saison_id,
                'defi_numero': 0
            })

            # Attribuer +1 joker VOL
            stock = supabase._request('GET',
                f'stock_jokers?utilisateur_id=eq.{uid}&saison_id=eq.{saison_id}&select=joker_vol'
            ) or []
            jokers_vol_actuel = stock[0].get('joker_vol', 0) if stock else 0
            supabase._request('PATCH',
                f'stock_jokers?utilisateur_id=eq.{uid}&saison_id=eq.{saison_id}',
                {'joker_vol': jokers_vol_actuel + 1}
            )

            attributions.append({
                'pseudo': pseudo,
                'defi': 'Triple (3/3 defis)',
                'defi_numero': 0,
                'jokers_vol_nouveau': jokers_vol_actuel + 1
            })

        return attributions, f"{len(attributions)} joker(s) VOL attribue(s)"

    except Exception as e:
        return [], str(e)


# ============================================
# UTILITAIRES
# ============================================

def get_semaine_actuelle():
    """Retourne le numéro de la semaine actuelle"""
    return datetime.now().isocalendar()[1]


def ajouter_jokers_nouvel_utilisateur(utilisateur_id):
    """Ajoute le stock de jokers pour un nouvel utilisateur"""
    # Quota règlement: 3 Jokers Points Doubles + 2 Jokers Points Volés par saison
    saison = get_saison_actuelle()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO stock_jokers (utilisateur_id, saison_id, jokers_doubles_disponibles, jokers_voles_disponibles)
        VALUES (?, ?, 3, 2)
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

    date_str = None

    # Essayer Supabase d'abord (pour Streamlit Cloud)
    try:
        from modules.supabase_db import get_supabase
        supabase = get_supabase()
        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.1&select=date_match&order=date_match&limit=1'
        )
        if matchs and len(matchs) > 0:
            date_str = matchs[0].get('date_match')
    except Exception:
        pass

    if date_str:
        try:
            # Essayer de parser la date ISO
            date_str = date_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(date_str)
            # Convertir en datetime naive (sans timezone) pour comparaison
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except (ValueError, AttributeError):
            # Fallback: essayer format standard
            try:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except:
                return None
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


def get_matchs_journee_cached(saison_id, semaine_id):
    """Recupere les matchs d'une journee avec cache 30s"""
    try:
        import streamlit as st
        @st.cache_data(ttl=30)
        def _fetch(saison_id, semaine_id):
            from modules.supabase_db import get_supabase
            return get_supabase().get_matches_journee(saison_id, semaine_id)
        return _fetch(saison_id, semaine_id)
    except Exception:
        from modules.supabase_db import get_supabase
        return get_supabase().get_matches_journee(saison_id, semaine_id)


def get_is_admin_cached(user_id):
    """Verifie is_admin avec cache 5 min (change rarement)"""
    try:
        import streamlit as st
        return _fetch_is_admin(user_id)
    except Exception:
        return _fetch_is_admin_raw(user_id)


def _fetch_is_admin_raw(user_id):
    """Requete directe sans cache"""
    from modules.supabase_db import get_supabase
    r = get_supabase()._request('GET', f'utilisateurs?id=eq.{user_id}&select=is_admin')
    return bool(r and r[0].get('is_admin'))


try:
    import streamlit as st
    @st.cache_data(ttl=300)
    def _fetch_is_admin(user_id):
        return _fetch_is_admin_raw(user_id)
except Exception:
    def _fetch_is_admin(user_id):
        return _fetch_is_admin_raw(user_id)


def get_user_predictions_cached(user_id, saison_id, journee_courante, match_ids_str):
    """Recupere les predictions d'un user pour une journee avec cache 15s"""
    try:
        import streamlit as st
        @st.cache_data(ttl=15)
        def _fetch(user_id, saison_id, journee_courante, match_ids_str):
            from modules.supabase_db import get_supabase
            return get_supabase()._request('GET',
                f'predictions?user_id=eq.{user_id}&select=match_id,score_prono_home,score_prono_away,mise_points,mise_bonus_gc,points_gagnes,matches(id,equipe_home,equipe_away,semaine_id,saison_id,score_final_home,score_final_away,cote_home,cote_draw,cote_away)&matches.saison_id=eq.{saison_id}&matches.semaine_id=eq.{journee_courante}'
            ) or []
        return _fetch(user_id, saison_id, journee_courante, match_ids_str)
    except Exception:
        from modules.supabase_db import get_supabase
        return get_supabase()._request('GET',
            f'predictions?user_id=eq.{user_id}&select=match_id,score_prono_home,score_prono_away,mise_points,mise_bonus_gc,points_gagnes,matches(id,equipe_home,equipe_away,semaine_id,saison_id,score_final_home,score_final_away,cote_home,cote_draw,cote_away)&matches.saison_id=eq.{saison_id}&matches.semaine_id=eq.{journee_courante}'
        ) or []


def get_rivaux_ids_cached(user_id):
    """Recupere les IDs des rivaux avec cache 60s"""
    try:
        import streamlit as st
        @st.cache_data(ttl=60)
        def _fetch(user_id):
            from modules.supabase_db import get_supabase
            return get_supabase().get_rivaux_ids(user_id)
        return _fetch(user_id)
    except Exception:
        from modules.supabase_db import get_supabase
        return get_supabase().get_rivaux_ids(user_id)


def get_rivaux_predictions_cached(rivaux_ids_str, match_ids_str, journee_courante):
    """Recupere les predictions des rivaux avec cache 15s"""
    try:
        import streamlit as st
        @st.cache_data(ttl=15)
        def _fetch(rivaux_ids_str, match_ids_str, journee_courante):
            from modules.supabase_db import get_supabase
            sb = get_supabase()
            predictions = sb._request('GET',
                f'predictions?match_id=in.({match_ids_str})&user_id=in.({rivaux_ids_str})&select=user_id,score_prono_home,score_prono_away,mise_points,mise_bonus_gc,points_gagnes,matches(equipe_home,equipe_away,score_final_home,score_final_away,date_match,cote_home,cote_draw,cote_away),utilisateurs(id,pseudo)'
            ) or []
            jokers = sb._request('GET',
                f'jokers_historique?utilisateur_id=in.({rivaux_ids_str})&semaine_id=eq.{journee_courante}&select=utilisateur_id,type_joker'
            ) or []
            return {'predictions': predictions, 'jokers': jokers}
        return _fetch(rivaux_ids_str, match_ids_str, journee_courante)
    except Exception:
        from modules.supabase_db import get_supabase
        sb = get_supabase()
        predictions = sb._request('GET',
            f'predictions?match_id=in.({match_ids_str})&user_id=in.({rivaux_ids_str})&select=user_id,score_prono_home,score_prono_away,mise_points,mise_bonus_gc,points_gagnes,matches(equipe_home,equipe_away,score_final_home,score_final_away,date_match,cote_home,cote_draw,cote_away),utilisateurs(id,pseudo)'
        ) or []
        jokers = sb._request('GET',
            f'jokers_historique?utilisateur_id=in.({rivaux_ids_str})&semaine_id=eq.{journee_courante}&select=utilisateur_id,type_joker'
        ) or []
        return {'predictions': predictions, 'jokers': jokers}


def get_user_joker_cached(user_id, journee_courante):
    """Recupere le joker d'un user pour une journee avec cache 15s"""
    try:
        import streamlit as st
        @st.cache_data(ttl=15)
        def _fetch(user_id, journee_courante):
            from modules.supabase_db import get_supabase
            return get_supabase()._request('GET',
                f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{journee_courante}&select=type_joker&limit=1'
            ) or []
        return _fetch(user_id, journee_courante)
    except Exception:
        from modules.supabase_db import get_supabase
        return get_supabase()._request('GET',
            f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{journee_courante}&select=type_joker&limit=1'
        ) or []


def get_recap_data_cached(match_ids_str, journee_courante):
    """Recupere les donnees du recap avec cache 30s"""
    try:
        import streamlit as st
        @st.cache_data(ttl=30)
        def _fetch(match_ids_str, journee_courante):
            from modules.supabase_db import get_supabase
            sb = get_supabase()
            preds = sb._request('GET',
                f'predictions?match_id=in.({match_ids_str})&select=user_id,match_id,score_prono_home,score_prono_away,mise_points'
            ) or []
            users = sb._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo') or []
            jokers = sb._request('GET',
                f'jokers_historique?semaine_id=eq.{journee_courante}&select=utilisateur_id,type_joker'
            ) or []
            return {'preds': preds, 'users': users, 'jokers': jokers}
        return _fetch(match_ids_str, journee_courante)
    except Exception:
        from modules.supabase_db import get_supabase
        sb = get_supabase()
        preds = sb._request('GET',
            f'predictions?match_id=in.({match_ids_str})&select=user_id,match_id,score_prono_home,score_prono_away,mise_points'
        ) or []
        users = sb._request('GET', 'utilisateurs?statut=eq.Actif&select=id,pseudo') or []
        jokers = sb._request('GET',
            f'jokers_historique?semaine_id=eq.{journee_courante}&select=utilisateur_id,type_joker'
        ) or []
        return {'preds': preds, 'users': users, 'jokers': jokers}


def get_countdown_pronostics_journee_cached(semaine_id, saison_id):
    """Countdown avec cache 10s"""
    try:
        import streamlit as st
        @st.cache_data(ttl=10)
        def _fetch(semaine_id, saison_id):
            return get_countdown_pronostics_journee(semaine_id, saison_id)
        return _fetch(semaine_id, saison_id)
    except Exception:
        return get_countdown_pronostics_journee(semaine_id, saison_id)


# ============================================
# CHRONOLOGIE PRONOSTICS (J-5)
# ============================================

def get_date_premiere_journee(semaine_id, saison_id=None):
    """Retourne la date du premier match d'une journee. Cache 5 min."""
    if saison_id is None:
        saison_id = get_saison_actuelle()

    try:
        import streamlit as st
        @st.cache_data(ttl=300)
        def _fetch(semaine_id, saison_id):
            return _get_date_premiere_journee_impl(semaine_id, saison_id)
        return _fetch(semaine_id, saison_id)
    except Exception:
        return _get_date_premiere_journee_impl(semaine_id, saison_id)


def _get_date_premiere_journee_impl(semaine_id, saison_id):
    """Implementation sans cache"""
    date_str = None

    try:
        from modules.supabase_db import get_supabase
        supabase = get_supabase()
        matchs = supabase._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{semaine_id}&select=date_match&order=date_match&limit=1'
        )
        if matchs and len(matchs) > 0:
            date_str = matchs[0].get('date_match')
    except Exception:
        pass

    if date_str:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except:
                return None
    return None


def get_date_ouverture_pronostics(semaine_id, saison_id=None):
    """Retourne la date d'ouverture des pronostics pour une journee (J-5)"""
    date_journee = get_date_premiere_journee(semaine_id, saison_id)
    if date_journee:
        return date_journee - timedelta(days=JOURS_OUVERTURE_PRONOSTICS)
    return None


def pronostics_ouverts(semaine_id, saison_id=None):
    """
    Verifie si les pronostics sont ouverts pour une journee.
    Ouverts J-5 avant la journee, fermes 1h avant le premier match.
    """
    date_ouverture = get_date_ouverture_pronostics(semaine_id, saison_id)
    date_journee = get_date_premiere_journee(semaine_id, saison_id)

    if date_ouverture is None or date_journee is None:
        return True  # Mode test - toujours ouvert

    now = datetime.now()
    date_fermeture = date_journee - timedelta(hours=1)

    return date_ouverture <= now < date_fermeture


def get_countdown_pronostics_journee(semaine_id, saison_id=None):
    """Retourne le temps restant avant fermeture des pronostics"""
    date_journee = get_date_premiere_journee(semaine_id, saison_id)

    if date_journee is None:
        return None

    now = datetime.now()
    date_fermeture = date_journee - timedelta(hours=1)

    if now >= date_fermeture:
        return {'expired': True, 'days': 0, 'hours': 0, 'minutes': 0}

    delta = date_fermeture - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    return {
        'expired': False,
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'date_fermeture': date_fermeture.strftime('%d/%m/%Y %H:%M')
    }


def get_journee_courante(saison_id=None):
    """
    Retourne le numero de la journee courante.
    Utilise Supabase. Cache 5 min (change rarement).
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    return _get_journee_courante_cached(saison_id)


def _get_journee_courante_cached(saison_id):
    """Version cachee (import st local pour eviter dependance top-level)"""
    import streamlit as st

    @st.cache_data(ttl=300)
    def _fetch(saison_id):
        from modules.supabase_db import get_supabase
        supabase = get_supabase()
        try:
            saisons = supabase._request('GET', f'saisons?annee_debut=eq.{saison_id}&select=journee_courante')
            if saisons and len(saisons) > 0:
                return saisons[0].get('journee_courante', 1)
            saisons = supabase._request('GET', 'saisons?is_active=eq.true&select=journee_courante')
            if saisons and len(saisons) > 0:
                return saisons[0].get('journee_courante', 1)
        except Exception:
            pass
        return 1

    return _fetch(saison_id)


# ============================================
# MISE A JOUR HEBDOMADAIRE CALENDRIER
# ============================================

def mettre_a_jour_calendrier_reports(saison_id=None):
    """
    Met a jour le calendrier pour gerer les matchs reportes.
    Appelle l'API Football-Data pour verifier les changements de dates.
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    try:
        import requests

        API_TOKEN = _get_football_api_token()
        headers = {'X-Auth-Token': API_TOKEN}

        url = f'https://api.football-data.org/v4/competitions/FL1/matches?season={saison_id}'
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return False, f"Erreur API: {response.status_code}"

        data = response.json()
        matchs_api = data.get('matches', [])

        conn = get_connection()
        cursor = conn.cursor()

        updates = 0
        for m in matchs_api:
            nouvelle_date = m.get('utcDate')
            home = m.get('homeTeam', {}).get('name')
            away = m.get('awayTeam', {}).get('name')
            statut = m.get('status')

            if statut == 'POSTPONED':
                # Match reporte - marquer comme inactif
                cursor.execute('''
                    UPDATE matches SET is_active = 0
                    WHERE equipe_home = ? AND equipe_away = ? AND saison_id = ?
                ''', (home, away, saison_id))
                updates += 1
            elif nouvelle_date:
                # Mettre a jour la date si differente
                cursor.execute('''
                    UPDATE matches SET date_match = ?
                    WHERE equipe_home = ? AND equipe_away = ? AND saison_id = ?
                    AND date_match != ?
                ''', (nouvelle_date, home, away, saison_id, nouvelle_date))
                if cursor.rowcount > 0:
                    updates += 1

        conn.commit()
        conn.close()

        return True, f"{updates} mise(s) a jour effectuee(s)"

    except Exception as e:
        return False, str(e)


def valider_resultats_journee(semaine_id, saison_id=None):
    """
    Fige les scores d'une journee apres validation admin.
    Met a jour les scores finaux depuis l'API.
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    try:
        import requests

        API_TOKEN = _get_football_api_token()
        headers = {'X-Auth-Token': API_TOKEN}

        conn = get_connection()
        cursor = conn.cursor()

        # Recuperer les matchs de la journee
        cursor.execute('''
            SELECT id, equipe_home, equipe_away FROM matches
            WHERE semaine_id = ? AND saison_id = ?
        ''', (semaine_id, saison_id))

        matchs_db = cursor.fetchall()

        # Appeler l'API pour les scores
        url = f'https://api.football-data.org/v4/competitions/FL1/matches?season={saison_id}&matchday={semaine_id}'
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            conn.close()
            return False, f"Erreur API: {response.status_code}"

        data = response.json()
        matchs_api = data.get('matches', [])

        # Creer un dictionnaire pour lookup rapide
        scores_api = {}
        for m in matchs_api:
            home = m.get('homeTeam', {}).get('name')
            away = m.get('awayTeam', {}).get('name')
            score = m.get('score', {}).get('fullTime', {})
            if score.get('home') is not None:
                scores_api[(home, away)] = (score['home'], score['away'])

        # Mettre a jour les scores dans la BDD
        updates = 0
        for match_id, home, away in matchs_db:
            if (home, away) in scores_api:
                score_h, score_a = scores_api[(home, away)]
                cursor.execute('''
                    UPDATE matches SET score_final_home = ?, score_final_away = ?, is_active = 0
                    WHERE id = ?
                ''', (score_h, score_a, match_id))
                updates += 1

        conn.commit()
        conn.close()

        return True, f"Journee {semaine_id} validee - {updates} score(s) fige(s)"

    except Exception as e:
        return False, str(e)


def get_utilisateurs_emails():
    """Recupere tous les utilisateurs actifs avec leur email via Supabase"""
    from modules.supabase_db import get_supabase
    supabase = get_supabase()
    users = supabase._request('GET', 'utilisateurs?statut=eq.Actif&email=not.is.null&select=id,pseudo,prenom,email') or []
    return [u for u in users if u.get('email')]


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


# ============================================
# FONCTIONS SUPABASE
# ============================================

def valider_resultats_journee_supabase(semaine_id, saison_id=None):
    """
    Valide les resultats d'une journee via Supabase.
    Recupere les scores depuis l'API Football-Data et met a jour Supabase.
    """
    from modules.supabase_db import get_supabase

    if saison_id is None:
        saison_id = get_saison_actuelle()

    try:
        import requests
        supabase = get_supabase()

        API_TOKEN = _get_football_api_token()
        headers = {'X-Auth-Token': API_TOKEN}

        # Recuperer les matchs de la journee depuis Supabase
        matchs_db = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,equipe_home,equipe_away'
        ) or []

        if not matchs_db:
            return False, "Aucun match trouve pour cette journee"

        # Appeler l'API pour les scores
        url = f'https://api.football-data.org/v4/competitions/FL1/matches?season={saison_id}&matchday={semaine_id}'
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return False, f"Erreur API: {response.status_code}"

        data = response.json()
        matchs_api = data.get('matches', [])

        # Creer un dictionnaire pour lookup rapide
        scores_api = {}
        for m in matchs_api:
            home = m.get('homeTeam', {}).get('name')
            away = m.get('awayTeam', {}).get('name')
            score = m.get('score', {}).get('fullTime', {})
            if score.get('home') is not None:
                scores_api[(home, away)] = (score['home'], score['away'])

        # Mettre a jour les scores dans Supabase
        updates = 0
        for match in matchs_db:
            home = match['equipe_home']
            away = match['equipe_away']
            match_id = match['id']

            if (home, away) in scores_api:
                score_h, score_a = scores_api[(home, away)]
                supabase._request('PATCH', f'matches?id=eq.{match_id}', {
                    'score_final_home': score_h,
                    'score_final_away': score_a
                })
                updates += 1

        return True, f"Journee {semaine_id} validee - {updates} score(s) fige(s)"

    except Exception as e:
        return False, str(e)


def get_users_grand_chelem_semaine_precedente(semaine_id, saison_id):
    """
    Retourne les user_ids qui ont fait un Grand Chelem (4/4 1N2 corrects) la semaine precedente.
    Exclut les voleurs: seul le proprietaire original des pronos peut avoir le GC.
    """
    from modules.supabase_db import get_supabase

    semaine_prec = semaine_id - 1
    if semaine_prec < 1:
        return set()

    try:
        supabase = get_supabase()

        # Recuperer les matchs termines ET actifs de la semaine precedente
        matchs_prec = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_prec}&saison_id=eq.{saison_id}&score_final_home=not.is.null&is_active=eq.true&select=id,score_final_home,score_final_away'
        ) or []

        if len(matchs_prec) < 4:
            return set()  # Pas assez de matchs pour un Grand Chelem

        match_ids = [m['id'] for m in matchs_prec]
        matchs_dict = {m['id']: (m['score_final_home'], m['score_final_away']) for m in matchs_prec}

        # Recuperer les voleurs de la semaine precedente (exclus du GC)
        jokers_vol = supabase._request('GET',
            f'jokers_historique?semaine_id=eq.{semaine_prec}&type_joker=eq.VOL&select=utilisateur_id'
        ) or []
        voleurs = {j['utilisateur_id'] for j in jokers_vol}

        # Recuperer toutes les predictions de ces matchs
        predictions = supabase._request('GET',
            f'predictions?match_id=in.({",".join(map(str, match_ids))})&select=user_id,match_id,score_prono_home,score_prono_away'
        ) or []

        # Compter les 1N2 corrects par user
        user_corrects = {}
        for pred in predictions:
            user_id = pred['user_id']
            match_id = pred['match_id']

            # Exclure les voleurs du GC
            if user_id in voleurs:
                continue

            if match_id not in matchs_dict:
                continue

            score_h, score_a = matchs_dict[match_id]
            prono_h = pred['score_prono_home']
            prono_a = pred['score_prono_away']

            bon_resultat = (
                (prono_h > prono_a and score_h > score_a) or
                (prono_h < prono_a and score_h < score_a) or
                (prono_h == prono_a and score_h == score_a)
            )

            if bon_resultat:
                user_corrects[user_id] = user_corrects.get(user_id, 0) + 1

        # Retourner les users avec 4/4 corrects (non voleurs)
        return {uid for uid, count in user_corrects.items() if count >= 4}

    except Exception as e:
        print(f"Erreur Grand Chelem: {e}")
        return set()


def _calculer_points_match(prono_h, prono_a, score_h, score_a, mise, cote_home, cote_draw, cote_away, bonus_exact=10, mise_bonus_gc=0):
    """
    Calcule les points pour un match donne.
    Retourne (points, is_exact)

    mise_bonus_gc: mise du budget bonus Grand Chelem (pas de perte si mauvais prono)
    """
    # Determiner la cote applicable selon le prono
    if prono_h > prono_a:
        cote = cote_home
    elif prono_h < prono_a:
        cote = cote_away
    else:
        cote = cote_draw

    points = 0
    points_bonus_gc = 0
    is_exact = False

    # Verifier si bon resultat (1N2)
    bon_resultat = (
        (prono_h > prono_a and score_h > score_a) or
        (prono_h < prono_a and score_h < score_a) or
        (prono_h == prono_a and score_h == score_a)
    )

    if bon_resultat:
        points = round(mise * cote, 2)
        # Bonus score exact
        if prono_h == score_h and prono_a == score_a:
            points += bonus_exact
            is_exact = True
        # Points bonus GC (meme calcul, gains uniquement)
        if mise_bonus_gc > 0:
            points_bonus_gc = round(mise_bonus_gc * cote, 2)
            if is_exact:
                points_bonus_gc += bonus_exact
    else:
        points = -mise  # Perte de la mise principale
        # Bonus GC: PAS de perte si mauvais prono (0 pts)
        points_bonus_gc = 0

    return points, is_exact, points_bonus_gc


def calculer_gains_supabase(semaine_id, saison_id=None):
    """
    Calcule les gains avec les COTES pour chaque match termine.
    Formule: mise × cote + bonus 10pts si score exact

    JOKERS:
    - DOUBLE: ×2 sur tous les gains (pertes incluses)
    - VOL: le joueur prend les points de la cible (pas ses propres pronos)

    GRAND CHELEM: gere cote pronostics (budget 140 au lieu de 100)

    AUTO-VOL:
    - Si un joueur a oublie ses pronos et a un joker VOL, il vole Kingo automatiquement
    - Si pas de joker VOL, il a -100 points (penalite)
    """
    from modules.supabase_db import get_supabase

    if saison_id is None:
        saison_id = get_saison_actuelle()

    BONUS_EXACT = 10  # Bonus pour score exact

    try:
        supabase = get_supabase()

        # === AUTO-VOL: Traiter les joueurs qui ont oublie leurs pronos ===
        try:
            oublis_traites, msg_oublis = appliquer_vol_auto_oublis(semaine_id, saison_id)
            if oublis_traites:
                print(f"Auto-VOL: {msg_oublis}")
        except Exception as e:
            print(f"Erreur Auto-VOL: {e}")

        # Recuperer les jokers DOUBLE actifs pour cette semaine
        jokers_double = supabase._request('GET',
            f'jokers_historique?semaine_id=eq.{semaine_id}&type_joker=eq.DOUBLE&select=utilisateur_id'
        ) or []
        users_avec_double = {j['utilisateur_id'] for j in jokers_double}

        # Recuperer les jokers VOL actifs avec leur cible
        jokers_vol = supabase._request('GET',
            f'jokers_historique?semaine_id=eq.{semaine_id}&type_joker=eq.VOL&select=utilisateur_id,cible_vol_id'
        ) or []
        # Dict: voleur_id -> cible_id
        vol_cibles = {j['utilisateur_id']: j['cible_vol_id'] for j in jokers_vol if j.get('cible_vol_id')}

        # Recuperer les matchs termines avec cotes
        matchs = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&score_final_home=not.is.null&select=id,score_final_home,score_final_away,cote_home,cote_draw,cote_away'
        ) or []

        if not matchs:
            return False, "Aucun match termine"

        match_ids = [m['id'] for m in matchs]
        match_ids_str = ','.join(map(str, match_ids))
        match_map = {m['id']: m for m in matchs}

        # Recuperer TOUTES les predictions de la semaine (pour le VOL)
        all_predictions = supabase._request('GET',
            f'predictions?match_id=in.({match_ids_str})&select=id,user_id,match_id,score_prono_home,score_prono_away,mise_points,mise_bonus_gc,points_gagnes'
        ) or []

        # Organiser les predictions par user et par match
        preds_by_user = {}
        for p in all_predictions:
            uid = p['user_id']
            mid = p['match_id']
            if uid not in preds_by_user:
                preds_by_user[uid] = {}
            preds_by_user[uid][mid] = p

        total_updates = 0
        comparaisons_vol = []  # Pour stocker les comparaisons VOL

        # Traiter chaque utilisateur
        users_traites = set(preds_by_user.keys())
        for user_id in users_traites:
            user_preds = preds_by_user.get(user_id, {})

            # Verifier si cet utilisateur a un joker VOL
            cible_id = vol_cibles.get(user_id)
            cible_preds = preds_by_user.get(cible_id, {}) if cible_id else {}

            points_propres_total = 0  # Points avec ses propres pronos
            points_voles_total = 0    # Points avec les pronos de la cible

            for match_id, pred in user_preds.items():
                # Si deja calcule, skip
                if pred.get('points_gagnes') is not None:
                    continue

                match = match_map.get(match_id)
                if not match:
                    continue

                score_h = match['score_final_home']
                score_a = match['score_final_away']
                cote_home = match.get('cote_home', 2.0) or 2.0
                cote_draw = match.get('cote_draw', 3.0) or 3.0
                cote_away = match.get('cote_away', 2.0) or 2.0

                # Calculer les points avec ses PROPRES pronos
                prono_h = pred['score_prono_home']
                prono_a = pred['score_prono_away']
                mise = pred['mise_points'] or 25
                mise_bonus_gc = pred.get('mise_bonus_gc', 0) or 0

                points_propres, is_exact_propres, pts_bonus_gc = _calculer_points_match(
                    prono_h, prono_a, score_h, score_a, mise, cote_home, cote_draw, cote_away, BONUS_EXACT, mise_bonus_gc
                )
                points_propres_total += points_propres

                # Si joker VOL actif, utiliser les pronos de la cible
                # VOL: uniquement sur le budget 100, PAS sur le bonus GC
                if cible_id and cible_id in preds_by_user:
                    cible_pred = cible_preds.get(match_id)
                    if cible_pred:
                        cible_prono_h = cible_pred['score_prono_home']
                        cible_prono_a = cible_pred['score_prono_away']
                        # VOL utilise les mises du budget 100 de la cible (PAS mise_bonus_gc)
                        cible_mise = cible_pred['mise_points'] or 25

                        points_voles, is_exact_voles, _ = _calculer_points_match(
                            cible_prono_h, cible_prono_a, score_h, score_a, cible_mise, cote_home, cote_draw, cote_away, BONUS_EXACT
                        )
                        points_voles_total += points_voles

                        # Le joueur prend les points voles (budget 100 uniquement)
                        # Le bonus GC du voleur est perdu (GC = proprietaire original seulement)
                        points_final = points_voles
                        is_exact_final = is_exact_voles
                        pts_bonus_gc = 0  # Voleur n'a pas droit au bonus GC
                    else:
                        # Pas de prono de la cible pour ce match, garder les siens
                        points_final = points_propres
                        is_exact_final = is_exact_propres
                else:
                    # Pas de VOL, utiliser ses propres points
                    points_final = points_propres
                    is_exact_final = is_exact_propres

                # JOKER DOUBLE: x2 sur les gains/pertes du budget 100 uniquement
                if user_id in users_avec_double:
                    points_final = points_final * 2
                    # Le bonus GC n'est PAS multiplie par le Double

                # Total = points budget 100 (avec Double/Vol) + bonus GC (protege)
                points_total = points_final + pts_bonus_gc

                supabase._request('PATCH', f'predictions?id=eq.{pred["id"]}', {
                    'points_gagnes': points_total,
                    'is_score_exact': is_exact_final
                })
                total_updates += 1

            # Stocker la comparaison VOL si applicable
            if cible_id and cible_id in preds_by_user:
                diff = points_voles_total - points_propres_total
                comparaisons_vol.append({
                    'user_id': user_id,
                    'cible_id': cible_id,
                    'points_propres': points_propres_total,
                    'points_voles': points_voles_total,
                    'diff': diff,
                    'rentable': diff > 0
                })

        # Invalider le cache Streamlit
        try:
            import streamlit as st
            st.cache_data.clear()
        except:
            pass

        # Construire le message de retour
        info_parts = []
        if users_avec_double:
            info_parts.append(f"{len(users_avec_double)} jokers DOUBLE")
        if vol_cibles:
            info_parts.append(f"{len(vol_cibles)} jokers VOL")

        # Ajouter les comparaisons VOL au message
        for comp in comparaisons_vol:
            signe = '+' if comp['diff'] > 0 else ''
            info_parts.append(f"VOL user {comp['user_id']}: {comp['points_voles']}pts (vs {comp['points_propres']}pts, {signe}{comp['diff']})")

        extra_info = f" ({', '.join(info_parts)})" if info_parts else ""

        return True, f"Gains calcules pour {total_updates} predictions{extra_info}"

    except Exception as e:
        return False, str(e)


def update_scores_from_api(semaine_id, saison_id=None):
    """
    Met a jour les scores depuis l'API et calcule les points automatiquement.
    Fonction all-in-one pour mise a jour en temps reel.
    Couvre: Ligue 1 + Premier League + La Liga + Serie A + Bundesliga.
    """
    import requests
    from datetime import timedelta
    from modules.supabase_db import get_supabase

    if saison_id is None:
        saison_id = get_saison_actuelle()

    try:
        supabase = get_supabase()
        API_TOKEN = _get_football_api_token()
        headers = {'X-Auth-Token': API_TOKEN}

        # Recuperer les matchs de la journee depuis Supabase (avec date_match)
        matchs_db = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,equipe_home,equipe_away,score_final_home,score_final_away,date_match'
        ) or []

        # === 1. Matchs Ligue 1 ===
        url = f'https://api.football-data.org/v4/competitions/FL1/matches?season={saison_id}&matchday={semaine_id}'
        response = requests.get(url, headers=headers)

        matchs_api = []
        if response.status_code == 200:
            matchs_api = response.json().get('matches', [])

        # === 2. Matchs etrangers (PL, La Liga, Serie A, Bundesliga) ===
        # Determiner la plage de dates depuis les matchs en base
        dates_db = [m.get('date_match', '') for m in matchs_db if m.get('date_match')]
        if dates_db:
            dates_str = [str(d)[:10] for d in dates_db if d]
            if dates_str:
                dt_min = datetime.strptime(min(dates_str), '%Y-%m-%d') - timedelta(days=1)
                dt_max = datetime.strptime(max(dates_str), '%Y-%m-%d') + timedelta(days=1)
                date_from = dt_min.strftime('%Y-%m-%d')
                date_to = dt_max.strftime('%Y-%m-%d')
            else:
                now = datetime.now()
                date_from = (now - timedelta(days=3)).strftime('%Y-%m-%d')
                date_to = (now + timedelta(days=4)).strftime('%Y-%m-%d')
        else:
            now = datetime.now()
            date_from = (now - timedelta(days=3)).strftime('%Y-%m-%d')
            date_to = (now + timedelta(days=4)).strftime('%Y-%m-%d')

        for code in ['PL', 'PD', 'SA', 'BL1']:
            try:
                url_ext = f'https://api.football-data.org/v4/competitions/{code}/matches?dateFrom={date_from}&dateTo={date_to}'
                resp = requests.get(url_ext, headers=headers, timeout=10)
                if resp.status_code == 200:
                    matchs_api.extend(resp.json().get('matches', []))
            except Exception:
                pass  # Continuer si un championnat echoue

        # === 3. Mettre a jour les scores ===
        updates = 0
        for m_api in matchs_api:
            home_api = m_api.get('homeTeam', {}).get('name')
            away_api = m_api.get('awayTeam', {}).get('name')
            score = m_api.get('score', {}).get('fullTime', {})
            status = m_api.get('status')

            if score.get('home') is None:
                continue  # Match pas encore termine

            # Trouver le match correspondant dans la DB
            for m_db in matchs_db:
                # Matching par nom d'equipe (flexible)
                home_match = (home_api and (home_api in m_db['equipe_home'] or m_db['equipe_home'] in home_api))
                away_match = (away_api and (away_api in m_db['equipe_away'] or m_db['equipe_away'] in away_api))

                if home_match and away_match:
                    # Verifier si le score a change
                    old_home = m_db.get('score_final_home')
                    old_away = m_db.get('score_final_away')
                    new_home = score['home']
                    new_away = score['away']

                    if old_home != new_home or old_away != new_away:
                        # Score different -> Mettre a jour
                        supabase._request('PATCH', f"matches?id=eq.{m_db['id']}", {
                            'score_final_home': new_home,
                            'score_final_away': new_away,
                            'status': 'FINISHED'
                        })
                        updates += 1

                        # Reset les points des predictions pour ce match (force recalcul)
                        supabase._request('PATCH', f"predictions?match_id=eq.{m_db['id']}", {
                            'points_gagnes': None,
                            'is_score_exact': None
                        })
                    break

        # TOUJOURS calculer les points (meme sans nouveaux scores)
        # Pour rattraper les calculs manques
        calculer_gains_supabase(semaine_id, saison_id)

        return True, f"{updates} score(s) mis a jour, points recalcules"

    except Exception as e:
        return False, str(e)


def get_points_joueur_semaine(user_id, semaine_id, saison_id=None):
    """
    Recupere les points d'un joueur pour une semaine donnee.
    Retourne dict avec total, nb_exacts, detail par match (mise, points_gagnes).
    """
    from modules.supabase_db import get_supabase

    if saison_id is None:
        saison_id = get_saison_actuelle()

    try:
        supabase = get_supabase()

        # Recuperer les matchs de la semaine
        matchs = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id'
        ) or []

        if not matchs:
            return {'total': 0, 'nb_exacts': 0, 'details': []}

        match_ids = [m['id'] for m in matchs]
        match_ids_str = ','.join(map(str, match_ids))

        # Recuperer les predictions du joueur
        predictions = supabase._request('GET',
            f'predictions?user_id=eq.{user_id}&match_id=in.({match_ids_str})&select=match_id,mise_points,points_gagnes,is_score_exact'
        ) or []

        total = 0
        nb_exacts = 0
        details = []
        for p in predictions:
            pts = p.get('points_gagnes') or 0
            total += pts
            if p.get('is_score_exact'):
                nb_exacts += 1
            details.append({
                'match_id': p['match_id'],
                'mise': p.get('mise_points') or 0,
                'points_gagnes': pts,
                'is_exact': p.get('is_score_exact') or False
            })

        return {'total': total, 'nb_exacts': nb_exacts, 'details': details}

    except Exception as e:
        print(f"Erreur get_points_joueur_semaine: {e}")
        return {'total': 0, 'nb_exacts': 0, 'details': []}


def get_streak_meilleur_joueur(user_id, saison_id=None):
    """
    Calcule le nombre de journees consecutives ou le joueur est meilleur joueur,
    en partant de la journee la plus recente.
    """
    if saison_id is None:
        saison_id = get_saison_actuelle()

    journee_courante = get_journee_courante(saison_id)
    streak = 0

    for j in range(journee_courante - 1, 0, -1):
        mvp = get_mvp_semaine(j, saison_id)
        if mvp and mvp['user_id'] == user_id:
            streak += 1
        else:
            break

    return streak


def get_bonus_meilleur_joueur(user_id, saison_id=None):
    """
    Calcule le bonus pour meilleur joueur consecutif.
    - streak < 2 : 0 pts
    - streak == 2 : +10 pts
    - streak > 2 : +10 + 15*(streak-2) pts
    """
    streak = get_streak_meilleur_joueur(user_id, saison_id)

    if streak < 2:
        return 0
    elif streak == 2:
        return 10
    else:
        return 10 + 15 * (streak - 2)


# Mapping football-data.org → The Odds API
ODDS_API_MAPPING = {
    'FL1': 'soccer_france_ligue_one',
    'PL': 'soccer_epl',
    'PD': 'soccer_spain_la_liga',
    'SA': 'soccer_italy_serie_a',
    'BL1': 'soccer_germany_bundesliga',
}


def fetch_real_odds(championnats_codes=None):
    """Recupere les vraies cotes depuis The Odds API.

    Args:
        championnats_codes: liste de codes football-data.org (ex: ['FL1', 'PL'])
                           Si None, recupere tous les championnats du mapping.

    Returns:
        dict: {(home_lower, away_lower): (cote_h, cote_n, cote_a)}
    """
    import requests

    # Recuperer la cle API
    try:
        import streamlit as st
        api_key = st.secrets.get("ODDS_API_KEY", "")
    except Exception:
        api_key = os.getenv("ODDS_API_KEY", "")

    if not api_key:
        print("[ODDS] Pas de cle API, fallback random")
        return {}

    if championnats_codes is None:
        championnats_codes = list(ODDS_API_MAPPING.keys())

    odds_dict = {}

    for code in championnats_codes:
        odds_key = ODDS_API_MAPPING.get(code)
        if not odds_key:
            continue

        try:
            url = f"https://api.the-odds-api.com/v4/sports/{odds_key}/odds"
            params = {
                'apiKey': api_key,
                'regions': 'eu',
                'markets': 'h2h',
                'oddsFormat': 'decimal',
            }
            resp = requests.get(url, params=params, timeout=15)

            if resp.status_code != 200:
                print(f"[ODDS] Erreur {resp.status_code} pour {code}")
                continue

            events = resp.json()
            print(f"[ODDS] {len(events)} matchs recuperes pour {code}")

            for event in events:
                home = event.get('home_team', '')
                away = event.get('away_team', '')

                # Collecter les cotes de tous les bookmakers
                all_home, all_draw, all_away = [], [], []
                for bookmaker in event.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market.get('key') != 'h2h':
                            continue
                        outcomes = {o['name']: o['price'] for o in market.get('outcomes', [])}
                        if home in outcomes:
                            all_home.append(outcomes[home])
                        if 'Draw' in outcomes:
                            all_draw.append(outcomes['Draw'])
                        if away in outcomes:
                            all_away.append(outcomes[away])

                # Moyenne des cotes (plus stable)
                if all_home and all_draw and all_away:
                    cote_h = round(sum(all_home) / len(all_home), 2)
                    cote_n = round(sum(all_draw) / len(all_draw), 2)
                    cote_a = round(sum(all_away) / len(all_away), 2)
                    odds_dict[(home.lower(), away.lower())] = (cote_h, cote_n, cote_a)

        except Exception as e:
            print(f"[ODDS] Exception pour {code}: {e}")
            continue

    print(f"[ODDS] Total: {len(odds_dict)} matchs avec cotes reelles")
    return odds_dict


def lookup_odds(odds_dict, equipe_home, equipe_away):
    """Cherche les cotes d'un match dans le dict.

    Matching par inclusion partielle pour gerer les differences de noms
    entre football-data.org et The Odds API.

    Returns:
        tuple (cote_h, cote_n, cote_a) ou None si pas trouve
    """
    if not odds_dict:
        return None

    home_lower = equipe_home.lower()
    away_lower = equipe_away.lower()

    # Match exact
    if (home_lower, away_lower) in odds_dict:
        return odds_dict[(home_lower, away_lower)]

    # Match par inclusion partielle
    for (oh, oa), cotes in odds_dict.items():
        if (oh in home_lower or home_lower in oh) and \
           (oa in away_lower or away_lower in oa):
            return cotes

    return None


def importer_matchs_journee_supabase(semaine_id, saison_id=None):
    """
    Importe les matchs d'une journee:
    - 9 matchs Ligue 1 (tous)
    - 11 meilleurs matchs des championnats etrangers (selon criteres)

    Total: ~20 matchs avec is_active=False (selection manuelle admin)

    Returns:
        tuple: (success, message, nb_matchs)
    """
    import requests
    import random
    from datetime import datetime, timedelta
    from modules.supabase_db import get_supabase

    if saison_id is None:
        saison_id = get_saison_actuelle()

    # === CONFIGURATION ===
    API_TOKEN = _get_football_api_token()
    headers = {'X-Auth-Token': API_TOKEN}

    # Championnats etrangers a scanner
    CHAMPIONNATS = {
        'PL': 'Premier League',
        'PD': 'La Liga',
        'SA': 'Serie A',
        'BL1': 'Bundesliga'
    }

    # Mega clubs europeens (score +1000)
    MEGA_CLUBS = {
        # Ligue 1
        'Paris Saint-Germain', 'Olympique de Marseille', 'Olympique Lyonnais',
        # Etrangers
        'Real Madrid', 'FC Barcelona', 'Atletico Madrid',
        'Manchester United', 'Manchester City', 'Liverpool', 'Arsenal', 'Chelsea', 'Tottenham',
        'Juventus', 'AC Milan', 'Inter Milan', 'AS Roma', 'SSC Napoli',
        'Bayern Munich', 'Borussia Dortmund'
    }

    # Derbies celebres (score +2000)
    DERBIES = [
        # Ligue 1
        ('Paris Saint-Germain', 'Olympique de Marseille'),  # Le Classique
        ('Olympique Lyonnais', 'AS Saint-Etienne'),  # Derby du Rhone
        ('Racing Club de Lens', 'Lille'),  # Derby du Nord
        ('OGC Nice', 'AS Monaco'),  # Derby de la Cote d'Azur
        # Etrangers
        ('Real Madrid', 'FC Barcelona'),  # El Clasico
        ('Real Madrid', 'Atletico Madrid'),  # Derby de Madrid
        ('Manchester United', 'Manchester City'),  # Derby de Manchester
        ('Manchester United', 'Liverpool'),  # North West Derby
        ('Arsenal', 'Tottenham'),  # North London Derby
        ('Arsenal', 'Chelsea'),  # London Derby
        ('AC Milan', 'Inter Milan'),  # Derby della Madonnina
        ('Juventus', 'Inter Milan'),  # Derby d'Italia
        ('AS Roma', 'SS Lazio'),  # Derby della Capitale
        ('Bayern Munich', 'Borussia Dortmund'),  # Der Klassiker
    ]

    # Top clubs par championnat (score +500 si 2 top clubs s'affrontent)
    TOP_CLUBS = {
        'FL1': {'Paris Saint-Germain', 'Olympique de Marseille', 'AS Monaco', 'Lille', 'Olympique Lyonnais',
                'OGC Nice', 'Racing Club de Lens', 'Stade Rennais', 'Stade Brestois', 'RC Strasbourg'},
        'PL': {'Manchester City', 'Arsenal', 'Liverpool', 'Chelsea', 'Manchester United', 'Tottenham', 'Newcastle', 'Brighton', 'Aston Villa', 'West Ham'},
        'PD': {'Real Madrid', 'FC Barcelona', 'Atletico Madrid', 'Athletic Bilbao', 'Real Sociedad', 'Real Betis', 'Villarreal', 'Sevilla'},
        'SA': {'Inter Milan', 'AC Milan', 'Juventus', 'SSC Napoli', 'AS Roma', 'SS Lazio', 'Atalanta', 'Fiorentina'},
        'BL1': {'Bayern Munich', 'Borussia Dortmund', 'RB Leipzig', 'Bayer Leverkusen', 'Eintracht Frankfurt', 'Union Berlin', 'Freiburg', 'Wolfsburg'}
    }

    def score_match(m, competition_code):
        """Calcule le score d'interet d'un match etranger"""
        home = m.get('homeTeam', {}).get('name', '')
        away = m.get('awayTeam', {}).get('name', '')
        score = 0

        # Derby (+2000)
        for d1, d2 in DERBIES:
            if (d1 in home and d2 in away) or (d2 in home and d1 in away):
                score += 2000
                break

        # Mega club implique (+1000)
        for mc in MEGA_CLUBS:
            if mc in home or mc in away:
                score += 1000
                break

        # 2 top clubs s'affrontent (+500)
        top = TOP_CLUBS.get(competition_code, set())
        home_top = any(t in home for t in top)
        away_top = any(t in away for t in top)
        if home_top and away_top:
            score += 500
        elif home_top or away_top:
            score += 200

        return score

    try:
        supabase = get_supabase()

        # Verifier les matchs existants (pour eviter les doublons)
        existing = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&select=id,equipe_home,equipe_away'
        ) or []

        # Creer un set des matchs existants pour verification rapide
        existing_matchs = set()
        for e in existing:
            key = f"{e['equipe_home']}_{e['equipe_away']}"
            existing_matchs.add(key)

        all_matchs_to_import = []

        # === 1. RECUPERER TOUS LES MATCHS LIGUE 1 ===
        url_l1 = f'https://api.football-data.org/v4/competitions/FL1/matches?season={saison_id}&matchday={semaine_id}'
        resp_l1 = requests.get(url_l1, headers=headers)
        matchs_l1 = []

        if resp_l1.status_code == 200:
            matchs_l1 = resp_l1.json().get('matches', [])
            for m in matchs_l1:
                # Calculer le score d'interet pour L1 aussi
                score = score_match(m, 'FL1')
                all_matchs_to_import.append({
                    'championnat': 'Ligue 1',
                    'equipe_home': m.get('homeTeam', {}).get('name', ''),
                    'equipe_away': m.get('awayTeam', {}).get('name', ''),
                    'date_match': m.get('utcDate', ''),
                    'score_interet': score
                })
        else:
            # Erreur API L1 - retourner l'erreur
            return False, f"Erreur API Ligue 1: {resp_l1.status_code} - {resp_l1.text[:200]}", 0

        if not matchs_l1:
            return False, f"Aucun match L1 trouve pour J{semaine_id} saison {saison_id}", 0

        # === 2. RECUPERER LES MATCHS ETRANGERS (meme weekend) ===
        # Calculer les dates du weekend de la journee L1
        if matchs_l1:
            dates_l1 = [m.get('utcDate', '')[:10] for m in matchs_l1 if m.get('utcDate')]
            if dates_l1:
                date_min = min(dates_l1)
                date_max = max(dates_l1)
                # Elargir la fenetre de 1 jour avant/apres
                try:
                    dt_min = datetime.strptime(date_min, '%Y-%m-%d') - timedelta(days=1)
                    dt_max = datetime.strptime(date_max, '%Y-%m-%d') + timedelta(days=1)
                    date_from = dt_min.strftime('%Y-%m-%d')
                    date_to = dt_max.strftime('%Y-%m-%d')
                except:
                    date_from = date_min
                    date_to = date_max
            else:
                # Fallback: semaine courante
                today = datetime.now()
                date_from = (today - timedelta(days=3)).strftime('%Y-%m-%d')
                date_to = (today + timedelta(days=4)).strftime('%Y-%m-%d')
        else:
            today = datetime.now()
            date_from = (today - timedelta(days=3)).strftime('%Y-%m-%d')
            date_to = (today + timedelta(days=4)).strftime('%Y-%m-%d')

        matchs_etrangers = []

        # Championnats etrangers (optionnel - ne bloque pas si erreur)
        try:
            for code, nom in CHAMPIONNATS.items():
                try:
                    url = f'https://api.football-data.org/v4/competitions/{code}/matches?dateFrom={date_from}&dateTo={date_to}'
                    resp = requests.get(url, headers=headers, timeout=10)

                    if resp.status_code == 200:
                        matchs = resp.json().get('matches', [])
                        for m in matchs:
                            # Ignorer les matchs deja termines
                            status = m.get('status', '')
                            if status == 'FINISHED':
                                continue

                            score = score_match(m, code)
                            matchs_etrangers.append({
                                'championnat': nom,
                                'equipe_home': m.get('homeTeam', {}).get('name', ''),
                                'equipe_away': m.get('awayTeam', {}).get('name', ''),
                                'date_match': m.get('utcDate', ''),
                                'score_interet': score
                            })
                except Exception:
                    pass  # Ignorer les erreurs sur championnats etrangers
        except Exception:
            pass  # Continuer avec L1 seulement

        # Trier par score d'interet et prendre les 11 meilleurs etrangers
        if matchs_etrangers:
            matchs_etrangers.sort(key=lambda x: x['score_interet'], reverse=True)
            top_11_etrangers = matchs_etrangers[:11]
            all_matchs_to_import.extend(top_11_etrangers)

        # === 3. TRIER TOUS LES MATCHS ET ACTIVER LES 4 MEILLEURS ===
        # Trier tous les matchs par score d'interet
        all_matchs_to_import.sort(key=lambda x: x['score_interet'], reverse=True)

        # === 4. IMPORTER DANS SUPABASE (seulement les nouveaux) ===
        # Recuperer les vraies cotes depuis The Odds API
        odds_codes = ['FL1'] + list(CHAMPIONNATS.keys())
        odds_dict = fetch_real_odds(odds_codes)

        # Determiner les 4 meilleurs matchs (par score d'interet)
        top_4_keys = set()
        for m in all_matchs_to_import[:4]:
            top_4_keys.add(f"{m['equipe_home']}_{m['equipe_away']}")

        count = 0
        skipped = 0
        activated = 0

        for i, m in enumerate(all_matchs_to_import):
            # Verifier si le match existe deja
            match_key = f"{m['equipe_home']}_{m['equipe_away']}"
            if match_key in existing_matchs:
                skipped += 1
                continue

            # Vraies cotes depuis The Odds API (fallback random)
            real = lookup_odds(odds_dict, m['equipe_home'], m['equipe_away'])
            if real:
                cote_h, cote_n, cote_a = real
            else:
                cote_h = round(random.uniform(1.5, 3.5), 2)
                cote_n = round(random.uniform(3.0, 4.0), 2)
                cote_a = round(random.uniform(1.8, 4.0), 2)

            # Activer les 4 meilleurs matchs par score d'interet
            is_active = (match_key in top_4_keys)
            if is_active:
                activated += 1

            supabase._request('POST', 'matches', {
                'saison_id': saison_id,
                'semaine_id': semaine_id,
                'championnat': m['championnat'],
                'equipe_home': m['equipe_home'],
                'equipe_away': m['equipe_away'],
                'cote_home': cote_h,
                'cote_draw': cote_n,
                'cote_away': cote_a,
                'date_match': m['date_match'],
                'is_active': is_active
            })
            count += 1

        nb_l1 = len([m for m in all_matchs_to_import if m['championnat'] == 'Ligue 1'])
        nb_etrangers = len(all_matchs_to_import) - nb_l1
        total = count + len(existing)

        if count == 0:
            return True, f"Deja {len(existing)} matchs, {skipped} ignores (doublons)", len(existing)

        return True, f"{count} matchs importes dont {activated} actives par le bot ({total} total: {nb_l1} L1 + {nb_etrangers} etrangers)", total

    except Exception as e:
        return False, str(e), 0
