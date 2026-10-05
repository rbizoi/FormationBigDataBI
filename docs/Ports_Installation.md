# Ports de la formation — installation complète

L'audit de `compose.yaml` trouve 19 publications TCP et aucun doublon interne.
Les anciens conflits venaient de ports occupés sur la machine, pas de ports
internes des conteneurs. Aucun port fixe ne peut être garanti libre sur tous les PC.

Le fichier `ports.env` fournit la plage 25001–25021 (avec des numéros laissés libres), différente des ports
habituels des autres installations. Le fichier `.env` existant est conservé,
avec ses autres paramètres. Chargez `ports.env` après `.env` pour que les
nouvelles valeurs de ports soient prioritaires. Utilisez les mêmes options
pour toutes les commandes Compose, y compris les tests et l'arrêt.

## Commandes Windows et Linux

```text
docker compose --env-file .env --env-file ports.env --profile full config --quiet
docker compose --env-file .env --env-file ports.env --profile full build
docker compose --env-file .env --env-file ports.env run --no-deps --rm ports-check
docker compose --env-file .env --env-file ports.env --profile full up -d
docker compose --env-file .env --env-file ports.env --profile full ps -a
```

Aucune commande shell ni PowerShell n'est nécessaire. Le contrôle s'exécute
par Docker. Il utilise le moteur Docker via `/var/run/docker.sock`, également
avec les conteneurs Linux de Docker Desktop sous Windows. Il ne stoppe aucun
conteneur existant et ne supprime aucun volume. Il crée uniquement des conteneurs
de test temporaires, publie réellement chaque port et les supprime aussitôt.
Il détecte les publications d'autres projets et les refus de publication par
le moteur (programme local ou réservation de port, notamment sous Windows).
Le moteur ciblé doit être celui de cette installation ; un contexte distant ou
un moteur rootless avec un autre socket nécessite d'adapter le montage du socket.

`PORTS_CHECK_PASS` signifie que tous les ports sont libres ou déjà utilisés par
le bon service de ce même projet. `PORTS_CHECK_FAIL` renvoie un code 1 et indique
tous les conflits, sans attendre un échec à chaque `up`. Les doublons créés par
des personnalisations sont également rejetés. Le rapport `ports-check.json` est
affiché dans le portail. Un refus technique (socket inaccessible, échec de pull,
etc.) est un échec, jamais une fausse validation.

Les services qui publient des ports dépendent de la réussite de `ports-check`.
Le contrôle peut donc également être lancé automatiquement par `up`. Relancez
explicitement `run --no-deps --rm ports-check` avant chaque installation pour
obtenir un état à jour. Un port peut être pris par un autre processus entre
le contrôle et le démarrage : il faut alors refaire le contrôle.

## Plan des ports

| Variable | Port ordinateur |
|---|---:|
| `POSTGRES_PORT` | 25001 |
| `KAFKA_EXTERNAL_PORT` | 25002 |
| `S3_API_PORT` | 25003 |
| `S3_CONSOLE_PORT` | 25004 |
| `ICEBERG_REST_PORT` | 25005 |
| `SPARK_MASTER_UI_PORT` | 25006 |
| `SPARK_WORKER1_UI_PORT` | 25007 |
| `SPARK_WORKER2_UI_PORT` | 25008 |
| `SPARK_HISTORY_UI_PORT` | 25009 |
| `JUPYTER_PORT` | 25010 |
| `SPARK_JOBS_UI_PORT` | 25011 |
| `TRINO_PORT` | 25012 |
| `MOCK_OPENDATA_PORT` | 25013 |
| `AIRFLOW_PORT` | 25014 |
| `PGADMIN_PORT` | 25017 |
| `KAFKA_UI_PORT` | 25018 |
| `DRUID_PORT` | 25019 |
| `SUPERSET_PORT` | 25020 |
| `DASHBOARD_PORT` | 25021 |

Le portail est http://localhost:25021. Les liens de toutes les cartes et
l'adresse Kafka annoncée à l'ordinateur suivent ces paramètres. Les adresses
internes des conteneurs restent identiques : postgres-source:5432,

## En cas de conflit

```text
docker ps --format "table {{.Names}}\t{{.Ports}}"
docker compose ls
```

Modifiez uniquement la valeur du port concerné dans `ports.env`, puis relancez
le contrôle. Ne supprimez pas un autre projet pour libérer un port sans l'avoir
identifié. Pour arrêter cette pile en conservant les données :

```text
docker compose --env-file .env --env-file ports.env --profile '*' down --remove-orphans
```

Après modification de ports, recréez les services concernés et le portail avec
`up -d` (Compose détecte les changements). Si vous utilisiez une autre copie du
projet, arrêtez-la depuis son dossier et son contexte Docker avant la migration.
Aucun effacement des volumes n'est requis.

## Validation des étudiants

Après la fin des initialisations (Exited 0) :

```text
docker compose --env-file .env --env-file ports.env --profile checks run --rm static-check
docker compose --env-file .env --env-file ports.env run --rm objectstore-init --verify-only
docker compose --env-file .env --env-file ports.env --profile checks run --rm integration-check --full
docker compose --env-file .env --env-file ports.env --profile checks run --rm airflow-check
```

Les tests GitHub Actions vérifient les 19 ports avec de vraies publications,
un conflit créé par un conteneur étranger et la reconnaissance d'un service

Consulter le README pour la liste actuelle des services et les commandes de nettoyage.
