import tkinter as tk
from tkinter import messagebox
import sqlite3
import os

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# --- FONCTION DE DETECTION DU BUDGET ---
def detecter_budget():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT grand_chelem_valide FROM historique ORDER BY rowid DESC LIMIT 1")
        resultat = cursor.fetchone()
        conn.close()
        return 140 if (resultat and resultat[0] == 1) else 100
    except:
        return 100

BUDGET_ACTUEL = detecter_budget()

# --- LOGIQUE DE VERROUILLAGE DES JOKERS ---
def gerer_exclusivite(joker_type):
    """Empêche de cocher deux jokers en même temps"""
    if joker_type == "double" and var_joker_double.get() == 1:
        var_joker_vole.set(0) # Décoche Volé
    elif joker_type == "vole" and var_joker_vole.get() == 1:
        var_joker_double.set(0) # Décoche Double

def valider_pronos():
    total_mises = 0
    data_to_save = []
    
    for i in range(len(matchs)):
        m_id = matchs[i][0]
        sh = scores_home_vars[i].get()
        sa = scores_away_vars[i].get()
        try:
            mi = int(mises_vars[i].get())
        except:
            messagebox.showerror("Erreur", "Mise invalide")
            return
        
        if mi < 10 or mi > 60:
            messagebox.showerror("Règle", f"Match {i+1} : Mise entre 10 et 60 pts.")
            return
        
        total_mises += mi
        data_to_save.append((m_id, sh, sa, mi))
    
    if total_mises != BUDGET_ACTUEL:
        messagebox.showerror("Budget", f"Total : {total_mises}/{BUDGET_ACTUEL} pts.")
        return

    # --- SAUVEGARDE AVEC JOKER DE JOURNÉE ---
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # MISE À JOUR : On s'assure que la table pour stocker le joker existe
    cursor.execute("CREATE TABLE IF NOT EXISTS joker_semaine (id INTEGER PRIMARY KEY, type TEXT)")
    
    # On vide les anciens pronos et l'ancien joker enregistré
    cursor.execute("DELETE FROM pronostics")
    cursor.execute("DELETE FROM joker_semaine")
    
    # On enregistre les pronos
    cursor.executemany("INSERT INTO pronostics (match_id, score_home_prono, score_away_prono, mise) VALUES (?, ?, ?, ?)", data_to_save)
    
    # MISE À JOUR : Enregistrement du joker actif dans la base de données
    joker_actif = "AUCUN"
    if var_joker_double.get(): joker_actif = "DOUBLE"
    elif var_joker_vole.get(): joker_actif = "VOLE"
    
    cursor.execute("INSERT INTO joker_semaine (type) VALUES (?)", (joker_actif,))
    
    conn.commit()
    conn.close()
    
    # Message de confirmation précis
    messagebox.showinfo("Succès", f"Pronos validés !\nJoker utilisé cette semaine : {joker_actif}")
    root.destroy()

# --- CHARGEMENT ---
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT rowid, equipe_home, equipe_away, cote_home, cote_draw, cote_away FROM matches LIMIT 4")
matchs = cursor.fetchall()
conn.close()

root = tk.Tk()
root.title("Pronos Expert - Saisie")
root.geometry("450x750")
root.configure(bg="#01013D")

tk.Label(root, text="PRONOS EXPERT", font=("Arial", 16, "bold"), bg="#01013D", fg="#FFD700").pack(pady=10)

# --- ZONE JOKERS DE LA JOURNÉE (EXCLUSIFS) ---
joker_frame = tk.LabelFrame(root, text=" JOKER DE LA SEMAINE (1 MAX) ", bg="#01013D", fg="#D4AF37", font=("Arial", 9, "bold"))
joker_frame.pack(fill="x", padx=30, pady=10)

var_joker_double = tk.IntVar()
var_joker_vole = tk.IntVar()

tk.Checkbutton(joker_frame, text="POINTS DOUBLES (x2)", variable=var_joker_double, 
               bg="#01013D", fg="white", selectcolor="#0A183D",
               command=lambda: gerer_exclusivite("double")).pack(side="left", padx=20, pady=5)

tk.Checkbutton(joker_frame, text="POINTS VOLÉS", variable=var_joker_vole, 
               bg="#01013D", fg="white", selectcolor="#0A183D",
               command=lambda: gerer_exclusivite("vole")).pack(side="left", padx=20, pady=5)

# --- LISTE DES MATCHS ---
scores_home_vars, scores_away_vars, mises_vars = [], [], []

for m in matchs:
    m_id, home, away, ch, cd, ca = m
    f = tk.Frame(root, bd=1, highlightbackground="#2c3e50", highlightthickness=1, bg="#0A183D")
    f.pack(fill="x", padx=20, pady=5)
    
    tk.Label(f, text=f"{home} vs {away}", font=("Arial", 9, "bold"), bg="#0A183D", fg="white").pack()
    
    sf = tk.Frame(f, bg="#0A183D")
    sf.pack()
    sh_v = tk.IntVar(value=0); sa_v = tk.IntVar(value=0); m_v = tk.StringVar(value="25")
    scores_home_vars.append(sh_v); scores_away_vars.append(sa_v); mises_vars.append(m_v)
    
    tk.Spinbox(sf, from_=0, to=9, textvariable=sh_v, width=2).pack(side="left", padx=5)
    tk.Label(sf, text="-", bg="#0A183D", fg="white").pack(side="left")
    tk.Spinbox(sf, from_=0, to=9, textvariable=sa_v, width=2).pack(side="left", padx=5)
    
    tk.Label(f, text="Mise:", bg="#0A183D", fg="white", font=("Arial", 8)).pack(side="left", padx=10)
    tk.Spinbox(f, from_=10, to=60, textvariable=m_v, width=4).pack(side="left")

tk.Button(root, text="VALIDER LA SEMAINE", bg="#FFD700", fg="#01013D", font=("Arial", 10, "bold"), 
          command=valider_pronos).pack(pady=20)

root.mainloop()