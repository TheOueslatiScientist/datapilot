# Dictionnaire de données — base ecommerce.db

La base SQLite ecommerce.db contient l'historique des ventes ShopNova du
1er janvier 2024 au 31 décembre 2025. Toutes les dates sont stockées en texte au
format ISO AAAA-MM-JJ : utiliser les fonctions strftime ou date de SQLite pour les
filtrer, par exemple strftime('%Y', date_commande) = '2025'.

## Table clients

Une ligne par client inscrit. Colonnes : client_id (identifiant), nom, email, ville,
region (région administrative française), date_inscription, segment (Standard,
Premium ou VIP, voir les règles de segmentation).

## Table produits

Catalogue des 30 produits vendus. Colonnes : produit_id, nom, categorie (High-tech,
Informatique, Maison, Sport, Livres, Beauté, Jeux), prix_unitaire (prix catalogue TTC
en euros), cout_unitaire (coût d'achat en euros, utilisé pour la marge brute).

## Table commandes

Une ligne par commande passée. Colonnes : commande_id, client_id, date_commande,
statut, canal (web, mobile, marketplace), frais_livraison (en euros).
Valeurs de statut : « livrée » (commande expédiée et reçue), « annulée » (annulée
avant expédition), « en cours » (pas encore livrée), « retournée » (tous les articles
ont été renvoyés et remboursés). Attention aux accents dans les valeurs de statut.

## Table lignes_commande

Une ligne par produit dans une commande. Colonnes : ligne_id, commande_id,
produit_id, quantite, prix_unitaire (prix réellement facturé, qui peut différer du
prix catalogue), remise_pct (remise en pourcentage, de 0 à 30). Le montant d'une
ligne vaut quantite × prix_unitaire × (1 − remise_pct / 100). Il n'existe pas de
colonne « montant total » dans la table commandes : il faut toujours le calculer à
partir des lignes.

## Table retours

Une ligne par commande retournée. Colonnes : retour_id, commande_id, date_retour,
motif, montant_rembourse (en euros).

## Jointures usuelles

commandes.client_id = clients.client_id ;
lignes_commande.commande_id = commandes.commande_id ;
lignes_commande.produit_id = produits.produit_id ;
retours.commande_id = commandes.commande_id.
