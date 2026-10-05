# Matrice de validation des conteneurs

Les interfaces et les flux sont contrôlés séparément. Voir le README pour les commandes et la matrice des intégrations pour les assertions sur les données.

| Service | Exécution | Contrôle |
|---|---|---|
| `ports-check` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `workspace-init` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `postgres-source` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `postgres-bootstrap` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `kafka` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `kafka-init` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `objectstore-permissions` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `objectstore` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `objectstore-init` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `iceberg-catalog-permissions` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `iceberg-rest` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `spark-master` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `spark-worker-1` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `spark-worker-2` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `spark-history` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `spark-jupyter` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `trino` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `mock-opendata` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `api-producer` | Serveur | Interface / fonctionnement dans les flux de la matrice |
| `file-producer` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `postgres-producer` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `web-log-producer` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `airflow-db` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `airflow` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `notebooks-init` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `pgadmin` | Serveur | Interface / fonctionnement dans les flux de la matrice |
| `kafka-ui` | Serveur | Interface / fonctionnement dans les flux de la matrice |
| `druid-db` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `zookeeper` | Serveur | Interface / fonctionnement dans les flux de la matrice |
| `druid-coordinator` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `druid-broker` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `druid-historical` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `druid-middlemanager` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `druid-router` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `superset-db` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `superset-init` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `superset` | Serveur | Healthcheck Compose puis contrôle fonctionnel selon la matrice |
| `integration-check` | Contrôle à la demande | Code de sortie 0 et données produites |
| `airflow-check` | Contrôle à la demande | Interface / fonctionnement dans les flux de la matrice |
| `dashboard` | Serveur | Interface / fonctionnement dans les flux de la matrice |
| `pgadmin-config` | Initialisation / producteur à exécution unique | Code de sortie 0 et données produites |
| `static-check` | Contrôle à la demande | Interface / fonctionnement dans les flux de la matrice |
