# Couverture des intégrations

Les contrôles portent sur des échanges supportés, avec des données existantes et des assertions. Un simple test HTTP vérifie une interface mais ne prouve pas une intégration. La suite `--full` ne saute aucun service absent ; la suite cœur ne couvre que le cœur. Le contrôle Airflow est une deuxième commande obligatoire.

| Origine | Destination(s) | Preuve / contrôle |
|---|---|---|
| CSV ventes, JSON clients, XLSX catalogue | Kafka | Producteurs existants ; acquittement Kafka, topic Bronze et identifiants de ventes |
| PostgreSQL clients/commandes/lignes | Kafka, Trino | Producteur SQL ; contrôle des ventes SQL dans Kafka et requête SQL fédérée |
| OpenData existant / API locale | Kafka, Spark | Événements existants publiés, présence dans Bronze ; API accessible en mode complet |
| Kafka ventes | Spark, Delta | Identifiants des ventes présents dans le topic et dans Delta |
| Kafka clients/catalogue/OpenData | Spark, Parquet S3 | Présence des trois topics dans Bronze |
| Logs access/application | Kafka, Spark, Delta, Iceberg | Déduplication par fichier/ligne/type ; comptes exacts des lignes sources |
| Spark | Workers | Exécution distribuée des pipelines et contrôles de données |
| Spark | RustFS S3, Parquet, Delta, Iceberg REST | Lecture/écriture, comptes et sommes ; catalogue et stockage réellement utilisés |
| Spark événements | RustFS S3, History Server | Applications visibles dans l’API History |
| Trino | PostgreSQL, Iceberg REST, RustFS | Comptes, sommes et jointure fédérée non vide |
| RustFS S3 sales.csv | Druid | Tâche batch terminée, COUNT et SUM exacts |
| Kafka sales.raw | Druid | Supervisor, COUNT DISTINCT des ventes existantes |
| Druid | PostgreSQL métadonnées, ZooKeeper, RustFS S3 | Ingestion réussie et segments S3 présents : chaîne native sollicitée |
| Superset | PostgreSQL, Trino, Druid | Authentification admin puis vraies requêtes SQL Lab et comptes vérifiés |
| Superset | Base PostgreSQL de métadonnées | Migration, compte admin, connexions enregistrées et retrouvées par API |
| Airflow | DAGs, Spark workers, Kafka, RustFS, Delta, Iceberg | DAGs chargés sans erreur + vérification distribuée avec le pilote de l’image Airflow |
| pgAdmin / Kafka UI / Jupyter / portail | Produit associé | Configuration et interface HTTP accessible ; connecteurs testés par les chemins ci-dessus |

**Sans lien direct configuré** : Druid ↔ Iceberg REST, Druid ↔ Delta, Superset ↔ Kafka, pgAdmin ↔ Kafka, ZooKeeper ↔ Trino, et les échanges entre interfaces web. Ces couples passent par Spark, SQL ou les API selon la chaîne ci-dessus ; ils ne sont pas présentés comme des intégrations natives installées. Le contrôle n’invente pas de connecteur entre chaque paire arbitraire de produits.



Le répertoire hôte `donnees` est copié dans les volumes Spark et dans `s3://lakehouse/donnees/`. Le job `10_verify_workspace_s3.py` compare les empreintes SHA-256 via les workers Spark et vérifie les droits de l’utilisateur Spark. Les chemins internes `/opt/spark/data` et `/home/spark/data` restent disponibles.
