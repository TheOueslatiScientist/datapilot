# Glossaire des indicateurs (KPI) — ShopNova

Ce document est la référence officielle de l'équipe Data de ShopNova. Toute analyse
présentée en comité de direction doit utiliser ces définitions. En cas de doute,
c'est ce glossaire qui fait foi, et non les intitulés des colonnes de la base.

## Chiffre d'affaires (CA)

Le chiffre d'affaires net correspond à la somme des montants facturés sur les lignes
de commande, remises déduites, pour les seules commandes au statut « livrée ».
Formule : somme de quantite × prix_unitaire × (1 − remise_pct / 100).
Les frais de livraison ne sont jamais inclus dans le chiffre d'affaires : ils sont
suivis séparément par l'équipe logistique. Les commandes « annulée », « en cours » et
« retournée » sont exclues du CA. Une commande retournée a été remboursée : la compter
gonflerait artificiellement le chiffre d'affaires.

## Panier moyen

Le panier moyen est le chiffre d'affaires net divisé par le nombre de commandes au
statut « livrée » sur la même période. Il s'exprime en euros TTC, arrondi à deux
décimales. Le panier moyen ne se calcule jamais sur les commandes annulées.

## Taux de retour

Le taux de retour mesure la part des commandes expédiées qui reviennent.
Formule : nombre de commandes « retournée » / (nombre de commandes « livrée » +
nombre de commandes « retournée »). Il s'exprime en pourcentage avec une décimale.
Un taux de retour supérieur à 8 % sur une catégorie déclenche une alerte qualité.

## Taux d'annulation

Le taux d'annulation est le nombre de commandes « annulée » divisé par le nombre total
de commandes passées sur la période, tous statuts confondus.

## Marge brute

La marge brute est le chiffre d'affaires net moins le coût d'achat des produits vendus.
Coût d'achat : somme de quantite × cout_unitaire (table produits) pour les lignes des
commandes livrées. Le taux de marge brute est la marge brute divisée par le CA net.

## Client actif

Un client est dit actif s'il a passé au moins une commande livrée au cours des 365 jours
précédant la date de référence. Pour le jeu de données d'étude, la date de référence est
le 31 décembre 2025. Un client inscrit qui n'a jamais commandé n'est pas un client actif.

## Nombre de commandes

Sauf mention contraire, « nombre de commandes » désigne les commandes au statut
« livrée ». Pour parler de toutes les commandes, on dit « commandes passées ».
