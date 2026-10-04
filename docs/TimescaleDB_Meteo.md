# TimescaleDB — chargement et contrôle des observations météo

TimescaleDB 2.30.2 sur PostgreSQL 17 est ajouté via une image officielle dont le
manifeste multiarchitecture est épinglé par SHA-256. Il fonctionne dans les
conteneurs Linux de Docker Desktop sous Windows et dans Docker sous Linux.
Le service dispose de son propre volume `timescaledb-data`, distinct de PostgreSQL.

## Installation

Les mêmes commandes fonctionnent sur les deux systèmes, sans script shell ou PowerShell.
Depuis le dossier contenant `compose.yaml` :

```text
docker compose --profile full --profile checks config --quiet
docker compose --profile timeseries build timescale-load
docker compose --profile timeseries up -d timescaledb pgadmin dashboard
docker compose run --rm pgadmin-config
docker compose up -d --force-recreate pgadmin dashboard
docker compose --profile timeseries run --rm timescale-load
docker compose --profile checks run --rm timescale-check
```

Les deux commandes `pgadmin-config`/recréation actualisent aussi un pgAdmin déjà
installé. Pour une nouvelle installation complète, utiliser le profil `full` :

```text
docker compose --profile full --profile checks build
docker compose --profile full up -d
docker compose --profile full ps -a
docker compose logs -f timescale-load
docker compose --profile checks run --rm timescale-check
```

Le service `timescale-load` charge automatiquement le fichier lors d'un démarrage
avec `full` ou `timeseries`. Attendre `TIMESCALE_LOAD_OK` et `Exited (0)` avant le
contrôle. Sur les machines modestes, les millions d'observations peuvent nécessiter
plusieurs minutes et plusieurs Go de stockage. Aucun volume existant n'est supprimé.

## Interface graphique et accès

Depuis le portail http://localhost:8090, ouvrir la carte **TimescaleDB météo · pgAdmin**.
Dans pgAdmin, développer **Formation → TimescaleDB météo**. L'interface est partagée
avec PostgreSQL ; le deuxième serveur est préenregistré.

| Paramètre | Valeur pédagogique par défaut |
|---|---|
| URL de pgAdmin | http://localhost:5050 |
| Compte de l'interface | admin@formation.fr |
| Mot de passe de l'interface | formation |
| Hôte SQL dans le réseau Docker | timescaledb |
| Port SQL dans Docker | 5432 |
| Hôte/port SQL depuis l'ordinateur | localhost:5433 |
| Base et utilisateur SQL | meteo |
| Mot de passe SQL demandé par pgAdmin | formation |
| Schéma / hypertable | meteo.observations |

Variables Compose personnalisables : `TIMESCALE_DB`, `TIMESCALE_USER`,
`TIMESCALE_PASSWORD`, `TIMESCALE_PORT`, `PGADMIN_EMAIL`, `PGADMIN_PASSWORD`,
`PGADMIN_PORT`. Changer une variable de mot de passe ne modifie pas un compte
stocké dans un volume existant. Les comptes de l'interface et de la base sont distincts.

Dans pgAdmin : **Databases → meteo → Schemas → meteo → Tables → observations**.
Le Query Tool permet d'exécuter :

```sql
SELECT count(*) FROM meteo.observations;
SELECT * FROM meteo.observations ORDER BY observed_at DESC LIMIT 100;
SELECT time_bucket(INTERVAL '1 day', observed_at) AS jour,
       station, avg(temperature) AS temperature_moyenne
FROM meteo.observations
WHERE observed_at >= TIMESTAMPTZ '2020-01-01 00:00:00+00'
GROUP BY jour, station ORDER BY jour, station;
SELECT * FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'meteo';
```

## Source et transformations

`data/meteo.gzip` est **un fichier Parquet avec compression interne**, pas une
archive gzip à décompresser. La version livrée contient 3 591 621 lignes et 24
colonnes, pour 42 stations du 1er janvier 1996 au 31 décembre 2025. Le code lit les métadonnées et charge l'intégralité du fichier courant,
sans limiter le nombre de stations ou de dates.

Les dates sans fuseau sont interprétées comme UTC (hypothèse explicite pour les
données SYNOP). Les identifiants station restent du texte, par exemple `07005`.
Les nulls et NaN deviennent SQL NULL ; les valeurs infinies et les clés manquantes
sont rejetées. Aucune conversion d'unité des mesures n'est effectuée.

| Colonne Parquet | Colonne SQL |
|---|---|
| Station | station |
| DateHeure | observed_at |
| Nom | station_name |
| Latitude | latitude |
| Longitude | longitude |
| Altitude | altitude |
| Zone | zone |
| DirectionVent | wind_direction |
| VitesseVent | wind_speed |
| Temperature | temperature |
| Humidite | humidity |
| Visibilite | visibility |
| Pression | pressure |
| Precipitation | precipitation |
| Heure | hour |
| Jour | day |
| Mois | month |
| Annee | year |
| Semaine | week |
| MoisJour | month_day |
| AnneeMois | year_month |
| AnneeSemaine | year_week |
| AnneeJour | year_day |
| JourNuit | day_night |

L'hypertable est partitionnée mensuellement sur `observed_at`. Trois colonnes de
traçabilité sont ajoutées : `source_name`, `source_sha256`, `source_row` (index
original à partir de zéro). La clé inclut la date et l'index source pour conserver
également des observations ayant la même station et la même date.

## Chargement et relance

`docker/timescale-load/load_meteo.py` lit le Parquet par lots de 8 192 lignes et
utilise PostgreSQL COPY dans une table temporaire. La création de l'hypertable,
la copie et le remplacement des seules lignes `source_name = 'data/meteo.gzip'`
sont réalisés dans une transaction. Une erreur laisse l'import précédent intact.
Les autres sources ne sont pas supprimées. Un verrou évite deux chargements
concurrents de la même source.

Relancer après une modification du fichier :

```text
docker compose --profile timeseries run --rm timescale-load
docker compose --profile checks run --rm timescale-check
```

## Contrôle et rapports

`docker/timescale-load/check_meteo.py` n'écrit aucune donnée dans la base. Il contrôle :

- présence de l'extension TimescaleDB et de l'hypertable ;
- empreinte SHA-256 et manifeste `meteo.ingestions` ;
- nombre total de lignes, stations, bornes temporelles ;
- correspondance des 24 valeurs de chaque ligne avec son index Parquet ;
- stabilité du fichier pendant le contrôle.

Le contrôle emploie un curseur serveur et une transaction de lecture cohérente.
Il renvoie un code 0 et `status: PASS` uniquement si tout correspond ; sinon code 1
et `status: FAIL`. Le rapport est `/reports/timescale-check.json` dans le volume
`timescale-reports`, affiché dans la section Contrôles du portail. Le contrôle est
également appelé par `integration-check --full`.

Le workflow `.github/workflows/timescaledb.yml` vérifie sur un vrai serveur les cas
limites, la relance sans duplication, la corruption d'une valeur, le rollback et
la conservation d'une autre source. Il importe ensuite le fichier complet deux
fois et compare intégralement le résultat. Le serveur enregistré dans pgAdmin et
la carte du portail sont également vérifiés. Les rapports sont joints au run CI.

Sources techniques :
- https://docs.timescale.com/self-hosted/latest/install/installation-docker/
- https://docs.timescale.com/api/latest/hypertable/create_hypertable/
- https://www.pgadmin.org/docs/pgadmin4/latest/container_deployment.html
