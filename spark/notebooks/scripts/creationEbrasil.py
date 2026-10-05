def creationParquetEbrasil(rep_source, rep_dest):
    """
        Création des fichiers parquet à partir des fichiers .csv du répertoire « data/ebrasil »
        rep_source : répertoire source qui doit contenir impérativement les 9 fichiers csv
                                olist_customers_dataset.csv
                                olist_order_items_dataset.csv
                                olist_order_reviews_dataset.csv
                                olist_products_dataset.csv
                                product_category_name_translation.csv
                                olist_geolocation_dataset.csv
                                olist_order_payments_dataset.csv
                                olist_orders_dataset.csv
                                olist_sellers_dataset.csv
        rep_dest : répertoire destination, s’il n’existe pas, il est créé
    """
    import pandas as pd, os

    def controleFichier(fichier=''):
        if not (os.path.exists(fichier) & (not os.path.isdir(fichier))):
            raise Exception(f"Le fichier {fichier} n’existe pas !!!")
        print(f"{'-' * 50}\nfichier existent\t:\t{fichier}\n{'-' * 50}")
        return True

    def lectureFichier(fichier='', rep_source=''):
        assert controleFichier(fichier=os.path.join(rep_source, fichier))
        print(f"{'-' * 50}\nlecture du fichier\t:\t{fichier}\n{'-' * 50}")
        return pd.read_csv(os.path.join(rep_source, fichier))

    if len(rep_dest)   == 0:  raise Exception(f"Le répertoire rep_dest {rep_dest} n’a pas été saisié !!!")
    if len(rep_source) == 0:  raise Exception(f"Le répertoire rep_source {rep_source} n’a pas été saisié !!!")

    if not (os.path.exists(rep_source) & os.path.isdir(rep_source)):
        raise Exception(f"Le répertoire {rep_source} n’existe pas !!!")

    listeFichiers = {nom.replace('olist_', '').replace('_dataset.csv', '').replace('_name_translation.csv', ''): nom
                     for nom in os.listdir(rep_source)}
    if not (('geolocation' in listeFichiers) &
            ('products' in listeFichiers) &
            ('customers' in listeFichiers) &
            ('orders' in listeFichiers) &
            ('product_category' in listeFichiers) &
            ('order_reviews' in listeFichiers) &
            ('order_items' in listeFichiers) &
            ('order_payments' in listeFichiers) &
            ('sellers' in listeFichiers)):
        raise Exception(f"Le répertoire {rep_source} n’a pas les fichiers e-brasil !!!")

    dictEtats = {'AC': 'Acre',
                 'AL': 'Alagoas',
                 'AP': 'Amapá',
                 'AM': 'Amazonas',
                 'BA': 'Bahia',
                 'CE': 'Ceará',
                 'ES': 'Espírito Santo',
                 'GO': 'Goiás',
                 'MA': 'Maranhão',
                 'MT': 'Mato Grosso',
                 'MS': 'Mato Grosso do Sul',
                 'MG': 'Minas Gerais',
                 'PA': 'Pará',
                 'PB': 'Paraïba',
                 'PR': 'Paraná',
                 'PE': 'Pernambouc',
                 'PI': 'Piauí',
                 'RJ': 'Rio de Janeiro',
                 'RN': 'Rio Grande do Norte',
                 'RS': 'Rio Grande do Sul',
                 'RO': 'Rondônia',
                 'RR': 'Roraima',
                 'SC': 'Santa Catarina',
                 'SP': 'São Paulo',
                 'SE': 'Sergipe',
                 'TO': 'Tocantins',
                 'DF': 'District fédéral'}

    if not (os.path.exists(rep_dest) & os.path.isdir(rep_dest)):
        os.makedirs(rep_dest)

    donnees = lectureFichier(listeFichiers['orders'], rep_source)
    donnees['purchase_timestamp'] = pd.to_datetime(donnees.order_purchase_timestamp, format='%Y-%m-%d %H:%M:%S')
    donnees['approved_at'] = pd.to_datetime(donnees.order_approved_at, format='%Y-%m-%d %H:%M:%S')
    donnees['delivered_carrier'] = pd.to_datetime(donnees.order_delivered_carrier_date, format='%Y-%m-%d %H:%M:%S')
    donnees['delivered_customer'] = pd.to_datetime(donnees.order_delivered_customer_date, format='%Y-%m-%d %H:%M:%S')
    donnees['estimated_delivery'] = pd.to_datetime(donnees.order_estimated_delivery_date, format='%Y-%m-%d %H:%M:%S')
    donnees['status'] = donnees['order_status']
    donnees.drop(columns=['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
                          'order_delivered_customer_date', 'order_estimated_delivery_date', 'order_status'],
                 inplace=True)
    donnees['annee'] = donnees.purchase_timestamp.dt.year
    donnees['mois'] = donnees.purchase_timestamp.dt.month
    donnees['annee_mois'] = donnees.purchase_timestamp.dt.year * 100 + donnees.purchase_timestamp.dt.month
    donnees['jour'] = donnees.purchase_timestamp.dt.day
    donnees['annee_jour'] = donnees.purchase_timestamp.dt.year * 1000 + donnees.purchase_timestamp.dt.day
    donnees['jour_semaine'] = donnees.purchase_timestamp.dt.day_of_week
    donnees['trimestre'] = donnees.purchase_timestamp.dt.quarter
    donnees['annee_trimestre'] = donnees.purchase_timestamp.dt.year * 10 + donnees.purchase_timestamp.dt.quarter
    donnees['semaine'] = donnees.purchase_timestamp.dt.isocalendar().week.astype('int32')
    donnees['annee_semaine'] = (donnees.purchase_timestamp.dt.year * 100 +
                                donnees.purchase_timestamp.dt.isocalendar().week).astype('int32')
    donnees['heure'] = donnees.purchase_timestamp.dt.hour
    # Intervalle depuis la commande
    donnees['approuvee'] = (donnees.approved_at - donnees.purchase_timestamp).dt.seconds / 60 / 60
    donnees['envoyee'] = (donnees.delivered_carrier - donnees.purchase_timestamp).dt.seconds / 60 / 60
    donnees['livree'] = (donnees.delivered_customer - donnees.purchase_timestamp).dt.seconds / 60 / 60
    donnees['estimee'] = (donnees.estimated_delivery - donnees.purchase_timestamp).dt.seconds / 60 / 60
    donnees.to_parquet(os.path.join(rep_dest, 'orders.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'orders.parquet'))
    # 2. DataFrame $customers$
    donnees = lectureFichier(listeFichiers['customers'], rep_source)
    donnees['name_state'] = donnees['customer_state'].apply(lambda x: dictEtats[x])
    donnees['customer_zip_code_prefix'] = donnees['customer_zip_code_prefix'].astype('int32')
    donnees.rename(columns={'customer_zip_code_prefix': 'zip_code', 'customer_city': 'city', 'customer_state': 'state'},
                   inplace=True)
    donnees.to_parquet(os.path.join(rep_dest, 'customers.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'customers.parquet'))
    # 3. DataFrame $items$
    donnees = lectureFichier(listeFichiers['order_items'], rep_source)
    donnees = donnees.merge(
        pd.read_parquet(os.path.join(rep_dest, 'orders.parquet'))[['order_id', 'purchase_timestamp']],
        on='order_id')
    donnees['shipping_limit'] = pd.to_datetime(donnees.shipping_limit_date, format='%Y-%m-%d %H:%M:%S')
    donnees['limit'] = (donnees.shipping_limit - donnees.purchase_timestamp).dt.seconds / 60 / 60
    donnees.drop(columns=['shipping_limit_date', 'purchase_timestamp'], inplace=True)
    donnees.groupby(['order_id', 'product_id']).agg('count').shape
    donnees.groupby(['order_id', 'product_id', 'seller_id']).agg('count').shape
    donnees.groupby(['order_id', 'order_item_id', 'product_id', 'seller_id']).agg('count').shape, donnees.shape
    donnees.to_parquet(os.path.join(rep_dest, 'items.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'items.parquet'))
    # 4. DataFrame $payments$
    donnees = lectureFichier(listeFichiers['order_payments'], rep_source)
    donnees.rename(columns={col: col.replace('payment_', '') for col in donnees.columns[1:]}, inplace=True)
    donnees.to_parquet(os.path.join(rep_dest, 'paymentsI.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'paymentsI.parquet'))
    payments = donnees.pivot_table(index='order_id', columns='type',
                                   values=['installments', 'value'], aggfunc='sum', fill_value=0, dropna=False)
    payments.columns = [col[0].replace('installments', 'int') + '_' + col[1] for col in payments.columns]
    payments[['int_boleto',
              'int_credit_card',
              'int_debit_card',
              'int_not_defined',
              'int_voucher']] = payments[['int_boleto',
                                          'int_credit_card',
                                          'int_debit_card',
                                          'int_not_defined',
                                          'int_voucher']].astype('int8')
    payments['value'] = payments.value_boleto + \
                        payments.value_credit_card + \
                        payments.value_debit_card + \
                        payments.value_not_defined + \
                        payments.value_voucher

    payments.reset_index().to_parquet(os.path.join(rep_dest, 'payments.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'payments.parquet'))
    # 5. DataFrame $reviews$
    donnees = lectureFichier(listeFichiers['order_reviews'], rep_source)
    donnees.rename(columns={col: col.replace('review_', '') for col in donnees.columns[2:]}, inplace=True)
    donnees.creation_date = pd.to_datetime(donnees.creation_date, format='%Y-%m-%d %H:%M:%S')
    donnees.answer_timestamp = pd.to_datetime(donnees.answer_timestamp, format='%Y-%m-%d %H:%M:%S')
    donnees = donnees.merge(
        pd.read_parquet(os.path.join(rep_dest, 'orders.parquet'))[['order_id', 'purchase_timestamp']],
        on='order_id')
    donnees['creation'] = ((donnees.creation_date - donnees.purchase_timestamp).dt.days * 24 + (
            donnees.creation_date - donnees.purchase_timestamp).dt.seconds / 60 / 60).astype('int32')
    donnees['answer'] = ((donnees.answer_timestamp - donnees.creation_date).dt.days * 24 + (
            donnees.answer_timestamp - donnees.creation_date).dt.seconds / 60 / 60).astype('int32')
    donnees.score = donnees.score.astype('int16')
    donnees['comment'] = donnees.comment_message.apply(lambda x: len(str(x))).astype('int16')

    donnees.to_parquet(os.path.join(rep_dest, 'reviewsI.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'reviewsI.parquet'))
    # Transformation de la table
    donnees.pivot_table(index='order_id',
                        columns='score',
                        values=['review_id', 'creation', 'answer', 'comment'],
                        aggfunc={'review_id': 'count', 'creation': 'sum', 'answer': 'sum', 'comment': 'sum'},
                        fill_value=0)
    donnees = donnees.pivot_table(index='order_id',
                                  columns='score',
                                  values=['review_id', 'creation', 'answer', 'comment'],
                                  aggfunc={'review_id': 'count', 'creation': 'sum', 'answer': 'sum', 'comment': 'sum'},
                                  fill_value=0)
    donnees.columns = [f"{col[0].replace('review_id', 'score')}_{col[1]}" for col in donnees.columns]
    donnees.reset_index(inplace=True)
    donnees['score'] = donnees.score_1 + \
                       donnees.score_2 + \
                       donnees.score_3 + \
                       donnees.score_4 + \
                       donnees.score_5
    donnees['answer'] = donnees.answer_1 + \
                        donnees.answer_2 + \
                        donnees.answer_3 + \
                        donnees.answer_4 + \
                        donnees.answer_5
    donnees['creation'] = donnees.creation_1 + \
                          donnees.creation_2 + \
                          donnees.creation_3 + \
                          donnees.creation_4 + \
                          donnees.creation_5
    donnees['comment'] = donnees.comment_1 + \
                         donnees.comment_2 + \
                         donnees.comment_3 + \
                         donnees.comment_4 + \
                         donnees.comment_5
    donnees.to_parquet(os.path.join(rep_dest, 'reviews.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'reviews.parquet'))
    # 6. DataFrame $products$
    products = lectureFichier(listeFichiers['products'], rep_source)
    products_translated = lectureFichier(listeFichiers['product_category'], rep_source)
    donnees = lectureFichier(listeFichiers['products'], rep_source)
    donnees.rename(columns={col: col.replace('product_', '') for col in donnees.columns[1:]}, inplace=True)
    categories = lectureFichier(listeFichiers['product_category'], rep_source)
    categories.rename(columns={col: col.replace('product_', '') for col in categories.columns}, inplace=True)
    donnees = donnees.merge(categories, how='left', on='category_name')
    donnees.loc[donnees["category_name"] == "portateis_cozinha_e_preparadores_de_alimentos",
    "category_name_english"
    ] = "kitchenware_tools_and_gadget"

    donnees.loc[donnees["category_name"] == "pc_gamer", "category_name_english"] = "pc_gamer"
    donnees["category_name_english"] = (donnees["category_name_english"].fillna("not documented"))

    donnees.drop(columns='category_name', inplace=True)
    donnees.rename(columns={'category_name_english': 'category_name'}, inplace=True)
    donnees.to_parquet(os.path.join(rep_dest, 'products.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'products.parquet'))
    # 7. DataFrame $sellers$
    donnees = lectureFichier(listeFichiers['sellers'], rep_source)
    donnees.rename(columns={col: col.replace('seller_', '').replace('_prefix', '') for col in donnees.columns[1:]},
                   inplace=True)
    donnees['name_state'] = donnees['state'].apply(lambda x: dictEtats[x])
    donnees['zip_code'] = donnees['zip_code'].astype('int32')
    donnees.to_parquet(os.path.join(rep_dest, 'sellers.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'sellers.parquet'))
    # 8. DataFrame $geolocation$
    donnees = lectureFichier('olist_geolocation_dataset.csv', rep_source)
    geographie = donnees.groupby('zip_code').agg({
        'lat': ['min', 'median', 'max'],
        'lng': ['min', 'median', 'max'],
        'city': 'first',
        'state': 'first'
    }).reset_index()
    geographie.columns = [geographie.columns[0][0]] + [col[0] + '_' + col[1] for col in geographie.columns[1:]]
    geographie.columns = [col.replace('_first', '').replace('_median', '') for col in geographie.columns]
    geographie = geographie[['zip_code', 'city', 'state', 'lat', 'lng', 'lat_min', 'lat_max', 'lng_min', 'lng_max']]
    geographie.to_parquet(os.path.join(rep_dest, 'geolocation.parquet'), compression='gzip', engine='pyarrow')
    assert controleFichier(fichier=os.path.join(rep_dest, 'geolocation.parquet'))


def creationPostgreSQLebrasil(rep_source='../ecommerce'):
    """
    Création des tables à partir des fichiers parquet
    rep_source : répertoire source qui doit contenir impérativement les 9 fichiers parquet
    """
    import pandas as pd, os, sqlalchemy

    url = sqlalchemy.URL.create(
        drivername="postgresql+psycopg2",
        username="formation",
        password="formation",
        host="postgres-source",
        port=5432,
        database="ebrasil",
    )

    engine = sqlalchemy.create_engine(
        url,  # url = "postgresql://formation:formation@postgres-source:5432/formation"
        pool_pre_ping=True,
    )

    print("connecting with engine " + str(engine))

    with engine.connect() as connection:
        print(connection.execute(sqlalchemy.text("SELECT current_database(), current_user")).fetchone())

    # --01
    donnees = pd.read_parquet(os.path.join(rep_source, 'orders.parquet'),
                              columns=['order_id', 'customer_id', 'purchase_timestamp', 'approved_at',
                                       'delivered_carrier', 'delivered_customer',
                                       'estimated_delivery', 'status'])
    # -------------------table  orders  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('orders',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "order_id": sqlalchemy.String(80),
                           "customer_id": sqlalchemy.String(80),
                           "purchase_timestamp": sqlalchemy.DateTime(),
                           "approved_at": sqlalchemy.DateTime(),
                           "delivered_carrier": sqlalchemy.DateTime(),
                           "delivered_customer": sqlalchemy.DateTime(),
                           "estimated_delivery": sqlalchemy.DateTime(),
                           "status": sqlalchemy.String(80)
                       })
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE orders
                                               ADD CONSTRAINT orders_pk PRIMARY KEY (order_id)
                                           """))
    # --02
    donnees = pd.read_parquet(os.path.join(rep_source, 'customers.parquet'),
                              columns=['customer_id', 'customer_unique_id', 'zip_code', 'city', 'state', 'name_state'])
    # -------------------table  customers  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('customers',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "customer_id": sqlalchemy.types.String(80),
                           "customer_unique_id": sqlalchemy.types.String(80),
                           "zip_code": sqlalchemy.types.Integer(),
                           "city": sqlalchemy.types.String(80),
                           "state": sqlalchemy.types.String(80),
                           "name_state": sqlalchemy.types.String(80)
                       })
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE customers
                                               ADD CONSTRAINT customers_pk PRIMARY KEY (customer_id)
                                           """))
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE orders
                                               ADD CONSTRAINT orders_customers_fk FOREIGN KEY (customer_id)
                                                   REFERENCES customers (customer_id)
                                           """))
        # --03
    donnees = pd.read_parquet(os.path.join(rep_source, 'items.parquet'),
                              columns=['order_id', 'order_item_id', 'product_id', 'seller_id', 'price', 'freight_value',
                                       'shipping_limit', 'limit'])
    # -------------------table  items  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('items',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "order_id": sqlalchemy.types.String(80),
                           "order_item_id": sqlalchemy.types.Integer(),
                           "product_id": sqlalchemy.types.String(80),
                           "seller_id": sqlalchemy.types.String(80),
                           "price": sqlalchemy.types.Float(),
                           "freight_value": sqlalchemy.types.Float(),
                           "shipping_limit": sqlalchemy.types.DateTime(),
                           "limit": sqlalchemy.types.Float()
                       })
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE items
                                               ADD CONSTRAINT items_pk PRIMARY KEY (order_id, order_item_id)
                                           """))
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE items
                                               ADD CONSTRAINT orders_items_fk FOREIGN KEY (order_id)
                                                   REFERENCES orders (order_id)
                                           """))
    # --04
    donnees = pd.read_parquet(os.path.join(rep_source, 'paymentsI.parquet'),
                              columns=['order_id', 'sequential', 'type', 'installments', 'value'])
    # -------------------table  payments  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('payments',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "order_id": sqlalchemy.types.String(80),
                           "sequential": sqlalchemy.types.Integer(),
                           "type": sqlalchemy.types.String(80),
                           "installments": sqlalchemy.types.Integer(),
                           "value": sqlalchemy.types.Float()
                       })
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE payments
                                               ADD CONSTRAINT payments_pk PRIMARY KEY (order_id, sequential)
                                           """))
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE payments
                                               ADD CONSTRAINT orders_payments_fk FOREIGN KEY (order_id)
                                                   REFERENCES orders (order_id)
                                           """))
        # --04
    donnees = pd.read_parquet(os.path.join(rep_source, 'payments.parquet'),
                              columns=['order_id', 'int_boleto', 'int_credit_card', 'int_debit_card', 'int_not_defined',
                                       'int_voucher',
                                       'value_boleto', 'value_credit_card', 'value_debit_card', 'value_not_defined',
                                       'value_voucher', 'value'])
    # -------------------table  paymentsP  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.reset_index().to_sql('payments_p',
                                     con=connection,
                                     if_exists='replace',
                                     index=False,
                                     dtype={
                                         "order_id": sqlalchemy.types.String(80),
                                         "int_boleto": sqlalchemy.types.Integer(),
                                         "int_credit_card": sqlalchemy.types.Integer(),
                                         "int_debit_card": sqlalchemy.types.Integer(),
                                         "int_not_defined": sqlalchemy.types.Integer(),
                                         "int_voucher": sqlalchemy.types.Integer(),
                                         "value_boleto": sqlalchemy.types.Float(),
                                         "value_credit_card": sqlalchemy.types.Float(),
                                         "value_debit_card": sqlalchemy.types.Float(),
                                         "value_not_defined": sqlalchemy.types.Float(),
                                         "value_voucher": sqlalchemy.types.Float(),
                                         "value": sqlalchemy.types.Float()
                                     })
        # --05
    donnees = pd.read_parquet(os.path.join(rep_source, 'reviewsI.parquet'),
                              columns=['review_id', 'order_id', 'score', 'comment_title', 'comment_message',
                                       'creation_date', 'answer_timestamp',
                                       'purchase_timestamp', 'creation', 'answer', 'comment'])
    # -------------------table  reviews  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('reviews',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "review_id": sqlalchemy.types.String(80),
                           "order_id": sqlalchemy.types.String(80),
                           "score": sqlalchemy.types.Integer(),
                           "comment_title": sqlalchemy.types.String(80),
                           "comment_message": sqlalchemy.types.String(256),
                           "creation_date": sqlalchemy.types.DateTime(),
                           "answer_timestamp": sqlalchemy.types.DateTime(),
                           "purchase_timestamp": sqlalchemy.types.DateTime(),
                           "creation": sqlalchemy.types.Integer(),
                           "answer": sqlalchemy.types.Integer(),
                           "comment": sqlalchemy.types.Integer()
                       })
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE reviews
                                               ADD CONSTRAINT reviews_pk PRIMARY KEY (order_id, review_id)
                                           """))
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE reviews
                                               ADD CONSTRAINT orders_reviews_fk FOREIGN KEY (order_id)
                                                   REFERENCES orders (order_id)
                                           """))
    # --05
    donnees = pd.read_parquet(os.path.join(rep_source, 'reviews.parquet'),
                              columns=['order_id', 'answer_1', 'answer_2', 'answer_3', 'answer_4', 'answer_5',
                                       'comment_1', 'comment_2', 'comment_3',
                                       'comment_4', 'comment_5', 'creation_1', 'creation_2', 'creation_3', 'creation_4',
                                       'creation_5', 'score_1',
                                       'score_2', 'score_3', 'score_4', 'score_5', 'score', 'answer', 'creation',
                                       'comment'])
    # -------------------table  reviewsP  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('reviews_p',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "order_id": sqlalchemy.types.String(80),
                           "answer_1": sqlalchemy.types.Integer(),
                           "answer_2": sqlalchemy.types.Integer(),
                           "answer_3": sqlalchemy.types.Integer(),
                           "answer_4": sqlalchemy.types.Integer(),
                           "answer_5": sqlalchemy.types.Integer(),
                           "comment_1": sqlalchemy.types.Integer(),
                           "comment_2": sqlalchemy.types.Integer(),
                           "comment_3": sqlalchemy.types.Integer(),
                           "comment_4": sqlalchemy.types.Integer(),
                           "comment_5": sqlalchemy.types.Integer(),
                           "creation_1": sqlalchemy.types.Integer(),
                           "creation_2": sqlalchemy.types.Integer(),
                           "creation_3": sqlalchemy.types.Integer(),
                           "creation_4": sqlalchemy.types.Integer(),
                           "creation_5": sqlalchemy.types.Integer(),
                           "score_1": sqlalchemy.types.Integer(),
                           "score_2": sqlalchemy.types.Integer(),
                           "score_3": sqlalchemy.types.Integer(),
                           "score_4": sqlalchemy.types.Integer(),
                           "score_5": sqlalchemy.types.Integer(),
                           "score": sqlalchemy.types.Integer(),
                           "answer": sqlalchemy.types.Integer(),
                           "creation": sqlalchemy.types.Integer(),
                           "comment": sqlalchemy.types.Integer()
                       })
    # --06
    donnees = pd.read_parquet(os.path.join(rep_source, 'products.parquet'),
                              columns=['product_id', 'name_lenght', 'description_lenght', 'photos_qty', 'weight_g',
                                       'length_cm', 'height_cm', 'width_cm', 'category_name'])
    # -------------------table  products  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('products',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "product_id": sqlalchemy.types.String(80),
                           "name_lenght": sqlalchemy.types.Float(),
                           "description_lenght": sqlalchemy.types.Float(),
                           "photos_qty": sqlalchemy.types.Float(),
                           "weight_g": sqlalchemy.types.Float(),
                           "length_cm": sqlalchemy.types.Float(),
                           "height_cm": sqlalchemy.types.Float(),
                           "width_cm": sqlalchemy.types.Float(),
                           "category_name": sqlalchemy.types.String(80)
                       })
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE products
                                               ADD CONSTRAINT products_pk PRIMARY KEY (product_id)
                                           """))
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE items
                                               ADD CONSTRAINT products_items_fk FOREIGN KEY (product_id)
                                                   REFERENCES products (product_id)
                                           """))
        # --07
    donnees = pd.read_parquet(os.path.join(rep_source, 'sellers.parquet'),
                              columns=['seller_id', 'zip_code', 'city', 'state', 'name_state'])
    # -------------------table  sellers  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('sellers',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "seller_id": sqlalchemy.types.String(80),
                           "zip_code": sqlalchemy.types.Integer(),
                           "city": sqlalchemy.types.String(80),
                           "state": sqlalchemy.types.String(80),
                           "name_state": sqlalchemy.types.String(80)
                       })
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE sellers
                                               ADD CONSTRAINT sellers_pk PRIMARY KEY (seller_id)
                                           """))
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE items
                                               ADD CONSTRAINT sellers_items_fk FOREIGN KEY (seller_id)
                                                   REFERENCES sellers (seller_id)
                                           """))
        # --08
    donnees = pd.read_parquet(os.path.join(rep_source, 'geolocation.parquet'),
                              columns=['zip_code', 'city', 'state', 'lat', 'lng', 'lat_min', 'lat_max', 'lng_min',
                                       'lng_max'])

    customers = pd.read_parquet(os.path.join(rep_source, 'customers.parquet'),
                                columns=['zip_code', 'city', 'name_state'])  # .rename(columns={'name_state':'state'})
    sellers = pd.read_parquet(os.path.join(rep_source, 'sellers.parquet'),
                              columns=['zip_code', 'city', 'name_state'])  # .rename(columns={'name_state':'state'})

    nouveaux_codes = pd.concat([customers[~customers.zip_code.isin(donnees.zip_code)],
                                sellers[~sellers.zip_code.isin(donnees.zip_code)]],
                               ignore_index=True).rename(columns={'name_state': 'state'}).drop_duplicates()

    donnees = pd.concat([donnees, nouveaux_codes], ignore_index=True)
    # -------------------table  sellers  ------------------------------------------------------------------------
    with engine.connect() as connection:
        donnees.to_sql('geolocation',
                       con=connection,
                       if_exists='replace',
                       index=False,
                       dtype={
                           "zip_code": sqlalchemy.types.Integer(),
                           "city": sqlalchemy.types.String(80),
                           "state": sqlalchemy.types.String(80),
                           "lat": sqlalchemy.types.Float(),
                           "lng": sqlalchemy.types.Float(),
                           "lat_min": sqlalchemy.types.Float(),
                           "lat_max": sqlalchemy.types.Float(),
                           "lng_min": sqlalchemy.types.Float(),
                           "lng_max": sqlalchemy.types.Float()
                       })
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE geolocation
                                               ADD CONSTRAINT geolocation_pk PRIMARY KEY (zip_code)
                                           """))
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE customers
                                               ADD CONSTRAINT geolocation_customers_fk FOREIGN KEY (zip_code)
                                                   REFERENCES geolocation (zip_code)
                                           """))
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           ALTER TABLE sellers
                                               ADD CONSTRAINT geolocation_sellers_fk FOREIGN KEY (zip_code)
                                                   REFERENCES geolocation (zip_code)
                                           """))

    with engine.connect() as connection:
        requete = """ \
                  select * \
                  from (select 'orders     ' table, count(*) enregistrements \
                        from orders \
                        union all \
                        select 'customers  ', count (*) \
                        from customers \
                        union all \
                        select 'sellers    ', count (*) \
                        from sellers \
                        union all \
                        select 'items      ', count (*) \
                        from items \
                        union all \
                        select 'payments   ', count (*) \
                        from payments \
                        union all \
                        select 'payments_p ', count (*) \
                        from payments_p \
                        union all \
                        select 'reviews    ', count (*) \
                        from reviews \
                        union all \
                        select 'reviews_p  ', count (*) \
                        from reviews_p \
                        union all \
                        select 'products   ', count (*) \
                        from products \
                        union all \
                        select 'geolocation', count (*) \
                        from geolocation) \
                  order by 1 \
                   """
        print(pd.read_sql_query(requete, connection))

def dropPostgreSQLebrasil():
    """
    Drop tables
    """
    import pandas as pd, os, sqlalchemy

    url = sqlalchemy.URL.create(
        drivername="postgresql+psycopg2",
        username="formation",
        password="formation",
        host="postgres-source",
        port=5432,
        database="ebrasil",
    )

    engine = sqlalchemy.create_engine(
        url,  # url = "postgresql://formation:formation@postgres-source:5432/formation"
        pool_pre_ping=True,
    )

    print("connecting with engine " + str(engine))

    with engine.connect() as connection:
        print(connection.execute(sqlalchemy.text("SELECT current_database(), current_user")).fetchone())

    with engine.connect() as connection:
        requete = """ \
                  select * \
                  from (select 'orders     ' table, count(*) enregistrements \
                        from orders \
                        union all \
                        select 'customers  ', count (*) \
                        from customers \
                        union all \
                        select 'sellers    ', count (*) \
                        from sellers \
                        union all \
                        select 'items      ', count (*) \
                        from items \
                        union all \
                        select 'payments   ', count (*) \
                        from payments \
                        union all \
                        select 'payments_p ', count (*) \
                        from payments_p \
                        union all \
                        select 'reviews    ', count (*) \
                        from reviews \
                        union all \
                        select 'reviews_p  ', count (*) \
                        from reviews_p \
                        union all \
                        select 'products   ', count (*) \
                        from products \
                        union all \
                        select 'geolocation', count (*) \
                        from geolocation) \
                  order by 1 \
                   """
        print(pd.read_sql_query(requete, connection))

    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table customers   cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table geolocation cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table items       cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table orders      cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table payments    cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table payments_p  cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table products    cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table reviews     cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table reviews_p   cascade"))
    with engine.begin() as connection: connection.execute(sqlalchemy.text("drop table sellers     cascade"))


if __name__ == "__main__":
    creationParquetEbrasil(rep_source='', rep_dest='')
