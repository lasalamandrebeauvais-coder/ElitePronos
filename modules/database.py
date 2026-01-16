import sqlite3
import os

# Chemin vers la base de donnees (relatif a la racine du projet)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Creer le dossier database s'il n'existe pas (necessaire pour Streamlit Cloud)
DB_DIR = os.path.dirname(DB_PATH)
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

def get_db_path():
    """Retourne le chemin absolu vers la base de donnees"""
    return DB_PATH

def create_database():
    """Cree toutes les tables necessaires pour Elite Pronos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Table UTILISATEURS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prenom TEXT,
            pseudo TEXT UNIQUE,
            email TEXT,
            telephone TEXT,
            pin TEXT,
            joueur_secours TEXT,
            statut TEXT DEFAULT 'en_attente'
        )
    ''')

    # 2. Table MATCHES (avec toutes les colonnes necessaires)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saison_id INTEGER DEFAULT 2024,
            semaine_id INTEGER NOT NULL DEFAULT 1,
            championnat TEXT NOT NULL DEFAULT 'FL1',
            equipe_home TEXT NOT NULL,
            equipe_away TEXT NOT NULL,
            cote_home REAL NOT NULL DEFAULT 2.0,
            cote_draw REAL NOT NULL DEFAULT 3.0,
            cote_away REAL NOT NULL DEFAULT 2.5,
            date_match DATETIME,
            score_final_home INTEGER,
            score_final_away INTEGER,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # 3. Table PREDICTIONS (principale pour les pronostics utilisateurs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            saison_id INTEGER DEFAULT 2024,
            score_prono_home INTEGER NOT NULL,
            score_prono_away INTEGER NOT NULL,
            mise_points INTEGER NOT NULL,
            points_gagnes INTEGER DEFAULT 0,
            is_score_exact BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES utilisateurs(id),
            FOREIGN KEY (match_id) REFERENCES matches(id),
            UNIQUE(user_id, match_id)
        )
    ''')

    # 4. Table PRONOSTICS (legacy - compatibilite)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pronostics (
            match_id INTEGER PRIMARY KEY,
            score_home_prono INTEGER,
            score_away_prono INTEGER,
            mise INTEGER
        )
    ''')

    # 5. Tables JOKERS & CONFIG
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS joker_semaine (
            id INTEGER PRIMARY KEY,
            type TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_semaine (
            cle TEXT PRIMARY KEY,
            valeur TEXT
        )
    ''')

    # 6. Table HISTORIQUE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historique (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            points_gagnes REAL,
            nb_1n2_corrects INTEGER,
            nb_scores_exacts INTEGER,
            grand_chelem_valide INTEGER DEFAULT 0,
            date_calcul TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. Table RELATIONS (amis)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER NOT NULL,
            ami_id INTEGER NOT NULL,
            statut TEXT DEFAULT 'en_attente',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
            FOREIGN KEY (ami_id) REFERENCES utilisateurs(id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"[OK] Base de donnees initialisee: {DB_PATH}")

if __name__ == "__main__":
    create_database()