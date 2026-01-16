import sqlite3
from .database import DB_PATH

def init_db():
    # Connexion (cree le fichier s'il n'existe pas)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Table des UTILISATEURS (avec gestion Admin et Tokens)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prenom TEXT,
            pseudo TEXT UNIQUE,
            email TEXT,
            telephone TEXT,
            date_naissance TEXT,
            pin TEXT,
            avatar TEXT,
            joueur_secours TEXT,
            statut TEXT DEFAULT 'en_attente', -- en_attente, valide, pause, admin
            tokens_football INTEGER DEFAULT 50
        )
    ''')

    # 2. Table des MATCHS (pour que l'admin puisse modifier)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matchs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semaine_l1 TEXT,
            championnat TEXT,
            equipe_dom TEXT,
            equipe_ext TEXT,
            cote_1 REAL,
            cote_n REAL,
            cote_2 REAL,
            score_reel_dom INTEGER,
            score_reel_ext INTEGER,
            statut_match TEXT DEFAULT 'a_venir' -- a_venir, termine, annule
        )
    ''')

    # 3. Table des PRONOSTICS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pronostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            match_id INTEGER,
            score_prono_dom INTEGER,
            score_prono_ext INTEGER,
            mise_points INTEGER,
            points_gagnes REAL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES utilisateurs(id),
            FOREIGN KEY(match_id) REFERENCES matchs(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ La base de données 'elite_pronos.db' a été créée avec succès !")

if __name__ == "__main__":
    init_db()