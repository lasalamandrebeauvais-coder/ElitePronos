import tkinter as tk
import sqlite3
import os

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

# --- CONFIGURATION DU CHAMPIONNAT ---
# Tu peux changer ce nombre ici, tout le reste suivra
NB_PARTICIPANTS = 100

def charger_donnees_completes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Stats globales
    cursor.execute("SELECT SUM(points_gagnes), COUNT(*), SUM(nb_scores_exacts), SUM(grand_chelem_valide) FROM historique")
    stats = cursor.fetchone()
    
    # 2. Records de classement
    cursor.execute("SELECT MIN(rang_semaine), MAX(rang_semaine) FROM historique")
    records = cursor.fetchone()
    
    # 3. Liste complète des semaines
    cursor.execute("SELECT semaine_no, points_gagnes, grand_chelem_valide, rang_semaine FROM historique ORDER BY semaine_no ASC")
    semaines = cursor.fetchall()
    
    conn.close()
    return stats, semaines, records

root = tk.Tk()
root.title("Elite Pronos - Dashboard Évolution")
root.geometry("500x780")
root.configure(bg="#0A0F1E")

# Récupération des données
stats, semaines, records = charger_donnees_completes()
total_pts = stats[0] if stats[0] else 0
total_scores_exacts = stats[2] if stats[2] else 0
total_chelems = stats[3] if stats[3] else 0
meilleur = records[0] if records[0] else "--"
pire = records[1] if records[1] else "--"

# Calcul de la tendance
tendance_texte = "Premier bilan"
tendance_color = "#4A90E2"
if len(semaines) >= 2:
    actuel = semaines[-1][3]
    precedent = semaines[-2][3]
    diff = precedent - actuel
    if diff > 0:
        tendance_texte = f"▲ +{diff} places gagnées"
        tendance_color = "#00FF41"
    elif diff < 0:
        tendance_texte = f"▼ {abs(diff)} places perdues"
        tendance_color = "#FF4B4B"
    else:
        tendance_texte = "▬ Position stable"

# --- TITRE ---
tk.Label(root, text="VOTRE ÉVOLUTION", font=("Segoe UI", 18, "bold"), bg="#0A0F1E", fg="#FFD700").pack(pady=(25, 10))

# --- SECTION CLASSEMENT (Adaptée dynamiquement) ---
rank_frame = tk.Frame(root, bg="#161B2D", padx=20, pady=15)
rank_frame.pack(fill="x", padx=40, pady=10)

place_actuelle = semaines[-1][3] if semaines else "--"
tk.Label(rank_frame, text="CLASSEMENT ACTUEL", font=("Segoe UI", 9), bg="#161B2D", fg="#4A90E2").pack()

# Affichage dynamique du nombre de participants
tk.Label(rank_frame, text=f"{place_actuelle}e / {NB_PARTICIPANTS}", font=("Segoe UI", 32, "bold"), bg="#161B2D", fg="white").pack()

tk.Label(rank_frame, text=tendance_texte, font=("Segoe UI", 11, "bold"), bg="#161B2D", fg=tendance_color).pack()

# --- SECTION RECORDS ---
records_frame = tk.Frame(root, bg="#0A0F1E", pady=5)
records_frame.pack(fill="x", padx=40)
tk.Label(records_frame, text=f"⭐ Record: {meilleur}e  |  🔻 Pire: {pire}e", font=("Segoe UI", 10), bg="#0A0F1E", fg="#E0E0E0").pack()

# --- SECTION STATS CUMULÉES ---
stats_mini = tk.Frame(root, bg="#0A0F1E")
stats_mini.pack(pady=10)
tk.Label(stats_mini, text=f"Total: {round(total_pts, 1)} pts  |  🎯 Exacts: {total_scores_exacts}", font=("Segoe UI", 9, "bold"), bg="#0A0F1E", fg="white").pack()

# --- SECTION CALENDRIER ---
tk.Label(root, text="HISTORIQUE DES SEMAINES", font=("Segoe UI", 10, "bold"), bg="#0A0F1E", fg="#4A90E2").pack(pady=(15, 5))

calendrier_frame = tk.Frame(root, bg="#0A0F1E")
calendrier_frame.pack(pady=5)

for i, sem in enumerate(semaines):
    s_no, pts, chelem, rg = sem
    if chelem == 1: bg_c, fg_c = "#FFD700", "#0A0F1E"
    elif pts >= 100: bg_c, fg_c = "#E0E0E0", "#0A0F1E"
    else: bg_c, fg_c = "#161B2D", "white"

    badge = tk.Frame(calendrier_frame, width=75, height=75, bg=bg_c)
    badge.grid(row=i//5, column=i%5, padx=6, pady=6)
    badge.grid_propagate(False)
    
    tk.Label(badge, text=f"S{s_no}", font=("Segoe UI", 10, "bold"), bg=bg_c, fg=fg_c).pack(pady=(5,0))
    tk.Label(badge, text=f"{int(pts)}p", font=("Segoe UI", 8, "bold"), bg=bg_c, fg=fg_c).pack()
    tk.Label(badge, text=f"{rg}e", font=("Segoe UI", 8, "italic"), bg=bg_c, fg=fg_c).pack(pady=(0,5))

tk.Button(root, text="FERMER LE BILAN", font=("Segoe UI", 9, "bold"), bg="#161B2D", fg="#4A90E2", 
          padx=30, pady=10, bd=0, command=root.destroy).pack(side="bottom", pady=20)

root.mainloop()