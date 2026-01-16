import customtkinter as ctk
import sqlite3
import os
from tkinter import messagebox, ttk, Menu

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

ctk.set_appearance_mode("dark")

class AdminPanel(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PRONOS EXPERT - ADMIN CONTROL")
        self.geometry("1100x650")
        self.configure(fg_color="#0A121E")

        # --- TITRE ---
        self.lbl_titre = ctk.CTkLabel(self, text="PANNEAU DE CONTRÔLE ADMIN", 
                                      font=("Impact", 35), text_color="#D4AF37")
        self.lbl_titre.pack(pady=20)

        # --- CONTENEUR ONGLETS ---
        self.tabview = ctk.CTkTabview(self, fg_color="#1A2634", segmented_button_selected_color="#D4AF37")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tab_joueurs = self.tabview.add("Inscriptions & Pauses")
        self.tab_matchs = self.tabview.add("Matchs de la Semaine")

        self.setup_joueurs_tab()
        self.setup_matchs_tab()
        self.charger_donnees()

    def setup_joueurs_tab(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#1A2634", foreground="white", fieldbackground="#1A2634", borderwidth=0)
        style.map("Treeview", background=[('selected', '#D4AF37')], foreground=[('selected', 'black')])

        # Tableau des joueurs (Affiche uniquement Inactifs/En pause)
        self.tree_joueurs = ttk.Treeview(self.tab_joueurs, columns=("ID", "Pseudo", "Email", "Statut"), show="headings")
        self.tree_joueurs.heading("ID", text="ID")
        self.tree_joueurs.heading("Pseudo", text="Pseudo")
        self.tree_joueurs.heading("Email", text="Email")
        self.tree_joueurs.heading("Statut", text="Statut")
        self.tree_joueurs.pack(fill="both", expand=True, padx=10, pady=10)

        # Menu Contextuel
        self.context_menu = Menu(self, tearoff=0, bg="#1A2634", fg="white", activebackground="#D4AF37", activeforeground="black")
        self.context_menu.add_command(label="✅ ACTIVER (Retirer de la liste)", command=self.activer_joueur)
        self.context_menu.add_command(label="⏸ METTRE EN PAUSE", command=self.suspendre_joueur)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔄 RAFRAÎCHIR", command=self.charger_joueurs)

        self.tree_joueurs.bind("<Button-3>", self.afficher_menu_contextuel)
        self.tree_joueurs.bind("<Button-2>", self.afficher_menu_contextuel)

        ctk.CTkLabel(self.tab_joueurs, text="💡 Seuls les joueurs en attente ou en pause sont visibles ici.", 
                     font=("Arial", 11, "italic"), text_color="gray").pack(pady=5)

    def afficher_menu_contextuel(self, event):
        item = self.tree_joueurs.identify_row(event.y)
        if item:
            self.tree_joueurs.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def setup_matchs_tab(self):
        self.tree_matchs = ttk.Treeview(self.tab_matchs, columns=("Championnat", "Home", "Away", "Cote H", "Cote N", "Cote A"), show="headings")
        for col in self.tree_matchs["columns"]:
            self.tree_matchs.heading(col, text=col)
            self.tree_matchs.column(col, width=120)
        self.tree_matchs.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(self.tab_matchs, text="RAFRAÎCHIR LES MATCHS", command=self.charger_matchs, 
                      fg_color="#1A2634", border_width=1, border_color="#D4AF37").pack(pady=10)

    def charger_donnees(self):
        self.charger_joueurs()
        self.charger_matchs()

    def charger_joueurs(self):
        """Affiche UNIQUEMENT les joueurs qui ne sont pas 'Actif'"""
        for item in self.tree_joueurs.get_children(): self.tree_joueurs.delete(item)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # SYNCHRONISATION : On filtre pour exclure les 'Actif'
        cursor.execute("SELECT id, pseudo, email, statut FROM utilisateurs WHERE statut != 'Actif'")
        for row in cursor.fetchall():
            self.tree_joueurs.insert("", "end", values=row)
        conn.close()

    def charger_matchs(self):
        for item in self.tree_matchs.get_children(): self.tree_matchs.delete(item)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT championnat, equipe_home, equipe_away, cote_home, cote_draw, cote_away FROM matches")
        for row in cursor.fetchall():
            self.tree_matchs.insert("", "end", values=row)
        conn.close()

    def activer_joueur(self):
        self.modifier_statut("Actif")

    def suspendre_joueur(self):
        self.modifier_statut("En pause")

    def modifier_statut(self, nouveau_statut):
        selected = self.tree_joueurs.selection()
        if not selected: return
        
        player_id = self.tree_joueurs.item(selected)['values'][0]
        pseudo = self.tree_joueurs.item(selected)['values'][1]
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE utilisateurs SET statut=? WHERE id=?", (nouveau_statut, player_id))
        conn.commit()
        conn.close()
        
        self.charger_joueurs() # Rafraîchit et fait disparaître le joueur si devenu 'Actif'
        if nouveau_statut == "Actif":
            messagebox.showinfo("Admin", f"Le joueur {pseudo} est maintenant ACTIF et retiré de la liste de traitement.")
        else:
            messagebox.showinfo("Admin", f"Le statut de {pseudo} est : {nouveau_statut}")

if __name__ == "__main__":
    app = AdminPanel()
    app.mainloop()