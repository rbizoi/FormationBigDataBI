# Dashboard Superset — Valeur des paniers et composition des commandes

## Accès

- Instance Superset locale : `http://localhost:25020`
- Dashboard : [Valeur des paniers et composition des commandes](http://localhost:25020/superset/dashboard/3/)
- Source : base **Apache Druid**, schéma `druid`, datasource `fact_order`
- Grain : une ligne par commande
- Analyse métier de référence : [Analyse_metier_commandes.pdf](https://github.com/rbizoi/FormationBigDataBI/blob/master/spark/notebooks/createEBrasil/exemplesBI/documentation/Analyse_metier_commandes.pdf)

## Indicateurs enregistrés sur le dataset `fact_order`

| Libellé Superset | Expression | Interprétation |
| --- | --- | --- |
| Montant payé | `SUM(payment_amount)` | Total payé pour les commandes de la période ou du groupe sélectionné |
| Panier moyen payé | `AVG(payment_amount)` | Montant moyen payé par commande |
| Montant produits | `SUM(product_amount)` | Total des produits commandés |
| Frais de livraison | `SUM(freight_amount)` | Total des frais de livraison |
| Articles moyens par commande | `AVG(item_count)` | Nombre moyen d’articles par commande |
| `COUNT(*)` | `COUNT(*)` | Nombre de commandes |

Les mesures monétaires sont exprimées dans la devise des données eBrasil (BRL).

## Graphiques du dashboard

1. **Évolution mensuelle des montants payés** — courbe mensuelle de `SUM(payment_amount)` selon `__time`.
2. **Panier moyen payé par commande** — KPI basé sur `AVG(payment_amount)`.
3. **Nombre total de commandes** — KPI basé sur `COUNT(*)`.
4. **Articles moyens par commande** — KPI basé sur `AVG(item_count)`.
5. **Montants produits et livraison par statut** — barres comparant `SUM(product_amount)` et `SUM(freight_amount)`, regroupées par `status`.

Les filtres et sélections du dashboard s’appliquent au dataset Druid `fact_order`. Les montants de produits et de livraison sont présentés côte à côte pour comparer leur contribution; leur somme n’est pas appelée « montant payé », car le dataset expose aussi `payment_amount` et `payment_gap`.

## Valeurs observées lors de la création

- Nombre de commandes : environ **99,4 k**
- Panier moyen payé : **160,99 BRL**
- Articles moyens par commande : **1,14**

Ces KPI sont recalculés par Superset à partir de Druid à l’ouverture du dashboard.