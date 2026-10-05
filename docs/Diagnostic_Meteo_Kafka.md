# Diagnostic météo et Kafka

Toutes les commandes sont à lancer à la racine du dépôt après `git pull`.

## Météo

Dans pgAdmin, ouvrir **Formation → TimescaleDB météo → Databases → meteo → Schemas → meteo → Tables → observations** (le nom de base peut être personnalisé dans `.env`). Il s'agit du serveur TimescaleDB, distinct de PostgreSQL source. Une base créée ne signifie pas que le chargement est terminé.

```bash
docker compose --env-file .env --env-file ports.env --profile full build timescale-load kafka-init file-producer
docker compose --env-file .env --env-file ports.env --profile full ps -a timescale-load timescaledb
docker compose --env-file .env --env-file ports.env --profile full logs --tail=100 timescale-load
docker compose --env-file .env --env-file ports.env --profile checks run --rm --entrypoint python timescale-check /app/diagnose_meteo.py
```

Le diagnostic affiche la base utilisée, les bases disponibles, l'hypertable, le nombre de lignes et les dates. Il retourne 1 si la table manque ou est vide. Pour alimenter ou réalimenter la table sans doublons :

```bash
docker compose --env-file .env --env-file ports.env --profile full run --rm timescale-load
docker compose --env-file .env --env-file ports.env --profile checks run --rm timescale-check
```

Le dernier contrôle compare les 24 colonnes de toutes les lignes au Parquet local, et écrit `/reports/timescale-check.json`. Pour le fichier livré : **3 591 621 lignes, 42 stations, de 1996 à 2025**. Attendre `TIMESCALE_LOAD_OK` avant ce contrôle.

## Kafka

`leader=-1` indique une partition sans leader disponible. Le seul listing des topics ne prouve pas qu'ils peuvent recevoir des messages. L'initialisation et le contrôle d'intégration attendent désormais un leader présent et dans les réplicas synchronisés pour chaque partition. Le producteur CSV/JSON/XLSX signale aussi les erreurs de livraison, même si sa file finit vide.

```bash
docker compose --env-file .env --env-file ports.env --profile full logs --tail=200 kafka
docker compose --env-file .env --env-file ports.env --profile full exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:19092 --describe
docker inspect --format '{{.State.Status}} OOMKilled={{.State.OOMKilled}} restarts={{.RestartCount}}' bigdata-training-kafka-1
docker compose --env-file .env --env-file ports.env --profile full run --rm kafka-init
```

Un échec d'initialisation affiche les partitions, leaders et réplicas concernés. Examiner les logs, la mémoire et l'espace disque avant de relancer. Ces commandes ne suppriment aucun volume. Une modification des ports hôte ne change pas l'adresse interne `kafka:19092`.

Après correction de l'état du broker :

```bash
docker compose --env-file .env --env-file ports.env --profile checks run --rm integration-check --full
docker compose --env-file .env --env-file ports.env --profile checks run --rm airflow-check
```
