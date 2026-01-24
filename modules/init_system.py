import sqlite3
import os

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

def initialiser_systeme_complet():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Table MATCHES (Celle qui cause l'erreur actuelle)
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        semaine_id INTEGER,
        championnat TEXT,
        equipe_home TEXT,
        equipe_away TEXT,
        cote_home REAL,
        cote_draw REAL,
        cote_away REAL,
        date_match TEXT,
        score_final_home INTEGER,
        score_final_away INTEGER,
        score_mi_temps_home INTEGER,
        score_mi_temps_away INTEGER,
        status TEXT DEFAULT 'SCHEDULED',
        saison_id INTEGER DEFAULT 2024,
        is_active BOOLEAN DEFAULT 1
    )''')

    # Migration: Ajouter les colonnes manquantes si elles n'existent pas
    colonnes_a_ajouter = [
        ("score_mi_temps_home", "INTEGER"),
        ("score_mi_temps_away", "INTEGER"),
        ("status", "TEXT DEFAULT 'SCHEDULED'"),
        ("saison_id", "INTEGER DEFAULT 2024"),
        ("is_active", "BOOLEAN DEFAULT 1"),
    ]
    for col_name, col_type in colonnes_a_ajouter:
        try:
            cursor.execute(f"ALTER TABLE matches ADD COLUMN {col_name} {col_type}")
        except:
            pass

    # 2. Table UTILISATEURS (Harmonisée pour l'admin)
    cursor.execute('''CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pseudo TEXT UNIQUE,
        nom TEXT,
        prenom TEXT,
        email TEXT,
        statut TEXT DEFAULT 'en_attente',
        points_total INTEGER DEFAULT 0
    )''')

    # 3. Table PRONOSTICS
    cursor.execute('''CREATE TABLE IF NOT EXISTS pronostics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER,
        score_home_prono INTEGER,
        score_away_prono INTEGER,
        mise INTEGER,
        FOREIGN KEY(match_id) REFERENCES matches(id)
    )''')

    conn.commit()
    conn.close()
    print("✅ Base de données synchronisée. Toutes les tables sont prêtes.")

if __name__ == "__main__":
    initialiser_systeme_complet()