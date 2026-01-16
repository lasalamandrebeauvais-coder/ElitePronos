import customtkinter as ctk
import sqlite3
import os
from tkinter import messagebox

# Chemin vers la base de donnees
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'pronos_expert.db')

ctk.set_appearance_mode("dark")

class InscriptionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.init_db_structure()

        self.title("Pronos Expert - Inscription")
        self.geometry("950x900") # Légèrement agrandi pour le 2ème bouton
        self.configure(fg_color="#0A121E") 

        # --- TITRES ---
        self.title_gold = ctk.CTkLabel(self, text="PRÊT À DÉTRÔNER TES POTES ?", 
                                        font=("Impact", 40), text_color="#D4AF37")
        self.title_gold.pack(pady=(30, 0))
        
        self.title_white = ctk.CTkLabel(self, text="ENTRE DANS L’ARÈNE", 
                                         font=("Impact", 40), text_color="white")
        self.title_white.pack(pady=(0, 30))

        # --- CONTENEUR PRINCIPAL ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=60)

        # --- COLONNE GAUCHE (Avatar) ---
        self.left_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, padx=40, sticky="n")

        self.avatar_box = ctk.CTkFrame(self.left_frame, width=220, height=220, 
                                       corner_radius=15, border_width=2, border_color="#D4AF37")
        self.avatar_box.pack(pady=10)
        self.avatar_box.pack_propagate(False)
        
        self.lbl_avatar = ctk.CTkLabel(self.left_frame, text="Avatar", font=("Arial", 14), text_color="white")
        self.lbl_avatar.pack()

        self.btn_upload = ctk.CTkButton(self.left_frame, text="Télécharger ma photo", 
                                         fg_color="#D4AF37", text_color="black", 
                                         font=("Arial", 12, "bold"), corner_radius=10)
        self.btn_upload.pack(pady=(20, 10), fill="x")

        self.btn_choice = ctk.CTkButton(self.left_frame, text="Choisir un avatar", 
                                         fg_color="white", text_color="black", 
                                         font=("Arial", 12, "bold"), corner_radius=10)
        self.btn_choice.pack(pady=5, fill="x")

        # --- COLONNE DROITE (Champs) ---
        self.right_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, padx=40, sticky="n")

        self.prenom = self.add_entry("Prénom")
        self.pseudo = self.add_entry("Pseudo")
        self.email = self.add_entry("Email")
        self.tel = self.add_entry("Téléphone")
        self.pin = self.add_entry("Code PIN (4 chiffres)", show="*")
        self.secours = self.add_entry("Secours (Optionnel)")

        # --- BOUTON DE VALIDATION CENTRAL ---
        self.btn_valider_mid = ctk.CTkButton(self, text="VALIDER MON INSCRIPTION", 
                                         height=55, width=350, corner_radius=28,
                                         fg_color="#D4AF37", text_color="black", 
                                         font=("Arial", 18, "bold"),
                                         command=self.sauvegarder)
        self.btn_valider_mid.pack(pady=(30, 5))

        self.link_reglement = ctk.CTkLabel(self, text="Voir le Règlement", 
                                            font=("Arial", 13, "underline"), 
                                            text_color="white", cursor="hand2")
        self.link_reglement.pack(pady=5)

        # --- BOUTON DE VALIDATION BAS DE PAGE ---
        self.btn_valider_bottom = ctk.CTkButton(self, text="CONFIRMER ET ENTRER DANS L'ARÈNE", 
                                         height=50, width=400, corner_radius=15,
                                         fg_color="transparent", border_width=2, border_color="#D4AF37",
                                         text_color="#D4AF37", 
                                         font=("Arial", 14, "bold"),
                                         command=self.sauvegarder)
        self.btn_valider_bottom.pack(pady=(10, 40))

    def init_db_structure(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prenom TEXT,
                pseudo TEXT UNIQUE,
                email TEXT,
                telephone TEXT,
                pin TEXT,
                joueur_secours TEXT,
                statut TEXT DEFAULT 'en_attente'
            )
        ''')
        conn.commit()
        conn.close()

    def add_entry(self, placeholder, show=""):
        entry = ctk.CTkEntry(self.right_frame, placeholder_text=placeholder, 
                             show=show, width=320, height=45, 
                             corner_radius=22, fg_color="white", text_color="black")
        entry.pack(pady=10)
        return entry

    def sauvegarder(self):
        if not self.pseudo.get() or not self.pin.get():
            messagebox.showwarning("Pronos Expert", "Veuillez remplir au moins le Pseudo et le PIN.")
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO utilisateurs (prenom, pseudo, email, telephone, pin, joueur_secours)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.prenom.get(), self.pseudo.get(), self.email.get(), 
                  self.tel.get(), self.pin.get(), self.secours.get()))
            conn.commit()
            conn.close()
            messagebox.showinfo("Pronos Expert", f"Félicitations {self.pseudo.get()} !\nInscription envoyée.")
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", "Ce pseudo est déjà utilisé.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

if __name__ == "__main__":
    app = InscriptionApp()
    app.mainloop()