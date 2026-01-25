# ============================================
# Module Supabase pour Elite Pronos
# Utilise l'API REST (compatible Windows/Streamlit Cloud)
# ============================================

import requests
import os

# Configuration par defaut
DEFAULT_SUPABASE_URL = "https://qyyfxbwyvshpuuqwrxsl.supabase.co"
DEFAULT_SUPABASE_KEY = "sb_secret_v_cT_G2XV1znRhrS0cx_qw_6vZmzMKW"

class SupabaseClient:
    """Client Supabase utilisant l'API REST"""

    def __init__(self, url=None, key=None):
        # Essayer de recuperer depuis les secrets Streamlit (prioritaire)
        try:
            import streamlit as st
            # Utiliser st.secrets["KEY"] (pas .get())
            self.url = url or st.secrets["SUPABASE_URL"]
            self.key = key or st.secrets["SUPABASE_KEY"]
        except Exception:
            # Fallback: variables d'environnement ou valeurs par defaut
            self.url = url or os.getenv("SUPABASE_URL", DEFAULT_SUPABASE_URL)
            self.key = key or os.getenv("SUPABASE_KEY", DEFAULT_SUPABASE_KEY)

        self.headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }

    def _request(self, method, endpoint, data=None, params=None):
        """Execute une requete API"""
        url = f"{self.url}/rest/v1/{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=data, params=params)

        if response.status_code >= 400:
            print(f"Erreur Supabase: {response.status_code} - {response.text}")
            return None

        try:
            return response.json()
        except:
            return response.text

    # ============================================
    # UTILISATEURS
    # ============================================

    def get_utilisateur_by_pseudo(self, pseudo):
        """Recupere un utilisateur par son pseudo"""
        result = self._request('GET', f'utilisateurs?pseudo=eq.{pseudo}&select=*')
        return result[0] if result else None

    def get_utilisateur_by_id(self, user_id):
        """Recupere un utilisateur par son ID"""
        result = self._request('GET', f'utilisateurs?id=eq.{user_id}&select=*')
        return result[0] if result else None

    def get_all_utilisateurs(self, statut=None):
        """Recupere tous les utilisateurs"""
        endpoint = 'utilisateurs?select=*'
        if statut:
            endpoint += f'&statut=eq.{statut}'
        return self._request('GET', endpoint) or []

    def create_utilisateur(self, data):
        """Cree un nouvel utilisateur"""
        result = self._request('POST', 'utilisateurs', data)
        return result[0] if result else None

    def update_utilisateur(self, user_id, data):
        """Met a jour un utilisateur"""
        result = self._request('PATCH', f'utilisateurs?id=eq.{user_id}', data)
        return result[0] if result else None

    def check_login(self, pseudo, pin):
        """Verifie les credentials de connexion"""
        result = self._request('GET', f'utilisateurs?pseudo=eq.{pseudo}&pin=eq.{pin}&select=*')
        return result[0] if result else None

    # ============================================
    # MATCHES
    # ============================================

    def get_matches_journee(self, saison_id, semaine_id):
        """Recupere les matchs d'une journee"""
        return self._request('GET',
            f'matches?saison_id=eq.{saison_id}&semaine_id=eq.{semaine_id}&is_active=eq.true&select=*&order=date_match'
        ) or []

    def get_match_by_id(self, match_id):
        """Recupere un match par son ID"""
        result = self._request('GET', f'matches?id=eq.{match_id}&select=*')
        return result[0] if result else None

    def update_match_score(self, match_id, score_home, score_away, status='FINISHED'):
        """Met a jour le score final d'un match"""
        return self._request('PATCH', f'matches?id=eq.{match_id}', {
            'score_final_home': score_home,
            'score_final_away': score_away,
            'status': status
        })

    def update_match_live(self, match_id, score_home, score_away, status='IN_PLAY'):
        """Met a jour le score live d'un match"""
        return self._request('PATCH', f'matches?id=eq.{match_id}', {
            'score_mi_temps_home': score_home,
            'score_mi_temps_away': score_away,
            'status': status
        })

    def get_matches_by_status(self, status_list):
        """Recupere les matchs par statut"""
        statuses = ','.join(status_list)
        return self._request('GET', f'matches?status=in.({statuses})&select=*') or []

    # ============================================
    # PREDICTIONS
    # ============================================

    def get_predictions_user_journee(self, user_id, saison_id, semaine_id):
        """Recupere les predictions d'un utilisateur pour une journee"""
        return self._request('GET',
            f'predictions?user_id=eq.{user_id}&saison_id=eq.{saison_id}&select=*,matches(equipe_home,equipe_away,semaine_id,score_final_home,score_final_away,cote_home,cote_draw,cote_away)&matches.semaine_id=eq.{semaine_id}'
        ) or []

    def get_predictions_journee(self, saison_id, semaine_id):
        """Recupere toutes les predictions d'une journee"""
        # D'abord recuperer les IDs des matchs de cette journee
        matches = self.get_matches_journee(saison_id, semaine_id)
        if not matches:
            return []
        match_ids = [m['id'] for m in matches]
        match_ids_str = ','.join(map(str, match_ids))
        return self._request('GET',
            f'predictions?match_id=in.({match_ids_str})&select=*,utilisateurs(pseudo),matches(equipe_home,equipe_away,score_final_home,score_final_away,cote_home,cote_draw,cote_away)'
        ) or []

    def create_prediction(self, data):
        """Cree une nouvelle prediction"""
        result = self._request('POST', 'predictions', data)
        return result[0] if result else None

    def update_prediction_points(self, prediction_id, points_gagnes, is_score_exact=False):
        """Met a jour les points d'une prediction"""
        return self._request('PATCH', f'predictions?id=eq.{prediction_id}', {
            'points_gagnes': points_gagnes,
            'is_score_exact': is_score_exact
        })

    def get_predictions_to_calculate(self, match_id):
        """Recupere les predictions a calculer pour un match"""
        return self._request('GET',
            f'predictions?match_id=eq.{match_id}&select=*,utilisateurs(pseudo)'
        ) or []

    # ============================================
    # JOKERS
    # ============================================

    def get_joker_semaine(self, user_id, semaine_id):
        """Recupere le joker utilise par un utilisateur cette semaine"""
        result = self._request('GET',
            f'jokers_historique?utilisateur_id=eq.{user_id}&semaine_id=eq.{semaine_id}&select=*'
        )
        return result[0] if result else None

    def create_joker(self, data):
        """Enregistre l'utilisation d'un joker"""
        result = self._request('POST', 'jokers_historique', data)
        return result[0] if result else None

    def get_stock_jokers(self, user_id, saison_id=2025):
        """Recupere le stock de jokers d'un utilisateur"""
        result = self._request('GET',
            f'stock_jokers?utilisateur_id=eq.{user_id}&saison_id=eq.{saison_id}&select=*'
        )
        return result[0] if result else None

    # ============================================
    # SAISONS
    # ============================================

    def get_saison_active(self):
        """Recupere la saison active"""
        result = self._request('GET', 'saisons?is_active=eq.true&select=*')
        return result[0] if result else None

    def get_journee_courante(self):
        """Recupere la journee courante"""
        saison = self.get_saison_active()
        return saison['journee_courante'] if saison else 1

    # ============================================
    # CLASSEMENT
    # ============================================

    def get_classement_general(self, saison_id):
        """Calcule le classement general"""
        # Recuperer tous les utilisateurs actifs avec leurs points
        utilisateurs = self.get_all_utilisateurs(statut='Actif')
        classement = []

        for user in utilisateurs:
            # Calculer les points totaux
            predictions = self._request('GET',
                f'predictions?user_id=eq.{user["id"]}&saison_id=eq.{saison_id}&select=points_gagnes,is_score_exact'
            ) or []

            total_points = sum(p.get('points_gagnes', 0) or 0 for p in predictions)
            scores_exacts = sum(1 for p in predictions if p.get('is_score_exact'))
            nb_pronos = len(predictions)

            classement.append({
                'pseudo': user['pseudo'],
                'points': total_points,
                'scores_exacts': scores_exacts,
                'nb_pronos': nb_pronos
            })

        # Trier par points decroissants
        classement.sort(key=lambda x: x['points'], reverse=True)
        return classement


# Instance globale
_client = None

def get_supabase():
    """Retourne le client Supabase (singleton)"""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client


def test_connexion():
    """Teste la connexion a Supabase"""
    try:
        client = get_supabase()
        saison = client.get_saison_active()
        if saison:
            print(f"Connexion Supabase OK - Saison {saison['annee_debut']}-{saison['annee_fin']}, J{saison['journee_courante']}")
            return True
        else:
            print("Connexion OK mais pas de saison active")
            return True
    except Exception as e:
        print(f"Erreur connexion Supabase: {e}")
        return False


if __name__ == "__main__":
    # Test
    test_connexion()
    client = get_supabase()
    print("\nUtilisateurs:", client.get_all_utilisateurs())
    print("\nMatchs J19:", client.get_matches_journee(2025, 19))
