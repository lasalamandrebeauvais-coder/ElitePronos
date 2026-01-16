import sqlite3
import os

# Chemin vers la base de donnees (relatif a la racine du projet)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

def get_db_path():
    """Retourne le chemin absolu vers la base de donnees"""
    return DB_PATH

def create_database():
    # Connexion au fichier unique valide
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Table UTILISATEURS (Synchronisée avec inscription.py et admin_panel.py)
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

    # 2. Table MATCHS (Synchronisée avec bot_sourcing.py et interface_win.py)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semaine_id INTEGER,
            championnat TEXT,
            equipe_home TEXT,
            equipe_away TEXT,
            cote_home REAL,
            cote_draw REAL,
            cote_away REAL,
            date_match TEXT
        )
    ''')

    # 3. Table PRONOSTICS (Synchronisée avec interface_win.py et calcul_resultats.py)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pronostics (
            match_id INTEGER PRIMARY KEY,
            score_home_prono INTEGER,
            score_away_prono INTEGER,
            mise INTEGER
        )
    ''')

    # 4. Tables JOKERS & CONFIG (Synchronisées avec interface_win.py)
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

    # 5. Table HISTORIQUE (Synchronisée avec calcul_resultats.py)
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

    conn.commit()
    conn.close()
    print(f"Base de donnees synchronisee: {DB_PATH}")

if __name__ == "__main__":
    create_database()