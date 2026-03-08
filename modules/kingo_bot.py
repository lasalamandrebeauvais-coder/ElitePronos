"""
Module Kingo Bot pour Elite Pronos
Le roi des pronostics - IA qui participe comme un joueur
Version Supabase
"""
import random
from datetime import datetime

# Import Supabase
from modules.supabase_db import get_supabase
from modules.database_manager import get_saison_actuelle

# Configuration Kingo
KINGO_PSEUDO = "Kingo"
KINGO_EMAIL = "kingo@elitepronos.com"
KINGO_PIN = "K1NG0_B0T"
KINGO_PRENOM = "Le Roi"


def get_or_create_kingo():
    """
    Recupere ou cree l'utilisateur Kingo dans Supabase
    Retourne l'ID de Kingo
    """
    supabase = get_supabase()

    try:
        # Verifier si Kingo existe
        result = supabase._request('GET', f'utilisateurs?pseudo=eq.{KINGO_PSEUDO}&select=id')

        if result and len(result) > 0:
            return result[0]['id']

        # Creer Kingo
        new_user = {
            'pseudo': KINGO_PSEUDO,
            'email': KINGO_EMAIL,
            'pin': KINGO_PIN,
            'prenom': KINGO_PRENOM,
            'statut': 'Actif',
            'is_admin': False,
            'is_bot': True,
            'reglement_accepte': True
        }
        created = supabase._request('POST', 'utilisateurs', new_user)

        if created and len(created) > 0:
            kingo_id = created[0]['id']

            # Initialiser le stock de jokers pour Kingo
            saison_id = get_saison_actuelle()
            supabase.init_stock_jokers(kingo_id, saison_id)

            print(f"[KINGO] Joueur Kingo cree avec ID {kingo_id}")
            return kingo_id

        return None

    except Exception as e:
        print(f"[KINGO] Erreur get_or_create_kingo: {e}")
        return None


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
    ecarts = []
    for cote_h, cote_n, cote_a in cotes:
        ecart = abs(cote_h - cote_a) if cote_h and cote_a else 0
        ecarts.append(ecart)

    # Mises de base: 25 pts par match
    mises = [25, 25, 25, 25]

    if len(ecarts) >= 4:
        idx_favori = ecarts.index(max(ecarts))
        idx_equilibre = ecarts.index(min(ecarts))

        if idx_favori != idx_equilibre:
            mises[idx_favori] = min(40, mises[idx_favori] + 15)
            mises[idx_equilibre] = max(10, mises[idx_equilibre] - 15)

        # S'assurer que le total = 100
        diff = 100 - sum(mises)
        if diff != 0:
            for i in range(4):
                nouvelle_mise = mises[i] + diff
                if 10 <= nouvelle_mise <= 60:
                    mises[i] = nouvelle_mise
                    break

    return mises[index_match] if index_match < len(mises) else 25


def kingo_pronostique_semaine(semaine_id=None, saison_id=None, force=False):
    """
    Kingo fait ses pronostics pour la semaine
    Retourne True si succes, False sinon
    force=True pour refaire les pronostics meme s'ils existent
    """
    supabase = get_supabase()

    try:
        # Recuperer l'ID de Kingo
        kingo_id = get_or_create_kingo()
        if not kingo_id:
            print("[KINGO] Impossible de creer/recuperer Kingo")
            return False

        # Determiner la saison
        if saison_id is None:
            saison_id = get_saison_actuelle()

        # Determiner la semaine (journee courante)
        if semaine_id is None:
            saisons = supabase._request('GET', f'saisons?id=eq.{saison_id}&select=journee_courante')
            if saisons and len(saisons) > 0:
                semaine_id = saisons[0].get('journee_courante', 1)
            else:
                print("[KINGO] Aucune saison active trouvee")
                return False

        # Verifier si Kingo a deja pronostique cette semaine
        existing = supabase._request('GET',
            f'predictions?user_id=eq.{kingo_id}&saison_id=eq.{saison_id}&select=id,match_id'
        )

        # Recuperer les matchs de la semaine
        matchs = supabase._request('GET',
            f'matches?semaine_id=eq.{semaine_id}&saison_id=eq.{saison_id}&is_active=eq.true&select=id,equipe_home,equipe_away,cote_home,cote_draw,cote_away&order=id'
        )

        if not matchs or len(matchs) == 0:
            print(f"[KINGO] Aucun match trouve pour la journee {semaine_id}")
            return False

        # Verifier si Kingo a deja pronostique ces matchs
        match_ids = [m['id'] for m in matchs]
        if existing:
            existing_match_ids = [p['match_id'] for p in existing]
            has_pronos = any(mid in existing_match_ids for mid in match_ids)

            if has_pronos and not force:
                print(f"[KINGO] Pronostics deja faits pour la journee {semaine_id}")
                return True

            # Si force=True, supprimer les anciens pronostics pour ces matchs
            if force:
                for match_id in match_ids:
                    supabase._request('DELETE', f'predictions?user_id=eq.{kingo_id}&match_id=eq.{match_id}')
                print(f"[KINGO] Anciens pronostics supprimes, regeneration...")

        # Preparer les cotes pour le calcul des mises
        cotes = [(m.get('cote_home', 2.0), m.get('cote_draw', 3.0), m.get('cote_away', 2.0)) for m in matchs]

        print(f"[KINGO] Genere les pronostics pour la journee {semaine_id}...")

        # Generer les pronostics
        for idx, match in enumerate(matchs[:4]):  # Max 4 matchs
            match_id = match['id']
            home = match['equipe_home']
            away = match['equipe_away']
            cote_h = match.get('cote_home', 2.0) or 2.0
            cote_a = match.get('cote_away', 2.0) or 2.0

            # Generer le score
            score_home, score_away = generer_score_intelligent(cote_h, cote_a)

            # Calculer la mise
            mise = calculer_mise_optimale(cotes, idx)

            # Inserer le pronostic
            pred_data = {
                'user_id': kingo_id,
                'match_id': match_id,
                'saison_id': saison_id,
                'score_prono_home': score_home,
                'score_prono_away': score_away,
                'mise_points': mise,
                'points_gagnes': 0
            }
            supabase._request('POST', 'predictions', pred_data)

            print(f"  -> {home} vs {away}: {score_home}-{score_away} ({mise} pts)")

        print(f"[KINGO] Pronostics enregistres pour la journee {semaine_id}")
        return True

    except Exception as e:
        print(f"[KINGO] Erreur: {str(e)}")
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
