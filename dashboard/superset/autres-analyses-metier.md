# Quatre dashboards d’analyses métier complémentaires

Ces dashboards ont été créés et publiés dans l’instance Superset locale, à partir des jeux physiques Apache Druid du schéma `druid`.

## Finance et paiements

- Dashboard Superset : http://localhost:25020/superset/dashboard/5/
- Source : `fact_payment` (une ligne par transaction de paiement).
- Indicateurs affichés : montant total (`SUM(payment_value)`, environ 16 M) et montant moyen par paiement (`AVG(payment_value)`, 154,11 en devise du jeu).

Cette analyse complète le panier moyen des commandes en détaillant les montants enregistrés côté paiements. Les dimensions disponibles incluent le type de paiement, le nombre d’échéances et les dates d’achat.

## Performance logistique

- Dashboard Superset : http://localhost:25020/superset/dashboard/6/
- Source : `fact_logistics` (grain commande).
- Indicateurs affichés : nombre de commandes suivies (`SUM(orders_count)`, environ 99,4 k) et délai moyen de livraison (`AVG(delivery_days)`, 12,56 jours).

Les dimensions de dates et de statut permettent d’examiner les délais, les retards, la ponctualité et les distances de livraison. Les mesures Druid comprennent notamment `delivery_days`, `late_days`, `delivered_on_time` et `distance_km`.

## Segmentation et valeur client RFM

- Dashboard Superset : http://localhost:25020/superset/dashboard/7/
- Source : `mart_customer_rfm` (une ligne par client).
- Indicateurs affichés : valeur moyenne des commandes par client (`AVG(average_order_value)`, 160,29) et nombre de clients (`COUNT(*)`, environ 93,4 k).

Les mesures RFM disponibles comprennent fréquence, montant et récence. Elles servent à comparer la valeur des clients et à préparer leur segmentation.

## Satisfaction et avis clients

- Dashboard Superset : http://localhost:25020/superset/dashboard/8/
- Source : `fact_review` (avis agrégés au niveau commande).
- Indicateurs affichés : total des avis (`SUM(review_count)`, environ 100 k) et note moyenne (`AVG(CAST(average_score AS DOUBLE))`, 4,07/5).

La table contient les comptes par score et des mesures de temps de réponse. Elle permet d’étudier la distribution des notes et leur évolution dans le temps.

## Périmètre

Ces quatre dashboards exposent des indicateurs synthétiques et s’appuient sur les champs du jeu eBrasil, avec les montants dans la devise source (BRL). Les URLs Superset sont locales à l’environnement de formation et ne constituent pas des exports importables.