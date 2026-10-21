# Quatre dashboards d’analyses métier complémentaires

Ces dashboards ont été créés et publiés dans l’instance Superset locale, à partir des jeux physiques Apache Druid du schéma `druid`.

## Finance et paiements

- Dashboard Superset : http://localhost:25020/superset/dashboard/5/
- Source : `fact_payment` (une ligne par transaction de paiement).
- Indicateur affiché : montant total des paiements, calculé par `SUM(payment_value)` (environ 16 M en devise du jeu de données).

Cette analyse complète le panier moyen des commandes en détaillant les montants enregistrés côté paiements. Les dimensions disponibles incluent le type de paiement, le nombre d’échéances et les dates d’achat.

## Performance logistique

- Dashboard Superset : http://localhost:25020/superset/dashboard/6/
- Source : `fact_logistics` (grain commande).
- Indicateur affiché : nombre de commandes suivies, calculé par `SUM(orders_count)` (environ 99,4 k).

Les dimensions de dates et de statut permettent d’examiner les délais, les retards, la ponctualité et les distances de livraison. Les mesures Druid comprennent notamment `delivery_days`, `late_days`, `delivered_on_time` et `distance_km`.

## Segmentation et valeur client RFM

- Dashboard Superset : http://localhost:25020/superset/dashboard/7/
- Source : `mart_customer_rfm` (une ligne par client).
- Indicateur affiché : valeur moyenne des commandes par client, calculée par `AVG(average_order_value)` (160,29 en devise du jeu de données).

Les mesures RFM disponibles comprennent fréquence, montant et récence. Elles servent à comparer la valeur des clients et à préparer leur segmentation.

## Satisfaction et avis clients

- Dashboard Superset : http://localhost:25020/superset/dashboard/8/
- Source : `fact_review` (avis agrégés au niveau commande).
- Indicateur affiché : total des avis, calculé par `SUM(review_count)` (environ 100 k).

La table contient les notes moyennes et les comptes par score, ainsi que des mesures de temps de réponse. Elle permet d’étudier la distribution des notes et leur évolution dans le temps.

## Périmètre

Ces quatre dashboards se concentrent sur les indicateurs principaux exposés dans Superset. Les montants sont dans la devise source du jeu (BRL dans le contexte eBrasil). Les URLs Superset sont locales à l’environnement de formation et ne constituent pas des exports importables.