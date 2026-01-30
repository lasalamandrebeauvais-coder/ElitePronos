-- ============================================
-- ELITE PRONOS - Schema Supabase
-- ============================================
-- Executer ce script dans Supabase SQL Editor
-- Dashboard > SQL Editor > New Query > Coller > Run

-- 1. Table UTILISATEURS
CREATE TABLE IF NOT EXISTS utilisateurs (
    id SERIAL PRIMARY KEY,
    prenom TEXT,
    pseudo TEXT UNIQUE NOT NULL,
    email TEXT,
    telephone TEXT,
    pin TEXT,
    joueur_secours TEXT,
    tokens_football INTEGER DEFAULT 50,
    statut TEXT DEFAULT 'en_attente',
    is_admin BOOLEAN DEFAULT FALSE,
    parrain TEXT,
    date_anniversaire DATE,
    equipe_preferee TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ajout colonnes profil (si table existe deja)
ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS date_anniversaire DATE;
ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS equipe_preferee TEXT;

-- 2. Table MATCHES
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    semaine_id INTEGER NOT NULL,
    championnat TEXT,
    equipe_home TEXT NOT NULL,
    equipe_away TEXT NOT NULL,
    cote_home REAL,
    cote_draw REAL,
    cote_away REAL,
    date_match TIMESTAMP WITH TIME ZONE,
    score_final_home INTEGER,
    score_final_away INTEGER,
    score_mi_temps_home INTEGER,
    score_mi_temps_away INTEGER,
    status TEXT DEFAULT 'SCHEDULED',
    saison_id INTEGER DEFAULT 2025,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Table PREDICTIONS
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES utilisateurs(id),
    match_id INTEGER REFERENCES matches(id),
    score_prono_home INTEGER NOT NULL,
    score_prono_away INTEGER NOT NULL,
    mise_points INTEGER NOT NULL,
    points_gagnes REAL DEFAULT 0,
    is_score_exact BOOLEAN DEFAULT FALSE,
    saison_id INTEGER DEFAULT 2025,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Table JOKERS_HISTORIQUE
CREATE TABLE IF NOT EXISTS jokers_historique (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER REFERENCES utilisateurs(id),
    semaine_id INTEGER NOT NULL,
    type_joker TEXT NOT NULL,
    saison_id INTEGER DEFAULT 2025,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Table STOCK_JOKERS
CREATE TABLE IF NOT EXISTS stock_jokers (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER REFERENCES utilisateurs(id),
    joker_double INTEGER DEFAULT 1,
    joker_vol INTEGER DEFAULT 1,
    saison_id INTEGER DEFAULT 2025
);

-- 6. Table SAISONS
CREATE TABLE IF NOT EXISTS saisons (
    id SERIAL PRIMARY KEY,
    annee_debut INTEGER NOT NULL,
    annee_fin INTEGER NOT NULL,
    journee_courante INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE
);

-- 7. Table CONFIG_SEMAINE
CREATE TABLE IF NOT EXISTS config_semaine (
    id SERIAL PRIMARY KEY,
    semaine_id INTEGER NOT NULL,
    saison_id INTEGER DEFAULT 2025,
    date_limite TIMESTAMP WITH TIME ZONE,
    is_open BOOLEAN DEFAULT TRUE
);

-- ============================================
-- INDEX pour performances
-- ============================================
CREATE INDEX IF NOT EXISTS idx_matches_semaine ON matches(semaine_id, saison_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_utilisateurs_pseudo ON utilisateurs(pseudo);

-- ============================================
-- DONNEES INITIALES
-- ============================================

-- Saison 2025-2026
INSERT INTO saisons (annee_debut, annee_fin, journee_courante, is_active)
VALUES (2025, 2026, 19, TRUE)
ON CONFLICT DO NOTHING;

-- Utilisateur admin baggio
INSERT INTO utilisateurs (prenom, pseudo, email, statut, is_admin, tokens_football)
VALUES ('Baggio', 'baggio', 'baggio@elitepronos.com', 'Actif', TRUE, 100)
ON CONFLICT (pseudo) DO NOTHING;

-- Matchs J19
INSERT INTO matches (semaine_id, championnat, equipe_home, equipe_away, cote_home, cote_draw, cote_away, date_match, score_final_home, score_final_away, status, saison_id)
VALUES
    (19, 'Ligue 1', 'AJ Auxerre', 'Paris Saint-Germain FC', 4.40, 4.30, 1.75, '2026-01-24 19:00:00+01', 0, 1, 'FINISHED', 2025),
    (19, 'Ligue 1', 'Le Havre AC', 'AS Monaco FC', 4.40, 4.00, 1.80, '2026-01-24 21:00:00+01', NULL, NULL, 'SCHEDULED', 2025),
    (19, 'Ligue 1', 'Olympique de Marseille', 'Racing Club de Lens', 1.80, 3.80, 4.40, '2026-01-25 21:00:00+01', NULL, NULL, 'SCHEDULED', 2025),
    (19, 'Ligue 1', 'FC Metz', 'Olympique Lyonnais', 3.40, 3.50, 2.10, '2026-01-26 17:00:00+01', NULL, NULL, 'SCHEDULED', 2025)
ON CONFLICT DO NOTHING;

-- ============================================
-- POLITIQUES DE SECURITE (RLS)
-- ============================================
-- Activer RLS sur les tables sensibles
ALTER TABLE utilisateurs ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- Politique: Lecture publique pour tous
CREATE POLICY "Lecture publique utilisateurs" ON utilisateurs FOR SELECT USING (true);
CREATE POLICY "Lecture publique predictions" ON predictions FOR SELECT USING (true);
CREATE POLICY "Lecture publique matches" ON matches FOR SELECT USING (true);

-- Politique: Ecriture avec service_role uniquement
CREATE POLICY "Ecriture service utilisateurs" ON utilisateurs FOR ALL USING (true);
CREATE POLICY "Ecriture service predictions" ON predictions FOR ALL USING (true);
CREATE POLICY "Ecriture service matches" ON matches FOR ALL USING (true);

-- ============================================
-- FIN DU SCRIPT
-- ============================================
SELECT 'Schema Elite Pronos cree avec succes!' AS message;
