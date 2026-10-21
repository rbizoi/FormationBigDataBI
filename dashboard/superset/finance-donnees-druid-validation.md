# État des données Druid pour les dashboards Finance

Vérification dans Superset / SQL Lab le 21 octobre 2026.

## Résultat

- `fact_order` est exploitable pour les commandes : un regroupement par `purchase_date_key` et `SUM(payment_amount)` renvoie des lignes par date.
- `fact_order` ne possède pas la colonne `payment_type` : la requête de regroupement échoue car la colonne est absente.
- `fact_payment` expose les champs `payment_type` et `payment_value` dans son schéma Superset, mais les résultats SQL renvoient `aggregated` comme valeur de `payment_type` (y compris en lecture de lignes brutes). Un `GROUP BY payment_type` renvoie donc une ligne agrégée unique.
- Le KPI global `SUM(payment_value)` fonctionne et renvoie environ 16,0 M. Il ne permet pas de répartir ce montant par type, commande, échéances, calendrier ou client.

## Conséquence

Les 50 graphiques prévus dans [finance-cinq-analyses-50-graphiques.md](finance-cinq-analyses-50-graphiques.md) ne peuvent pas être construits fidèlement avec les datasources actuellement disponibles. Seul le dashboard brouillon « Finance - Mix des moyens de paiement » a été créé dans Superset; il contient le KPI global « Montant total payé ». Il n’est pas publié et ne constitue pas le dashboard demandé.

## Données à réingérer ou corriger

Pour couvrir les axes du PDF, la datasource Finance doit conserver au minimum les dimensions au grain paiement : `order_id`, `payment_type`, `installments`, `payment_value`, date/heure d’achat et les attributs client utilisés (état, ville, code postal, identifiant client). Il faut ensuite recharger/réconcilier le datasource Druid sans perdre ces dimensions dans le roll-up. Les dates et dimensions client absentes du grain paiement peuvent être jointes via une clé commande/client dans une source correctement modélisée.

La hiérarchie commande/panier doit être contrôlée séparément avec `fact_order` et `fact_order_item`, en agrégeant chaque source au même grain avant comparaison.
