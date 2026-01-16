"""
Script de Test pour la Phase Finale
Elite Pronos - Validation Pluriannuelle et SMTP
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database_manager import (
    init_database,
    get_saison_actuelle,
    get_saison_label,
    get_setting,
    set_setting,
    is_mode_officiel,
    get_countdown_j1,
    inscriptions_ouvertes,
    get_stock_jokers,
    reset_jokers_nouvelle_saison
)

def print_header(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")


def print_test(name, passed, details=""):
    status = "[OK]" if passed else "[X]"
    print(f"  {status} {name}")
    if details:
        print(f"      -> {details}")


def test_saison():
    """Test gestion des saisons"""
    print_header("TEST: Gestion des Saisons")

    all_passed = True

    # Test saison actuelle
    saison = get_saison_actuelle()
    passed = saison >= 2024
    all_passed = all_passed and passed
    print_test("Saison actuelle", passed, f"Saison: {saison}")

    # Test label saison
    label = get_saison_label(saison)
    passed = f"{saison}-{saison+1}" == label
    all_passed = all_passed and passed
    print_test("Label saison", passed, f"Label: {label}")

    return all_passed


def test_settings():
    """Test parametres application"""
    print_header("TEST: Parametres Application")

    all_passed = True

    # Test is_officiel
    is_off = is_mode_officiel()
    passed = isinstance(is_off, bool)
    all_passed = all_passed and passed
    print_test("Mode officiel", passed, f"is_officiel: {is_off}")

    # Test get/set setting
    original = get_setting('is_officiel')
    set_setting('is_officiel', 'True')
    new_val = get_setting('is_officiel')
    passed = new_val == 'True'
    set_setting('is_officiel', original or 'False')  # Restaurer
    all_passed = all_passed and passed
    print_test("Get/Set settings", passed)

    return all_passed


def test_countdown():
    """Test countdown J1"""
    print_header("TEST: Countdown J1")

    all_passed = True

    # Test countdown
    countdown = get_countdown_j1()
    # countdown peut etre None si pas de J1 definie
    passed = countdown is None or isinstance(countdown, dict)
    all_passed = all_passed and passed
    print_test("Countdown J1", passed, f"Countdown: {countdown}")

    # Test inscriptions
    inscr = inscriptions_ouvertes()
    passed = isinstance(inscr, bool)
    all_passed = all_passed and passed
    print_test("Inscriptions ouvertes", passed, f"Ouvertes: {inscr}")

    return all_passed


def test_jokers_saison():
    """Test gestion jokers par saison"""
    print_header("TEST: Jokers par Saison")

    all_passed = True

    saison = get_saison_actuelle()

    # Test stock avec saison
    stock = get_stock_jokers(1, saison)
    passed = 'doubles' in stock and 'voles' in stock
    all_passed = all_passed and passed
    print_test("Stock jokers saison", passed, f"Stock: {stock}")

    return all_passed


def test_notifier():
    """Test module notifier"""
    print_header("TEST: Module Notifier")

    all_passed = True

    try:
        from modules.notifier_st import (
            get_smtp_config,
            email_bienvenue,
            email_lancement_saison,
            test_email_template
        )

        # Test config SMTP
        config = get_smtp_config()
        passed = 'host' in config and 'port' in config
        all_passed = all_passed and passed
        print_test("Config SMTP", passed)

        # Test templates
        user_test = {'id': 1, 'pseudo': 'Test', 'prenom': 'Jean', 'email': 'test@test.com'}
        html = email_bienvenue(user_test)
        passed = 'Elite Pronos' in html and 'Test' in html
        all_passed = all_passed and passed
        print_test("Template bienvenue", passed, f"{len(html)} chars")

        html = email_lancement_saison(user_test)
        passed = 'nouvelle saison' in html.lower() or 'saison' in html.lower()
        all_passed = all_passed and passed
        print_test("Template lancement", passed, f"{len(html)} chars")

    except ImportError as e:
        print_test("Import notifier", False, str(e))
        all_passed = False

    return all_passed


def test_sourcing():
    """Test module sourcing"""
    print_header("TEST: Module Sourcing")

    all_passed = True

    try:
        from modules.bot_sourcing import get_saison_actuelle as bot_saison
        saison = bot_saison()
        passed = saison >= 2024
        all_passed = all_passed and passed
        print_test("Sourcing saison", passed, f"Saison: {saison}")

    except ImportError as e:
        print_test("Import sourcing", False, str(e))
        all_passed = False

    return all_passed


def run_all_tests():
    """Execute tous les tests"""
    print(f"\n{'#'*60}")
    print(f"# ELITE PRONOS - TESTS PHASE FINALE")
    print(f"# Pluriannuel, SMTP, Countdown")
    print(f"{'#'*60}")

    # Initialiser la base
    print("\nInitialisation de la base de donnees...")
    init_database()

    # Executer les tests
    results = []

    results.append(("Gestion Saisons", test_saison()))
    results.append(("Parametres App", test_settings()))
    results.append(("Countdown J1", test_countdown()))
    results.append(("Jokers Saison", test_jokers_saison()))
    results.append(("Module Notifier", test_notifier()))
    results.append(("Module Sourcing", test_sourcing()))

    # Resume
    print_header("RESUME DES TESTS")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[OK]" if result else "[X]"
        print(f"  {status} {name}")

    print(f"\nResultat: {passed}/{total} tests reussis")

    if passed == total:
        print(f"\n{'='*60}")
        print(f"   PHASE FINALE VALIDEE !")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"   CERTAINS TESTS ONT ECHOUE")
        print(f"{'='*60}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
