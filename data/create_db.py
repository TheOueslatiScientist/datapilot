"""
create_db.py — Génère la base SQLite du cas fil rouge « ShopNova » (e-commerce fictif).

Usage :
    python data/create_db.py            # crée data/ecommerce.db
    python data/create_db.py --force    # recrée la base si elle existe déjà

Le générateur est déterministe (graine fixe) : tous les étudiants obtiennent
exactement les mêmes données, donc les mêmes réponses attendues.
"""
from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ecommerce.db"
SEED = 42

SCHEMA = """
CREATE TABLE clients (
    client_id         INTEGER PRIMARY KEY,
    nom               TEXT    NOT NULL,
    email             TEXT    NOT NULL UNIQUE,
    ville             TEXT    NOT NULL,
    region            TEXT    NOT NULL,
    date_inscription  TEXT    NOT NULL,          -- format ISO AAAA-MM-JJ
    segment           TEXT    NOT NULL CHECK (segment IN ('Standard', 'Premium', 'VIP'))
);

CREATE TABLE produits (
    produit_id     INTEGER PRIMARY KEY,
    nom            TEXT NOT NULL,
    categorie      TEXT NOT NULL,
    prix_unitaire  REAL NOT NULL,                -- prix de vente catalogue TTC (EUR)
    cout_unitaire  REAL NOT NULL                 -- coût d'achat (EUR)
);

CREATE TABLE commandes (
    commande_id     INTEGER PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(client_id),
    date_commande   TEXT    NOT NULL,            -- format ISO AAAA-MM-JJ
    statut          TEXT    NOT NULL CHECK (statut IN ('livrée', 'annulée', 'en cours', 'retournée')),
    canal           TEXT    NOT NULL CHECK (canal IN ('web', 'mobile', 'marketplace')),
    frais_livraison REAL    NOT NULL
);

CREATE TABLE lignes_commande (
    ligne_id       INTEGER PRIMARY KEY,
    commande_id    INTEGER NOT NULL REFERENCES commandes(commande_id),
    produit_id     INTEGER NOT NULL REFERENCES produits(produit_id),
    quantite       INTEGER NOT NULL CHECK (quantite > 0),
    prix_unitaire  REAL    NOT NULL,             -- prix réellement facturé (EUR TTC)
    remise_pct     REAL    NOT NULL DEFAULT 0    -- remise en % (0 à 30)
);

CREATE TABLE retours (
    retour_id          INTEGER PRIMARY KEY,
    commande_id        INTEGER NOT NULL REFERENCES commandes(commande_id),
    date_retour        TEXT    NOT NULL,
    motif              TEXT    NOT NULL,
    montant_rembourse  REAL    NOT NULL
);

CREATE INDEX idx_commandes_client ON commandes(client_id);
CREATE INDEX idx_commandes_date   ON commandes(date_commande);
CREATE INDEX idx_lignes_commande  ON lignes_commande(commande_id);
"""

VILLES = {
    "Île-de-France": ["Paris", "Versailles", "Créteil", "Nanterre"],
    "Auvergne-Rhône-Alpes": ["Lyon", "Grenoble", "Clermont-Ferrand"],
    "Provence-Alpes-Côte d'Azur": ["Marseille", "Nice", "Toulon"],
    "Occitanie": ["Toulouse", "Montpellier"],
    "Nouvelle-Aquitaine": ["Bordeaux", "Limoges"],
    "Hauts-de-France": ["Lille", "Amiens"],
    "Grand Est": ["Strasbourg", "Reims"],
    "Bretagne": ["Rennes", "Brest"],
}
POIDS_REGIONS = [30, 14, 12, 10, 10, 9, 8, 7]

PRODUITS = [
    # (nom, catégorie, prix TTC, coût)
    ("Casque audio sans fil", "High-tech", 89.90, 41.00),
    ("Écouteurs Bluetooth", "High-tech", 49.90, 19.50),
    ("Enceinte portable", "High-tech", 69.00, 30.00),
    ("Montre connectée", "High-tech", 149.00, 72.00),
    ("Chargeur rapide USB-C", "High-tech", 24.90, 7.80),
    ("Clavier mécanique", "Informatique", 99.00, 46.00),
    ("Souris ergonomique", "Informatique", 39.90, 14.00),
    ("Écran 27 pouces", "Informatique", 249.00, 168.00),
    ("Disque SSD 1 To", "Informatique", 79.90, 45.00),
    ("Webcam HD", "Informatique", 59.00, 24.00),
    ("Cafetière à piston", "Maison", 29.90, 9.50),
    ("Lampe de bureau LED", "Maison", 34.90, 12.00),
    ("Plaid en laine", "Maison", 44.90, 17.00),
    ("Set de 4 verres", "Maison", 19.90, 6.20),
    ("Bougie parfumée", "Maison", 14.90, 3.90),
    ("Tapis de yoga", "Sport", 29.90, 10.50),
    ("Gourde isotherme", "Sport", 22.90, 7.00),
    ("Haltères 2x5 kg", "Sport", 54.90, 26.00),
    ("Corde à sauter", "Sport", 12.90, 3.20),
    ("Sac de sport", "Sport", 39.90, 15.00),
    ("Roman policier", "Livres", 9.90, 5.10),
    ("Guide Python pour la data", "Livres", 34.90, 19.00),
    ("Bande dessinée", "Livres", 15.90, 8.30),
    ("Livre de cuisine", "Livres", 24.90, 12.40),
    ("Crème hydratante", "Beauté", 19.90, 6.00),
    ("Brosse à dents électrique", "Beauté", 59.90, 22.00),
    ("Coffret parfum", "Beauté", 64.90, 25.00),
    ("Sèche-cheveux", "Beauté", 44.90, 19.00),
    ("Jeu de société", "Jeux", 34.90, 14.50),
    ("Puzzle 1000 pièces", "Jeux", 17.90, 6.10),
]

PRENOMS = ["Camille", "Lucas", "Léa", "Hugo", "Chloé", "Nathan", "Manon", "Louis",
           "Inès", "Gabriel", "Sarah", "Adam", "Emma", "Yanis", "Jade", "Rayan",
           "Lina", "Arthur", "Zoé", "Noah", "Amira", "Mehdi", "Clara", "Théo"]
NOMS = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
        "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
        "Garcia", "Benali", "Nguyen", "Haddad", "Fontaine", "Rousseau"]
MOTIFS_RETOUR = ["Article défectueux", "Ne correspond pas à la description",
                 "Taille ou format inadapté", "Livraison trop tardive", "Changement d'avis"]

DEBUT = date(2024, 1, 1)
FIN = date(2025, 12, 31)


def date_aleatoire(rng: random.Random, debut: date, fin: date) -> date:
    return debut + timedelta(days=rng.randint(0, (fin - debut).days))


def generer(conn: sqlite3.Connection) -> None:
    rng = random.Random(SEED)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    # --- Produits ---------------------------------------------------------
    cur.executemany(
        "INSERT INTO produits VALUES (?, ?, ?, ?, ?)",
        [(i + 1, *p) for i, p in enumerate(PRODUITS)],
    )

    # --- Clients ----------------------------------------------------------
    regions = list(VILLES)
    clients = []
    for cid in range(1, 501):
        prenom, nom = rng.choice(PRENOMS), rng.choice(NOMS)
        region = rng.choices(regions, weights=POIDS_REGIONS)[0]
        ville = rng.choice(VILLES[region])
        inscription = date_aleatoire(rng, date(2022, 1, 1), date(2025, 9, 30))
        segment = rng.choices(["Standard", "Premium", "VIP"], weights=[70, 22, 8])[0]
        email = f"{prenom.lower()}.{nom.lower()}{cid}@exemple.fr".replace("é", "e").replace("ï", "i")
        clients.append((cid, f"{prenom} {nom}", email, ville, region, inscription.isoformat(), segment))
    cur.executemany("INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?)", clients)

    # --- Commandes, lignes, retours ----------------------------------------
    commande_id, ligne_id, retour_id = 0, 0, 0
    freq = {"Standard": 4, "Premium": 9, "VIP": 16}   # nb moyen de commandes sur 2 ans
    for cid, *_rest in clients:
        segment = _rest[-1]
        inscription = date.fromisoformat(_rest[4])
        n_cmd = max(0, int(rng.gauss(freq[segment], freq[segment] / 3)))
        for _ in range(n_cmd):
            d = date_aleatoire(rng, max(DEBUT, inscription), FIN)
            # saisonnalité : un peu plus de commandes en novembre/décembre
            if d.month not in (11, 12) and rng.random() < 0.12:
                d = d.replace(month=rng.choice([11, 12]), day=min(d.day, 28))
                if d < inscription:
                    continue
            commande_id += 1
            canal = rng.choices(["web", "mobile", "marketplace"], weights=[50, 35, 15])[0]
            r = rng.random()
            statut = "livrée" if r < 0.86 else "annulée" if r < 0.92 else "retournée"
            if d >= date(2025, 12, 22) and statut == "livrée":
                statut = "en cours"

            montant = 0.0
            lignes = []
            for _ in range(rng.choices([1, 2, 3, 4], weights=[45, 30, 17, 8])[0]):
                ligne_id += 1
                pid = rng.randint(1, len(PRODUITS))
                prix = PRODUITS[pid - 1][2]
                qte = rng.choices([1, 2, 3], weights=[78, 17, 5])[0]
                remise = rng.choices([0, 5, 10, 20, 30], weights=[65, 12, 12, 8, 3])[0]
                montant += qte * prix * (1 - remise / 100)
                lignes.append((ligne_id, commande_id, pid, qte, prix, remise))
            frais = 0.0 if montant >= 50 else 4.90
            cur.execute("INSERT INTO commandes VALUES (?, ?, ?, ?, ?, ?)",
                        (commande_id, cid, d.isoformat(), statut, canal, frais))
            cur.executemany("INSERT INTO lignes_commande VALUES (?, ?, ?, ?, ?, ?)", lignes)

            if statut == "retournée":
                retour_id += 1
                d_retour = min(d + timedelta(days=rng.randint(5, 28)), FIN)
                motif = rng.choices(MOTIFS_RETOUR, weights=[30, 25, 20, 10, 15])[0]
                cur.execute("INSERT INTO retours VALUES (?, ?, ?, ?, ?)",
                            (retour_id, commande_id, d_retour.isoformat(), motif, round(montant, 2)))
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Crée la base SQLite ShopNova")
    parser.add_argument("--force", action="store_true", help="écrase la base existante")
    args = parser.parse_args()

    if DB_PATH.exists():
        if not args.force:
            print(f"La base existe déjà : {DB_PATH} (utilisez --force pour la recréer)")
            return
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        generer(conn)
        for table in ["clients", "produits", "commandes", "lignes_commande", "retours"]:
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table:<16} {n:>6} lignes")
    print(f"Base créée : {DB_PATH}")


if __name__ == "__main__":
    main()
