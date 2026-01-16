import sqlite3
import os

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

def calcul_automatique_global():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. SÉCURITÉ : On s'assure que les colonnes de scores existent dans 'matches'
    try:
        cursor.execute("ALTER TABLE matches ADD COLUMN score_final_home INTEGER")
        cursor.execute("ALTER TABLE matches ADD COLUMN score_final_away INTEGER")
    except sqlite3.OperationalError:
        pass # Déjà présentes

    # 2. RÉCUPÉRATION DES DONNÉES
    try:
        cursor.execute('''
            SELECT m.equipe_home, m.equipe_away, 
                   m.score_final_home, m.score_final_away,
                   p.score_home_prono, p.score_away_prono, p.mise
            FROM matches m
            JOIN pronostics p ON m.id = p.match_id
        ''')
        resultats = cursor.fetchall()
    except sqlite3.OperationalError:
        print("⚠️ Erreur : La table 'pronostics' est vide ou mal formée. Saisis d'abord tes pronos !")
        conn.close()
        return

    total_semaine = 0
    matchs_calcules = 0

    print("\n--- CALCUL DES POINTS AUTOMATIQUE ---")
    for res in resultats:
        home, away, v_h, v_a, p_h, p_a, mise = res
        
        if v_h is None: 
            print(f"⏳ {home} vs {away} : Score final non saisi par l'admin.")
            continue

        # LOGIQUE DE POINTS
        points_match = 0
        if v_h == p_h and v_a == p_a:
            points_match = int(mise * 3)
            status = "🎯 SCORE EXACT !"
        elif (v_h > v_a and p_h > p_a) or (v_h < v_a and p_h < p_a) or (v_h == v_a and p_h == p_a):
            points_match = int(mise * 1.5)
            status = "✅ BON RÉSULTAT (1N2)"
        else:
            status = "❌ PERDU"

        total_semaine += points_match
        matchs_calcules += 1
        print(f"⚽ {home}-{away} | Prono: {p_h}-{p_a} | Réel: {v_h}-{v_a} -> {status} ({points_match} pts)")

    # 3. MISE À JOUR DU PROFIL
    if matchs_calcules > 0:
        cursor.execute("UPDATE utilisateurs SET points_total = points_total + ? WHERE pseudo = 'LeStrategiste'", (total_semaine,))
        conn.commit()
        print(f"\n🚀 SUCCESS : {total_semaine} points ajoutés au profil de 'LeStrategiste'.")
    else:
        print("\nℹ️ Aucun match n'a encore de score final pour le calcul.")

    conn.close()

if __name__ == "__main__":
    calcul_automatique_global()