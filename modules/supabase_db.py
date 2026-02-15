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

    def init_stock_jokers(self, user_id, saison_id=2025):
        """Initialise le stock de jokers pour un nouvel utilisateur"""
        # Verifier si le stock existe deja
        existing = self.get_stock_jokers(user_id, saison_id)
        if existing:
            return existing

        # Creer le stock initial: 3 jokers doubles + 2 jokers voles
        result = self._request('POST', 'stock_jokers', {
            'utilisateur_id': user_id,
            'saison_id': saison_id,
            'joker_double': 3,
            'joker_vol': 2
        })
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
    # RELATIONS / RIVAUX
    # ============================================

    def get_rivaux_ids(self, user_id):
        """Recupere les IDs des rivaux selectionnes par un utilisateur"""
        result = self._request('GET',
            f'relations?or=(utilisateur_id.eq.{user_id},ami_id.eq.{user_id})&statut=eq.amis&select=utilisateur_id,ami_id'
        ) or []
        rivaux = []
        for r in result:
            if r['utilisateur_id'] == user_id:
                rivaux.append(r['ami_id'])
            else:
                rivaux.append(r['utilisateur_id'])
        return rivaux

    def ajouter_rival(self, user_id, rival_id):
        """Ajoute un rival"""
        return self._request('POST', 'relations', {
            'utilisateur_id': user_id,
            'ami_id': rival_id,
            'statut': 'amis'
        })

    def supprimer_rival(self, user_id, rival_id):
        """Supprime un rival"""
        # Supprimer dans les deux sens
        self._request('DELETE',
            f'relations?utilisateur_id=eq.{user_id}&ami_id=eq.{rival_id}'
        )
        self._request('DELETE',
            f'relations?utilisateur_id=eq.{rival_id}&ami_id=eq.{user_id}'
        )
        return True

    def get_joueurs_avec_stats(self, current_user_id, saison_id=2025):
        """Recupere tous les joueurs actifs avec leurs stats pour selection rivaux
        Optimise: 2 requetes au lieu de N+1"""
        utilisateurs = self.get_all_utilisateurs(statut='Actif')

        # 1 seule requete pour TOUTES les predictions de la saison
        all_predictions = self._request('GET',
            f'predictions?saison_id=eq.{saison_id}&select=user_id,points_gagnes,is_score_exact'
        ) or []

        # Agreger par utilisateur
        user_stats = {}
        for p in all_predictions:
            uid = p['user_id']
            if uid not in user_stats:
                user_stats[uid] = {'points': 0, 'bons': 0, 'exacts': 0}
            pts = p.get('points_gagnes', 0) or 0
            user_stats[uid]['points'] += pts
            if pts > 0:
                user_stats[uid]['bons'] += 1
            if p.get('is_score_exact'):
                user_stats[uid]['exacts'] += 1

        joueurs = []
        for user in utilisateurs:
            if user['id'] == current_user_id:
                continue
            stats = user_stats.get(user['id'], {'points': 0, 'bons': 0, 'exacts': 0})
            joueurs.append({
                'id': user['id'],
                'pseudo': user['pseudo'],
                'prenom': user.get('prenom', ''),
                'points': stats['points'],
                'bons_pronos': stats['bons'],
                'scores_exacts': stats['exacts']
            })

        joueurs.sort(key=lambda x: x['points'], reverse=True)
        for idx, j in enumerate(joueurs):
            j['rang'] = idx + 1

        return joueurs

    # ============================================
    # CLASSEMENT
    # ============================================

    def get_classement_general(self, saison_id):
        """Calcule le classement general
        Optimise: 2 requetes au lieu de N+1"""
        utilisateurs = self.get_all_utilisateurs(statut='Actif')

        # 1 seule requete pour TOUTES les predictions
        all_predictions = self._request('GET',
            f'predictions?saison_id=eq.{saison_id}&select=user_id,points_gagnes,is_score_exact'
        ) or []

        # Agreger par utilisateur
        user_stats = {}
        for p in all_predictions:
            uid = p['user_id']
            if uid not in user_stats:
                user_stats[uid] = {'points': 0, 'exacts': 0, 'nb': 0}
            user_stats[uid]['points'] += (p.get('points_gagnes', 0) or 0)
            user_stats[uid]['nb'] += 1
            if p.get('is_score_exact'):
                user_stats[uid]['exacts'] += 1

        classement = []
        for user in utilisateurs:
            stats = user_stats.get(user['id'], {'points': 0, 'exacts': 0, 'nb': 0})
            classement.append({
                'pseudo': user['pseudo'],
                'points': stats['points'],
                'scores_exacts': stats['exacts'],
                'nb_pronos': stats['nb']
            })

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
