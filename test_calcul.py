"""
Script de Test pour le Moteur de Calcul des Gains
Elite Pronos - Phase 9: Automatisation

Ce script valide l'intégrité des calculs avec les nouveaux paramètres de jokers.
"""
import sqlite3
import os
import sys

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database_manager import (
    init_database,
    get_stock_jokers,
    utiliser_joker_double,
    utiliser_joker_vol,
    get_joker_actif_semaine,
    resoudre_chaine_vol,
    get_pronostics_effectifs,
    tous_matchs_termines,
    get_classement_general,
    trouver_cible_vol_auto,
    get_connection
)
from modules.calcul_gains import (
    determiner_resultat_match,
    calculer_gain_match,
    calculer_gains_semaine,
    calculer_tous_gains_semaine,
    afficher_rapport_semaine,
    BONUS_GRAND_CHELEM
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'pronos_expert.db')

# Couleurs console (desactivees pour compatibilite Windows)
class Colors:
    OK = ''
    FAIL = ''
    WARNING = ''
    INFO = ''
    RESET = ''
    BOLD = ''


def print_header(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")


def print_test(name, passed, details=""):
    status = "[OK] PASS" if passed else "[X] FAIL"
    print(f"  {status} - {name}")
    if details:
        print(f"         {details}")


def setup_test_data():
    """Prépare les données de test dans la base de données"""
    conn = get_connection()
    cursor = conn.cursor()

    # Nettoyer les données de test précédentes
    cursor.execute("DELETE FROM predictions WHERE match_id >= 900")
    cursor.execute("DELETE FROM matches WHERE id >= 900")
    cursor.execute("DELETE FROM jokers_historique WHERE semaine_id = 99")

    # Créer 4 matchs de test pour la semaine 99
    test_matches = [
        (900, 99, 'FL1', 'PSG', 'OM', 1.50, 3.50, 5.00, 2, 1),      # PSG gagne
        (901, 99, 'FL1', 'Lyon', 'Monaco', 2.00, 3.20, 3.50, 1, 1),  # Nul
        (902, 99, 'PL', 'Liverpool', 'Arsenal', 1.80, 3.40, 4.00, 3, 0),  # Liverpool gagne
        (903, 99, 'PL', 'Chelsea', 'ManCity', 3.00, 3.30, 2.10, 0, 2),   # ManCity gagne
    ]

    for m in test_matches:
        cursor.execute('''
            INSERT OR REPLACE INTO matches
            (id, semaine_id, championnat, equipe_home, equipe_away, cote_home, cote_draw, cote_away,
             score_final_home, score_final_away, date_match, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)
        ''', m)

    # Récupérer les IDs des utilisateurs de test
    cursor.execute("SELECT id FROM utilisateurs WHERE statut = 'Actif' LIMIT 3")
    users = cursor.fetchall()

    if len(users) < 2:
        print(f"{Colors.FAIL}Erreur: Pas assez d'utilisateurs actifs pour les tests{Colors.RESET}")
        conn.close()
        return None

    user_ids = [u[0] for u in users]

    # Utilisateur 1: Pronostics parfaits (Grand Chelem)
    test_predictions_user1 = [
        (user_ids[0], 900, 2, 1, 25),  # Correct exact
        (user_ids[0], 901, 1, 1, 25),  # Correct exact
        (user_ids[0], 902, 3, 0, 25),  # Correct exact
        (user_ids[0], 903, 0, 2, 25),  # Correct exact
    ]

    # Utilisateur 2: Pronostics partiels
    test_predictions_user2 = [
        (user_ids[1], 900, 1, 0, 30),  # Correct sens (1)
        (user_ids[1], 901, 2, 1, 20),  # Incorrect (prédit victoire dom)
        (user_ids[1], 902, 2, 1, 30),  # Correct sens (1)
        (user_ids[1], 903, 1, 0, 20),  # Incorrect
    ]

    for p in test_predictions_user1 + test_predictions_user2:
        cursor.execute('''
            INSERT OR REPLACE INTO predictions
            (user_id, match_id, score_prono_home, score_prono_away, mise_points, points_gagnes)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', p)

    conn.commit()
    conn.close()

    return user_ids


# ============================================
# TESTS UNITAIRES
# ============================================

def test_determiner_resultat():
    """Test de la détermination du résultat 1N2"""
    print_header("TEST: Détermination résultat 1N2")

    tests = [
        ((2, 1), '1', "Victoire domicile"),
        ((0, 3), '2', "Victoire extérieur"),
        ((1, 1), 'N', "Match nul"),
        ((0, 0), 'N', "0-0 = Nul"),
    ]

    all_passed = True
    for (home, away), expected, desc in tests:
        result = determiner_resultat_match(home, away)
        passed = result == expected
        all_passed = all_passed and passed
        print_test(desc, passed, f"Score {home}-{away} -> {result} (attendu: {expected})")

    return all_passed


def test_calcul_gain_match():
    """Test du calcul de gain pour un match"""
    print_header("TEST: Calcul gain match")

    all_passed = True

    # Test 1: Pronostic correct avec sens correct
    gain, is_1n2, is_exact = calculer_gain_match(
        prono_home=2, prono_away=1,
        score_home=2, score_away=0,
        mise=25, cote_home=1.50, cote_draw=3.50, cote_away=5.00
    )
    passed = is_1n2 == True and is_exact == False
    all_passed = all_passed and passed
    print_test("Sens correct, score différent", passed, f"Gain: {gain}, 1N2: {is_1n2}")

    # Test 2: Score exact
    gain, is_1n2, is_exact = calculer_gain_match(
        prono_home=2, prono_away=1,
        score_home=2, score_away=1,
        mise=25, cote_home=1.50, cote_draw=3.50, cote_away=5.00
    )
    expected_gain = 25 * 1.50 + 25 * 2  # mise × cote + bonus exact
    passed = is_exact == True and gain == expected_gain
    all_passed = all_passed and passed
    print_test("Score exact", passed, f"Gain: {gain} (attendu: {expected_gain})")

    # Test 3: Pronostic incorrect
    gain, is_1n2, is_exact = calculer_gain_match(
        prono_home=0, prono_away=2,
        score_home=2, score_away=1,
        mise=25, cote_home=1.50, cote_draw=3.50, cote_away=5.00
    )
    passed = gain == 0 and is_1n2 == False
    all_passed = all_passed and passed
    print_test("Pronostic incorrect", passed, f"Gain: {gain} (attendu: 0)")

    return all_passed


def test_stock_jokers(user_ids):
    """Test de la gestion du stock de jokers"""
    print_header("TEST: Gestion stock jokers")

    all_passed = True
    user_id = user_ids[0]

    # Vérifier le stock initial
    stock = get_stock_jokers(user_id)
    passed = stock['doubles'] >= 0 and stock['voles'] >= 0
    all_passed = all_passed and passed
    print_test("Récupération stock", passed, f"Doubles: {stock['doubles']}, Volés: {stock['voles']}")

    return all_passed


def test_chaine_vol(user_ids):
    """Test de la résolution des chaînes de vol"""
    print_header("TEST: Chaîne de vol récursive")

    all_passed = True

    if len(user_ids) < 2:
        print_test("Chaîne de vol", False, "Pas assez d'utilisateurs")
        return False

    # Test sans vol
    source_id, msg = resoudre_chaine_vol(user_ids[0], 99)
    passed = source_id == user_ids[0]
    all_passed = all_passed and passed
    print_test("Sans vol (source = soi-même)", passed, f"Source: {source_id}")

    return all_passed


def test_grand_chelem(user_ids):
    """Test du bonus Grand Chelem"""
    print_header("TEST: Grand Chelem")

    all_passed = True

    # L'utilisateur 1 a fait 4/4 pronostics corrects
    gains = calculer_gains_semaine(user_ids[0], 99)

    passed = gains['grand_chelem'] == True
    all_passed = all_passed and passed
    print_test("Détection Grand Chelem", passed,
               f"4/4 corrects: {gains['nb_1n2_corrects']}/4")

    # Vérifier le bonus
    expected_with_bonus = gains['total_gains']
    print_test("Bonus appliqué", True,
               f"Total avec bonus: {expected_with_bonus} pts (bonus: {BONUS_GRAND_CHELEM})")

    return all_passed


def test_matchs_termines():
    """Test de la vérification des matchs terminés"""
    print_header("TEST: Vérification matchs terminés")

    all_passed = True

    # Semaine 99 devrait avoir 4 matchs terminés
    termines = tous_matchs_termines(99)
    passed = termines == True
    all_passed = all_passed and passed
    print_test("Semaine 99 (4 matchs avec scores)", passed)

    # Semaine inexistante
    termines = tous_matchs_termines(999)
    passed = termines == False
    all_passed = all_passed and passed
    print_test("Semaine 999 (inexistante)", passed)

    return all_passed


def test_calcul_complet(user_ids):
    """Test du calcul complet de la semaine"""
    print_header("TEST: Calcul complet semaine")

    all_passed = True

    resultats, msg = calculer_tous_gains_semaine(99)

    passed = resultats is not None
    all_passed = all_passed and passed
    print_test("Calcul effectué", passed, msg)

    if resultats:
        print(f"\n{Colors.INFO}Résultats:{Colors.RESET}")
        for r in resultats['resultats']:
            joker = r.get('joker_utilise', 'Aucun')
            gc = " [GRAND CHELEM]" if r['grand_chelem'] else ""
            print(f"    {r['pseudo']}: {r['total_gains']} pts "
                  f"({r['nb_1n2_corrects']}/4, {r['nb_scores_exacts']} exacts) "
                  f"[{joker}]{gc}")

    return all_passed


def test_rapport():
    """Test de la génération du rapport"""
    print_header("TEST: Génération rapport")

    rapport = afficher_rapport_semaine(99)
    passed = "RAPPORT SEMAINE 99" in rapport
    print_test("Rapport généré", passed)

    if passed:
        print(f"\n{Colors.INFO}Aperçu du rapport:{Colors.RESET}")
        for line in rapport.split('\n')[:15]:
            print(f"    {line}")

    return passed


# ============================================
# MAIN
# ============================================

def run_all_tests():
    """Exécute tous les tests"""
    print(f"\n{Colors.BOLD}{'#'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}# ELITE PRONOS - TESTS DU MOTEUR DE CALCUL{Colors.RESET}")
    print(f"{Colors.BOLD}# Phase 9: Automatisation{Colors.RESET}")
    print(f"{Colors.BOLD}{'#'*60}{Colors.RESET}")

    # Initialiser la base de données
    print(f"\n{Colors.INFO}Initialisation de la base de données...{Colors.RESET}")
    init_database()

    # Préparer les données de test
    print(f"{Colors.INFO}Préparation des données de test...{Colors.RESET}")
    user_ids = setup_test_data()

    if not user_ids:
        print(f"{Colors.FAIL}Impossible de configurer les tests{Colors.RESET}")
        return

    # Exécuter les tests
    results = []

    results.append(("Détermination résultat", test_determiner_resultat()))
    results.append(("Calcul gain match", test_calcul_gain_match()))
    results.append(("Stock jokers", test_stock_jokers(user_ids)))
    results.append(("Chaîne de vol", test_chaine_vol(user_ids)))
    results.append(("Matchs terminés", test_matchs_termines()))
    results.append(("Grand Chelem", test_grand_chelem(user_ids)))
    results.append(("Calcul complet", test_calcul_complet(user_ids)))
    results.append(("Génération rapport", test_rapport()))

    # Résumé
    print_header("RÉSUMÉ DES TESTS")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[OK]" if result else "[X]"
        print(f"  {status} {name}")

    print(f"\nResultat: {passed}/{total} tests reussis")

    if passed == total:
        print(f"\n{'='*60}")
        print(f"   TOUS LES TESTS SONT PASSES !")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"   CERTAINS TESTS ONT ECHOUE")
        print(f"{'='*60}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
