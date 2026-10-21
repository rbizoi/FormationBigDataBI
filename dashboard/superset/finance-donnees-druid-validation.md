# État des données Druid pour les dashboards Finance

Vérification dans Superset / SQL Lab le 21 octobre 2026.

## Résultat

- `fact_order` est exploitable pour les commandes : un regroupement par `purchase_date_key` et `SUM(payment_amount)` renvoie des lignes par date.
- `fact_order` ne possède pas la colonne `payment_type` : la requête de regroupement échoue car la colonne est absente.
- `fact_payment` expose les champs `payment_type` et `payment_value` dans son schéma Superset, mais les résultats SQL renvoient `aggregated` comme valeur de `payment_type` (y compris en lecture de lignes brutes). Un `GROUP BY payment_type` renvoie donc une ligne agrégée unique.
- Le KPI global `SUM(payment_value)` fonctionne et renvoie environ 16,0 M. Il ne permet pas de répartir ce montant par type, commande, échéances, calendrier ou client.

## Conséquence

Les 50 graphiques prévus dans [finance-cinq-analyses-50-graphiques.md](finance-cinq-analyses-50-graphiques.md) ne peuvent pas être construits fidèlement avec les datasources actuellement disponibles. Seul le dashboard brouillon « Finance - Mix des moyens de paiement » a été créé dans Superset; il contient le KPI global « Montant total payé ». Il n’est pas publié et ne constitue pas le dashboard demandé.

## Correction du pipeline publiée sur GitHub

Le pipeline Spark→Druid a été corrigé dans `spark/jobs/20_build_ebrasil_warehouse.py` et `docker/ebrasil-druid/ingest.py` :

- le manifeste conserve toutes les colonnes du fait avec leur type Druid, y compris `payment_value` (double) et `installments` (long);
- Druid reçoit ces colonnes comme dimensions typées et une liste `metricsSpec` vide, avec `rollup=false`, afin de garder les valeurs de chaque ligne de paiement;
- l’ingestion échoue si `fact_payment` ne contient pas plusieurs valeurs de `payment_type` ou si les deux champs numériques sont absents;
- `docker/ebrasil-druid/check.py` répète ces contrôles après ingestion.

Les noms de dimensions calendrier du plan ont aussi été alignés sur le modèle Spark : `purchase_date_year`, `purchase_date_quarter`, `purchase_date_month`, `purchase_date_weekday`, `purchase_time_hour` et `purchase_time_day_part`.

## État restant dans l’environnement Superset

Les requêtes du 21 octobre montrent encore l’ancien datasource Druid : `payment_type` vaut `aggregated` et les dimensions de paiement ne sont pas utilisables pour les répartitions. Il faut relancer la construction du modèle Spark puis l’ingestion Druid pour publier le nouveau schéma. Après cela, Superset devra actualiser les colonnes du dataset `fact_payment` avant la création et la validation des 50 graphiques.

La hiérarchie commande/panier doit être contrôlée séparément avec `fact_order` et `fact_order_item`, en agrégeant chaque source au même grain avant comparaison.
