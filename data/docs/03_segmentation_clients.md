# Règles de segmentation clients — ShopNova

## Principe

Chaque client appartient à un et un seul segment : Standard, Premium ou VIP.
Le segment est stocké dans la colonne segment de la table clients. Il est recalculé
une fois par an, le 1er janvier, par l'équipe CRM, à partir de l'historique des
24 derniers mois. Entre deux recalculs, le segment stocké peut donc ne plus refléter
exactement le comportement récent du client.

## Segment Standard

C'est le segment par défaut attribué à tout nouveau client à l'inscription.
Un client reste Standard tant qu'il ne remplit pas les critères Premium ou VIP.

## Segment Premium

Un client devient Premium s'il remplit au moins une des deux conditions suivantes sur
les 24 derniers mois : au moins 6 commandes livrées, ou un chiffre d'affaires net
cumulé d'au moins 500 euros. Avantages : livraison offerte dès 30 euros d'achat
(au lieu de 50 euros) et retours toujours gratuits.

## Segment VIP

Un client devient VIP si son chiffre d'affaires net cumulé sur les 24 derniers mois
atteint au moins 1 500 euros. Avantages : livraison toujours offerte, délai de retour
étendu à 60 jours, accès anticipé aux soldes et conseiller dédié.

## Utilisation en analyse

Pour une analyse par segment, utiliser la colonne segment telle qu'elle est stockée,
sauf si la demande précise explicitement « segment recalculé ». Dans ce dernier cas,
il faut recalculer le segment à partir des commandes en appliquant les règles
ci-dessus. Les comparaisons de panier moyen entre segments sont un indicateur suivi
chaque trimestre par la direction marketing.
