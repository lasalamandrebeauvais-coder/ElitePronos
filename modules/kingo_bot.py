"""
Module Kingo Bot pour Elite Pronos
Le roi des pronostics - IA qui participe comme un joueur
"""
import sqlite3
import random
import os
from datetime import datetime

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# Configuration Kingo
KINGO_PSEUDO = "Kingo"
KINGO_EMAIL = "kingo@elitepronos.com"
KINGO_PIN = "K1NG0_B0T"
KINGO_PRENOM = "Le Roi"


def get_or_create_kingo():
    """
    Recupere ou cree l'utilisateur Kingo
    Retourne l'ID de Kingo
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verifier si Kingo existe
    cursor.execute("SELECT id FROM utilisateurs WHERE pseudo = ?", (KINGO_PSEUDO,))
    result = cursor.fetchone()

    if result:
        conn.close()
        return result[0]

    # Creer Kingo
    cursor.execute("""
        INSERT INTO utilisateurs (pseudo, email, pin, prenom, statut, is_admin)
        VALUES (?, ?, ?, ?, 'Actif', 0)
    """, (KINGO_PSEUDO, KINGO_EMAIL, KINGO_PIN, KINGO_PRENOM))

    kingo_id = cursor.lastrowid

    # Ajouter les jokers pour Kingo
    try:
        cursor.execute("""
            INSERT INTO jokers_stock (user_id, joker_double_restants, joker_vole_restants)
            VALUES (?, 3, 2)
        """, (kingo_id,))
    except:
        pass

    conn.commit()
    conn.close()

    print(f"[KINGO] Joueur Kingo cree avec ID {kingo_id}")
    return kingo_id


def generer_score_intelligent(cote_home, cote_away):
    """
    Genere un score realiste base sur les cotes
    Plus la cote est basse, plus l'equipe est susceptible de marquer
    """
    # Convertir les cotes en probabilites approximatives
    prob_home = 1 / cote_home if cote_home else 0.33
    prob_away = 1 / cote_away if cote_away else 0.33

    # Normaliser
    total = prob_home + prob_away
    prob_home /= total
    prob_away /= total

    # Generer les buts (0-4 max par equipe)
    # Plus de probabilite = plus de buts en moyenne
    buts_home = 0
    buts_away = 0

    # Simuler les buts pour home
    for _ in range(5):
        if random.random() < prob_home * 0.6:
            buts_home += 1

    # Simuler les buts pour away
    for _ in range(5):
        if random.random() < prob_away * 0.5:
            buts_away += 1

    # Limiter a 4 buts max
    buts_home = min(buts_home, 4)
    buts_away = min(buts_away, 4)

    return buts_home, buts_away


def calculer_mise_optimale(cotes, index_match):
    """
    Calcule la mise optimale basee sur les cotes (favoriser les favoris)
    Budget total: 100 pts, reparti sur 4 matchs
    """
    # Calculer l'equilibre des cotes pour chaque match
    ecarts = []
    for cote_h, cote_n, cote_a in cotes:
        # Ecart = difference entre favoris et outsider
        ecart = abs(cote_h - cote_a)
        ecarts.append(ecart)

    # Mises de base: 25 pts par match
    mises = [25, 25, 25, 25]

    if len(ecarts) >= 4:
        # Trouver le match le plus desequilibre (favori clair)
        idx_favori = ecarts.index(max(ecarts))
        # Et le plus equilibre (risque)
        idx_equilibre = ecarts.index(min(ecarts))

        # Ajuster: plus sur le favori, moins sur l'equilibre
        if idx_favori != idx_equilibre:
            mises[idx_favori] = min(40, mises[idx_favori] + 15)  # Max 40
            mises[idx_equilibre] = max(10, mises[idx_equilibre] - 15)  # Min 10

        # S'assurer que le total = 100
        diff = 100 - sum(mises)
        if diff != 0:
            # Ajuster le premier match qui peut absorber la difference
            for i in range(4):
                nouvelle_mise = mises[i] + diff
                if 10 <= nouvelle_mise <= 60:
                    mises[i] = nouvelle_mise
                    break

    return mises[index_match] if index_match < len(mises) else 25


def kingo_pronostique_semaine(semaine_id=None, saison_id=None):
    """
    Kingo fait ses pronostics pour la semaine
    Retourne True si succes, False sinon
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Recuperer l'ID de Kingo
        kingo_id = get_or_create_kingo()

        # Determiner la saison et semaine
        if saison_id is None:
            now = datetime.now()
            saison_id = now.year if now.month >= 8 else now.year - 1

        if semaine_id is None:
            # Trouver la semaine active
            cursor.execute("""
                SELECT DISTINCT semaine_id FROM matches
                WHERE saison_id = ? AND is_active = 1 AND score_final_home IS NULL
                ORDER BY semaine_id ASC LIMIT 1
            """, (saison_id,))
            result = cursor.fetchone()
            if result:
                semaine_id = result[0]
            else:
                print("[KINGO] Aucune semaine active trouvee")
                conn.close()
                return False

        # Verifier si Kingo a deja pronostique cette semaine
        cursor.execute("""
            SELECT COUNT(*) FROM predictions p
            JOIN matches m ON p.match_id = m.id
            WHERE p.user_id = ? AND m.semaine_id = ? AND m.saison_id = ?
        """, (kingo_id, semaine_id, saison_id))

        if cursor.fetchone()[0] > 0:
            print(f"[KINGO] Pronostics deja faits pour la semaine {semaine_id}")
            conn.close()
            return True

        # Recuperer les matchs de la semaine
        cursor.execute("""
            SELECT id, equipe_home, equipe_away, cote_home, cote_draw, cote_away
            FROM matches
            WHERE semaine_id = ? AND saison_id = ? AND is_active = 1
            ORDER BY id
            LIMIT 4
        """, (semaine_id, saison_id))

        matchs = cursor.fetchall()

        if not matchs:
            print(f"[KINGO] Aucun match trouve pour la semaine {semaine_id}")
            conn.close()
            return False

        # Preparer les cotes pour le calcul des mises
        cotes = [(m[3], m[4], m[5]) for m in matchs]

        print(f"[KINGO] Genere les pronostics pour la semaine {semaine_id}...")

        # Generer les pronostics
        for idx, match in enumerate(matchs):
            match_id, home, away, cote_h, cote_n, cote_a = match

            # Generer le score
            score_home, score_away = generer_score_intelligent(cote_h, cote_a)

            # Calculer la mise
            mise = calculer_mise_optimale(cotes, idx)

            # Inserer le pronostic
            cursor.execute("""
                INSERT INTO predictions (user_id, match_id, score_prono_home, score_prono_away, mise_points, points_gagnes)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (kingo_id, match_id, score_home, score_away, mise))

            print(f"  -> {home} vs {away}: {score_home}-{score_away} ({mise} pts)")

        conn.commit()
        conn.close()

        print(f"[KINGO] Pronostics enregistres pour la semaine {semaine_id}")
        return True

    except Exception as e:
        print(f"[KINGO] Erreur: {str(e)}")
        conn.close()
        return False


def kingo_generer_message_accueil(semaine_id=None):
    """
    Genere un message d'accueil personnalise pour Kingo
    """
    messages = [
        "Encore une semaine ou je vais dominer ! Qui ose me defier ?",
        "Les favoris ne gagnent pas toujours... sauf quand c'est moi qui les choisit !",
        "J'ai analyse les cotes, etudie les stats. Preparez-vous a perdre.",
        "Le roi des pronostics est pret. Et vous ?",
        "Cette semaine, je sens le Grand Chelem arriver !",
        "Mes algorithmes ne mentent jamais. Enfin, presque jamais...",
        "Vous pensez pouvoir me battre ? J'adore les optimistes !",
        "Les cotes sont mes amies. La victoire est ma destinee.",
    ]

    return random.choice(messages)


if __name__ == "__main__":
    print("=== KINGO BOT - Test ===")
    kingo_id = get_or_create_kingo()
    print(f"Kingo ID: {kingo_id}")
    kingo_pronostique_semaine()
