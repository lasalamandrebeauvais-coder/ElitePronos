# Elite Pronos

Plateforme de pronostics football entre amis, developpee avec Streamlit.

## Fonctionnalites

- **Pronostics hebdomadaires** : 4 matchs par semaine, 100 points de budget
- **Systeme de Jokers** : Points Doubles (x2) et Points Voles
- **Grand Chelem** : Bonus +40 pts si 4/4 pronostics corrects
- **Classement en temps reel** : General, Hebdomadaire, Records
- **Gestion pluriannuelle** : Support de plusieurs saisons

## Installation locale

```bash
# Cloner le depot
git clone https://github.com/lasalamandrebeauvais-coder/ElitePronos.git
cd ElitePronos

# Creer l'environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installer les dependances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

## Deploiement Streamlit Cloud

1. Connectez votre depot GitHub a Streamlit Cloud
2. Configurez les secrets dans **Settings > Secrets** :

```toml
[secrets]
IS_OFFICIEL = "False"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "votre@email.com"
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"
```

3. L'application demarre automatiquement sur `app.py`

## Mode Test vs Mode Officiel

| Mode | IS_OFFICIEL | Emails | Usage |
|------|-------------|--------|-------|
| **Test** | False | Simules | Developpement |
| **Officiel** | True | Reels | Production |

Par defaut, l'application demarre en **Mode Test**.
L'admin peut activer le mode officiel via le panneau d'administration.

## Structure du projet

```
ElitePronos/
├── app.py                 # Point d'entree Streamlit
├── requirements.txt       # Dependances Python
├── database/              # Base SQLite (non versionnee)
├── modules/
│   ├── database_manager.py    # Gestion BDD et saisons
│   ├── calcul_gains.py        # Moteur de calcul des points
│   ├── notifier_st.py         # Systeme d'emails SMTP
│   ├── login_st.py            # Authentification
│   ├── inscription_st.py      # Inscription utilisateurs
│   ├── dashboard_st.py        # Tableau de bord
│   ├── pronostics_st.py       # Saisie des pronostics
│   ├── classement_st.py       # Classements
│   └── bot_sourcing.py        # Import matchs API
└── assets/
    └── avatars/           # Avatars utilisateurs
```

## Auteur

Projet developpe pour la ligue Elite Pronos - Saison 2024-2025

---

*Elite Pronos v1.0*
