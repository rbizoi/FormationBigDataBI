> **Installation complète — nouveau plan de ports :** utiliser
> `--env-file .env --env-file ports.env` dans toutes les commandes Compose.
> Les ports externes sont désormais 25000–25021 et le portail est
> http://localhost:25021. Voir [la procédure complète](docs/Ports_Installation.md).
> Lancer `docker compose --env-file .env --env-file ports.env run --no-deps --rm ports-check`
> après la construction, avant `up -d`, pour contrôler tous les conflits à la fois.

<img src="https://raw.githubusercontent.com/rbizoi/FormationBigDataBI/refs/heads/master/images/architecture.png" width="1024">

# Docker formation Big Data et BI
`Windows` et `Linux`

Laboratoire pédagogique utilisable avec **les mêmes commandes Docker** sous Windows (Docker Desktop en mode conteneurs Linux / WSL2) et Linux (Docker Engine + Compose v2, ou Docker Desktop). Aucun script Shell, PowerShell ou CMD à exécuter ; Python et les dépendances tournent dans les conteneurs.

Télécharger et extraire le ZIP du dépôt ou utiliser un checkout existant, puis ouvrir un terminal dans le dossier contenant `compose.yaml`. Docker doit être installé et démarré. Prévoir environ 24–32 Go de RAM disponibles pour la pile complète, plusieurs dizaines de Go de disque et une connexion Internet au premier build. Ce sont des estimations, sans contrôle RAM bloquant. Le cœur reste utilisable séparément.

## Démarrage complet

Les valeurs pédagogiques de secours de Compose sont utilisables directement. Le dépôt ne distribue aucun `.env` avec des secrets personnels. Pour personnaliser les paramètres, créer facultativement `.env` avec un éditeur à partir de `.env.example` avant le premier démarrage. Aucun `cp`, script hôte ou Python hôte n’est nécessaire.

```text
docker version
docker compose version
docker info --format "{{.OSType}}"
docker compose --env-file .env --env-file ports.env --profile full config --quiet
docker compose --env-file .env --env-file ports.env --profile full build
docker compose --env-file .env --env-file ports.env --profile full up -d
```

`OSType` doit être `linux`, y compris sous Windows. Compose attend les dépendances saines et les initialisations terminées. La fin de `up -d` ne constitue pas une validation des échanges de données. Le premier démarrage de la pile complète peut prendre plusieurs minutes.

**Portail : http://localhost:25021**. Il regroupe les interfaces, les identifiants réellement configurés et les rapports. Les boutons ouvrent les interfaces des conteneurs déjà démarrés ; ils ne démarrent pas de conteneurs.

## Contrôles fonctionnels avec les données existantes

```text
docker compose --env-file .env --env-file ports.env --profile checks run --rm integration-check --full
docker compose --env-file .env --env-file ports.env --profile checks run --rm airflow-check
```

Exécuter ces deux commandes successivement. Selon le matériel, prévoir jusqu’à 30–60 minutes pour la première validation complète. La seconde nécessite les tables produites par la première. Chaque commande retourne `0` seulement si ses contrôles passent, et un code non nul en cas d’échec. **La validation complète exige le succès des deux commandes.** Les rapports `reports/integration.json` et `reports/airflow-check.json`, affichés dans le portail, sont horodatés ; les logs Spark détaillés restent dans `reports/`.

Le contrôle publie les CSV, JSON, XLSX, tables PostgreSQL, logs et OpenData déjà présents dans le dépôt ; exécute les pipelines Spark ; compare les comptes et montants CSV/Parquet/Iceberg/Trino ; vérifie les identifiants Kafka/Delta ; ingère `sales.csv` dans Druid depuis S3 ; vérifie un flux Kafka dans Druid et les segments dans RustFS ; exécute des requêtes depuis Superset sur PostgreSQL, Trino et Druid ; vérifie les données de vente dans Elasticsearch après Logstash. Il teste également les interfaces HTTP.

Le contrôle Airflow charge les deux DAGs et exécute une vérification distribuée des données avec **l’image et le pilote Python Airflow**, contre les workers Spark. Il ne simule pas une exécution complète du scheduler Airflow : celle-ci reste à lancer depuis l’interface pour les exercices.

Les contrôles écrivent dans les zones pédagogiques `bronze`, `delta`, `gold`, `logs`, `ml` et les datasources Druid `training_sales` / `training_sales_stream`. Ils republient les événements Kafka ; ne pas utiliser ce laboratoire avec des données de production. Les traitements dédupliquent les identifiants/positions de logs ; les comptes Kafka bruts et Elasticsearch peuvent augmenter à chaque relance. Le supervisor Druid Kafka reste actif pour les exercices.

Voir [la matrice d’intégration](docs/INTEGRATION_MATRIX.md) pour les liens pris en charge. Une interface utilisateur n’est pas un connecteur universel : les couples sans protocole natif sont explicitement marqués sans intégration directe, et les chaînes entre produits sont testées à travers les connecteurs installés.

## Cœur ou profils séparés

```text
docker compose build
docker compose --env-file .env --env-file ports.env up -d
docker compose --env-file .env --env-file ports.env --profile checks run --rm integration-check
```

| Profil | Produits ajoutés | Commande |
|---|---|---|
| `analytics` | Druid, ZooKeeper, métadonnées, Superset | `docker compose --env-file .env --env-file ports.env --profile analytics up -d --build` |
| `elastic` | Elasticsearch, Logstash, Kibana | `docker compose --env-file .env --env-file ports.env --profile elastic up -d` |
| `orchestration` | Airflow et sa base | `docker compose --env-file .env --env-file ports.env --profile orchestration up -d --build` |
| `demo` | API OpenData locale et producteur continu Kafka | `docker compose --env-file .env --env-file ports.env --profile demo up -d --build` |
| `full` | Les quatre ensembles ci-dessus | `docker compose --env-file .env --env-file ports.env --profile full up -d --build` |

Les profils `seed` et `logs` restent disponibles pour lancer les producteurs individuellement ; le contrôle d’intégration les exécute lui-même dans son conteneur.

## Interfaces et identifiants par défaut

Les valeurs pédagogiques par défaut utilisent `formation` pour la base, l’utilisateur et le mot de passe SQL PostgreSQL. Un fichier `.env` facultatif prime sur ces valeurs ; il est exclu de Git.

| Produit / interface | Adresse locale | Utilisateur | Mot de passe ou token |
|---|---|---|---|
| Portail | http://localhost:25021 | Aucun | Aucun |
| PostgreSQL / pgAdmin | http://localhost:25017 | `admin@formation.fr` | `formation` |
| Connexion SQL dans pgAdmin | `postgres-source:5432`, base `formation` | `formation` | `formation` |
| Kafka UI | http://localhost:25018 | Aucun | Aucun |
| RustFS | http://localhost:25004 | `labadmin` | `TRAINING_ONLY_S3_PASSWORD` |
| Spark Master | http://localhost:25006 | Aucun | Aucun |
| Spark Workers | http://localhost:25007 et http://localhost:25008 | Aucun | Aucun |
| Spark History | http://localhost:25009 | Aucun | Aucun |
| Job Spark Jupyter | http://localhost:25011 | Aucun | Seulement pendant une session Spark active |
| JupyterLab | http://localhost:25010 | Aucun | `CHANGE_ME` par défaut ; valeur `JUPYTER_TOKEN` dans le portail |
| Trino | http://localhost:25012 | `formation` (libre) | Aucun |
| Airflow | http://localhost:25014 | Aucun en mode pédagogique `all_admins` | Aucun |
| Kibana | http://localhost:25016 | Aucun | Aucun |
| Druid | http://localhost:25019 | Aucun | Aucun |
| Superset | http://localhost:25020 | `admin` | `formation` |

Les ports sont modifiables dans `.env` ; le portail suit les mêmes variables. Pour pgAdmin, le serveur est préenregistré mais le mot de passe SQL est demandé à la connexion. Changer une variable après la création d’un compte ou d’un volume PostgreSQL ne change pas son mot de passe : le modifier dans le produit, ou repartir de volumes neufs si les données sont jetables. Jupyter lit son token au démarrage du conteneur. Les notebooks existants sont copiés une fois dans un volume nommé ; les modifications dans Jupyter y sont conservées. Les nouveautés sont copiées si leur chemin n’existe pas déjà.

Iceberg REST est une API (`http://localhost:25005/v1/config`) sans console native dans l’image utilisée ; ses tables se consultent dans Superset, Trino ou Jupyter. Elasticsearch a Kibana ; Logstash se supervise avec les logs Docker et les données dans Kibana. ZooKeeper et les bases de métadonnées sont des dépendances internes. Parquet et Delta sont des formats, consultables avec Jupyter/Spark. Power BI Desktop reste une application externe Windows : Superset fournit ici l’interface BI disponible sur les deux systèmes.

Tous les ports publiés sont limités à `127.0.0.1`. Les comptes sont pédagogiques et plusieurs services sont sans authentification. Éviter d’exposer ce Compose sur Internet. Le portail affiche volontairement les accès du laboratoire local.

## Validation statique facultative

```text
docker compose --env-file .env --env-file ports.env --profile checks build static-check
docker compose --env-file .env --env-file ports.env --profile checks run --rm static-check
```

Cette commande vérifie les fichiers et les contrats des données. Elle ne remplace pas les deux contrôles runtime.

## Commandes de contrôle et d’exploitation

```text
docker compose --env-file .env --env-file ports.env --profile full ps -a
docker compose --env-file .env --env-file ports.env --profile full logs --tail 100
docker compose logs postgres-bootstrap kafka-init objectstore-init notebooks-init pgadmin-config
docker compose --env-file .env --env-file ports.env --profile full logs superset-init druid-coordinator druid-middlemanager
docker compose --env-file .env --env-file ports.env --profile full exec airflow airflow dags list
docker compose exec trino trino --user formation --execute "SHOW CATALOGS"
docker compose --env-file .env --env-file ports.env --profile full stop
docker compose --env-file .env --env-file ports.env --profile full start
docker compose --env-file .env --env-file ports.env --profile full down
```

`down` conserve les volumes. Pour **supprimer les données Docker de ce projet** et repartir à zéro :

```text
docker compose --env-file .env --env-file ports.env --profile full --profile checks --profile seed --profile logs down --volumes --remove-orphans
```

Cette dernière commande supprime aussi les notebooks modifiés dans le volume. Les données sources du dépôt et les rapports sur l’hôte restent présents. Ne pas utiliser `docker system prune` pour réinitialiser ce laboratoire.

## Portée des vérifications de cette modification

Configuration validée avec Docker Compose, syntaxes Python et contrats de fichiers vérifiés. L’environnement d’édition ne possède pas de daemon Docker : les images n’y ont pas été construites, les conteneurs n’y ont pas démarré et les intégrations runtime ne sont **pas encore certifiées**. Les commandes de contrôle ci-dessus doivent réussir sur votre machine pour confirmer la pile complète. Les anciens documents de correction décrivent l’historique ; ce README est la procédure actuelle.

## Accès Spark, Airflow et copie intégrale vers S3

Les volumes Docker `spark-data` et `spark-jobs` sont initialisés depuis les
répertoires du projet par `workspace-init`, sans changer les droits des fichiers
Windows/Linux de l'hôte. Spark est propriétaire et peut lire/écrire les deux
volumes. Les répertoires sont en mode 2775 et les fichiers en mode 664, groupe 0.
`/home/spark/data` et `/home/spark/jobs` pointent respectivement vers
`/opt/spark/data` et `/opt/spark/jobs` : les jobs existants restent compatibles.

| Composants | Données | Jobs |
|---|---|---|
| Spark master, workers 1/2, history, Jupyter | lecture/écriture, utilisateur spark | lecture/écriture, utilisateur spark |
| Airflow et airflow-check | lecture seule, utilisateur airflow | lecture seule, utilisateur airflow |
| integration-check | lecture/écriture, utilisateur spark | lecture/écriture, utilisateur spark |
| Producteurs fichiers/logs, API simulée, Druid middlemanager | lecture du répertoire data de l'hôte | pas de montage jobs |
| Autres services | échanges réseau/API/S3, pas de montage de ces répertoires | pas de montage jobs |

`objectstore-init` copie **tous les fichiers** du répertoire `data` vers
`s3://lakehouse/data/`, en conservant les sous-répertoires. Cela inclut Olist,
la météo, les logs et les fichiers Parquet/gzip. Chaque copie est relue et
comparée par SHA-256. Le manifeste est `s3://lakehouse/data-manifest.json`.
La copie utilise l'API S3 de RustFS sur `http://objectstore:9000` ; Spark utilise
les identifiants déjà configurés et les chemins `s3a://lakehouse/data/...`.
L'accès Spark utilise les JAR Hadoop S3A déjà inclus dans l'image.

### Recréer tous les conteneurs (Windows et Linux)

Depuis ce dossier, avec le même nom de projet que l'installation précédente :

```text
docker compose --env-file .env --env-file ports.env --profile full --profile checks down
docker compose --env-file .env --env-file ports.env --profile full --profile checks build
docker compose --env-file .env --env-file ports.env run --rm workspace-init
docker compose --env-file .env --env-file ports.env --profile full up -d --force-recreate
docker compose --env-file .env --env-file ports.env run --rm objectstore-init
docker compose --env-file .env --env-file ports.env run --rm objectstore-init --verify-only
docker compose --env-file .env --env-file ports.env --profile full ps -a
docker compose --env-file .env --env-file ports.env --profile checks run --rm integration-check --full
docker compose --env-file .env --env-file ports.env --profile checks run --rm airflow-check
```

Ces commandes conservent les volumes PostgreSQL, Kafka, RustFS et les autres
volumes persistants. L'initialisation recopie les fichiers livrés et normalise
les droits des volumes Spark. Elle remplace les fichiers portant le même nom ;
sauvegarder les modifications pédagogiques avant une nouvelle initialisation.
Elle ne supprime pas les fichiers supplémentaires. La copie S3 ne supprime pas
non plus d'anciens objets supplémentaires ; le test signale une divergence.
Après ajout/modification des données sources, relancer `workspace-init` puis
`objectstore-init` avant les tests. Arrêter les traitements avant cette copie.

Le nouveau job `10_verify_workspace_s3.py` vérifie la lecture de chaque fichier,
la création/suppression de fichiers par Spark dans les deux répertoires, les
alias `/home/spark`, les accès des exécuteurs non root, les SHA-256 via une
lecture Spark distribuée de S3 et les 2 000 ventes (identifiants distincts).
`airflow-check` lance le même job sous l'utilisateur Airflow : lecture locale
seule et traitements distribués sur les workers Spark. Les rapports sont dans
le volume `check-reports`, consultables via le portail.

```text
docker compose exec --user spark spark-jupyter python3 -c "from pathlib import Path; print(list(Path('/home/spark/data').iterdir())); print(list(Path('/home/spark/jobs').iterdir()))"
docker compose --env-file .env --env-file ports.env --profile full exec --user airflow airflow python3 -c "from pathlib import Path; print(Path('/home/spark/data/input/sales.csv').open().readline()); print(Path('/home/spark/jobs/10_verify_workspace_s3.py').is_file())"
docker compose logs workspace-init objectstore-init
```

Validation de cette révision : contrats statiques et tests Python exécutés.
Construction et démarrage Docker non exécutés dans l'environnement de création,
qui ne dispose pas du moteur Docker. Les commandes d'intégration ci-dessus
restent nécessaires sur la machine de formation.

## TimescaleDB et données météo

TimescaleDB est disponible avec les profils `timeseries` et `full`. La carte
**TimescaleDB météo · pgAdmin** du portail ouvre pgAdmin avec le serveur
`timescaledb:5432` préenregistré (base/utilisateur `meteo`, mot de passe pédagogique
`formation`). Le port SQL depuis l'hôte est `5433`.

Le service `timescale-load` charge les **3 591 621 observations et 24 colonnes**
du fichier Parquet `data/meteo.gzip` dans `meteo.observations`, une hypertable
partitionnée par mois. Le chargement est transactionnel et peut être relancé.

```text
docker compose --env-file .env --env-file ports.env --profile timeseries build timescale-load
docker compose --env-file .env --env-file ports.env --profile timeseries up -d timescaledb pgadmin dashboard
docker compose --env-file .env --env-file ports.env run --rm pgadmin-config
docker compose --env-file .env --env-file ports.env up -d --force-recreate pgadmin dashboard
docker compose --env-file .env --env-file ports.env --profile timeseries run --rm timescale-load
docker compose --env-file .env --env-file ports.env --profile checks run --rm timescale-check
```

Le contrôle compare toutes les lignes et colonnes au fichier d'origine ; le
rapport est affiché dans le portail. Pour la procédure complète, les paramètres,
le mapping des colonnes et les requêtes SQL, consulter
[TimescaleDB_Meteo.md](docs/TimescaleDB_Meteo.md).
