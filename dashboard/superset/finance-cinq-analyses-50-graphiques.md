# Analyse métier Finance — 5 dashboards Superset

Source : [Analyse_metier_finance.pdf](https://github.com/rbizoi/FormationBigDataBI/blob/master/spark/notebooks/createEBrasil/exemplesBI/documentation/Analyse_metier_finance.pdf)

Ce plan reprend les cinq axes du document et les dix visuels attendus dans chaque axe. Source principale : `fact_payment` dans Apache Druid. Les champs calendrier et attributs client sont les dimensions dénormalisées présentes sur ce fait.

## Règles de lecture et de calcul

- Grain de `fact_payment` : une ligne par commande et moyen de paiement. Ne pas additionner les lignes comme si elles représentaient des commandes distinctes.
- Montant total : `SUM(payment_value)`.
- Transactions préparées : `SUM(transaction_count)`.
- Commandes distinctes : `COUNT(DISTINCT order_id)`.
- Échéances moyennes : `AVG(installments)`.
- Ticket moyen : `AVG(payment_value)` au niveau du grain disponible; pour un ticket de commande, agréger d’abord les paiements par `order_id`, puis calculer la moyenne.
- Montants de paiement observés : ce sont les montants associés aux moyens de paiement préparés; ils ne représentent pas des frais, remboursements ou encaissements nets.
- Les dimensions `purchase_date_calendar_date`, `purchase_date_year`, `purchase_date_quarter`, `purchase_date_month`, `purchase_date_day`, `purchase_date_weekday`, `purchase_time_hour`, `purchase_time_day_part`, `customer_state`, `customer_city`, `customer_zip_code`, `customer_unique_id`, `payment_type`, `installments`, `order_id` sont celles indiquées ou utilisées dans les exemples du document.
- Les heatmaps utilisent la dimension indiquée dans « détail ». Pour faciliter la lecture, limiter les villes, clients et codes postaux aux premières valeurs par montant/volume.
- Les hiérarchies sont à réaliser avec des niveaux de granularité et des filtres/cross-filters du dashboard. Les chemins qui traversent des grains différents doivent être interprétés comme navigation et comparaison, jamais comme jointure additive implicite.

## Dashboard 1 — Mix des moyens de paiement

Hiérarchies : **type > date d’achat**; **type > état/ville client**; calendrier **année > trimestre > mois > jour**.

| # | Visuel | Type | Dimension / détail | Mesure |
|---|---|---|---|---|
| 1 | Type paiement | Barres | `payment_type` | Montant payé |
| 2 | Mois achat | Courbe | `purchase_date_month` | Commandes distinctes |
| 3 | Année achat | Courbe | `purchase_date_year` | Transactions préparées |
| 4 | Trimestre achat | Barres | `purchase_date_quarter` | Montant payé |
| 5 | Jour semaine | Barres | `purchase_date_weekday` | Commandes distinctes |
| 6 | Partie du jour | Barres | `purchase_time_day_part` | Transactions préparées |
| 7 | État client | Barres | `customer_state` | Montant payé |
| 8 | Type × mois | Heatmap | détail : mois (`SUBSTRING(purchase_date_calendar_date,1,7)`) | Commandes distinctes |
| 9 | Type × état | Heatmap | détail : `customer_state` | Transactions préparées |
| 10 | Ville client | Barres | `customer_city` | Montant payé |

## Dashboard 2 — Échéanciers et recours au paiement fractionné

Hiérarchies : **nombre d’échéances > type > montant**; **type > client et calendrier**. Toujours comparer volumes et montants.

| # | Visuel | Type | Dimension / détail | Mesure |
|---|---|---|---|---|
| 1 | Échéances | Barres | `installments` | Montant payé |
| 2 | Type paiement | Barres | `payment_type` | Échéances moyennes |
| 3 | Montant par tranche 50 | Barres | `FLOOR(payment_value/50)*50` | Commandes distinctes |
| 4 | Mois achat | Courbe | `purchase_date_month` | Ticket moyen |
| 5 | État client | Barres | `customer_state` | Montant payé |
| 6 | Jour semaine | Barres | `purchase_date_weekday` | Échéances moyennes |
| 7 | Heure | Barres | `purchase_time_hour` | Commandes distinctes |
| 8 | Échéances × type | Heatmap | détail : `payment_type` | Ticket moyen |
| 9 | Type × mois | Heatmap | détail : mois (`SUBSTRING(purchase_date_calendar_date,1,7)`) | Commandes distinctes |
| 10 | Échéances × tranche montant | Heatmap | détail : tranche `FLOOR(payment_value/50)*50` | Montant payé |

## Dashboard 3 — Valeur des paiements et distribution des tickets

Hiérarchies : **montant > commande > type**; **date d’achat > marché client**; drill-through via `order_id`.

| # | Visuel | Type | Dimension / détail | Mesure |
|---|---|---|---|---|
| 1 | Tranche montant 25 | Barres | `FLOOR(payment_value/25)*25` | Ticket moyen |
| 2 | Type paiement | Barres | `payment_type` | Montant total |
| 3 | Échéances | Barres | `installments` | Commandes distinctes |
| 4 | Mois achat | Courbe | `purchase_date_month` | Ticket moyen |
| 5 | Année achat | Courbe | `purchase_date_year` | Montant total |
| 6 | État client | Barres | `customer_state` | Commandes distinctes |
| 7 | Ville client | Barres | `customer_city` | Ticket moyen |
| 8 | Type × tranche montant | Heatmap | détail : tranche `FLOOR(payment_value/25)*25` | Montant |
| 9 | Échéances × type | Heatmap | détail : `payment_type` | Commandes distinctes |
| 10 | Commande | Barres | `order_id` | Ticket moyen |

## Dashboard 4 — Géographie des paiements et comportement client

Hiérarchies : **état > ville > code postal**; **client > type de paiement > commande**; garder la période en contexte.

| # | Visuel | Type | Dimension / détail | Mesure |
|---|---|---|---|---|
| 1 | État client | Barres | `customer_state` | Montant total |
| 2 | Ville client | Barres | `customer_city` | Commandes distinctes |
| 3 | Code postal | Barres | `customer_zip_code` | Ticket moyen |
| 4 | Client unique | Barres | `customer_unique_id` | Montant total |
| 5 | Type paiement | Barres | `payment_type` | Commandes distinctes |
| 6 | Mois achat | Courbe | `purchase_date_month` | Ticket moyen |
| 7 | État × type | Heatmap | détail : `payment_type` | Montant total |
| 8 | Ville × type | Heatmap | détail : `payment_type` | Commandes distinctes |
| 9 | Client × type | Heatmap | détail : `payment_type` | Ticket moyen |
| 10 | Heure achat | Barres | `purchase_time_hour` | Montant total |

## Dashboard 5 — Couverture des commandes et cohérence des agrégats

Hiérarchies : **type > commande**; **période > client > état**. Pour contrôler les paniers, ouvrir `fact_order` et `fact_order_item` séparément et comparer au bon grain.

| # | Visuel | Type | Dimension / détail | Mesure |
|---|---|---|---|---|
| 1 | Type paiement | Barres | `payment_type` | Commandes distinctes |
| 2 | Mois achat | Courbe | `purchase_date_month` | Montant total |
| 3 | État client | Barres | `customer_state` | Transactions préparées |
| 4 | Client unique | Barres | `customer_unique_id` | Commandes distinctes |
| 5 | Échéances | Barres | `installments` | Montant total |
| 6 | Tranche montant | Barres | tranches de montant | Transactions préparées |
| 7 | Jour semaine | Barres | `purchase_date_weekday` | Commandes distinctes |
| 8 | Type × mois | Heatmap | détail : mois (`SUBSTRING(purchase_date_calendar_date,1,7)`) | Montant total |
| 9 | Type × échéances | Heatmap | détail : `installments` | Transactions préparées |
| 10 | Commande | Barres | `order_id` | Commandes distinctes |

## Hiérarchies et limites d’implémentation

Superset peut filtrer/croiser ces vues par les dimensions communes. Pour les drill-downs calendaires, utiliser les champs année, trimestre, mois et jour comme niveaux ordonnés et garder un filtre de période synchronisé. Pour les chemins géographiques, configurer état, ville puis code postal. Pour les parcours client/commande, utiliser `customer_unique_id` et `order_id` comme dimensions de navigation, avec filtres temporels.

Le document évoque des parcours multi-niveaux mais les tables de faits ont des granularités différentes. Toute comparaison panier/paiement doit agréger chacune des sources à la même clé (commande ou période) avant rapprochement. Si les champs de navigation ou les métriques dérivées n’existent pas dans le dataset Superset, les ajouter au dataset Druid (ou via SQL virtuel) avant la visualisation.
