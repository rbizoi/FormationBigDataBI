def creationParquetEbrasil(rep_source, rep_dest):
    """
        Création des fichiers parquet à partir des fichiers .csv du répertoire « data/ebrasil »
        rep_source : répertoire source qui doit contenir imperativement les 9 fichiers csv
                                olist_customers_dataset.csv
                                olist_order_items_dataset.csv
                                olist_order_reviews_dataset.csv
                                olist_products_dataset.csv
                                product_category_name_translation.csv
                                olist_geolocation_dataset.csv
                                olist_order_payments_dataset.csv
                                olist_orders_dataset.csv
                                olist_sellers_dataset.csv
        rep_dest : répertoire destination, s’il n’existe pas il est crée
    """
    import pandas as pd, os

    def controleFichier(fichier=''):
        if not (os.path.exists(fichier) & (not os.path.isdir(fichier))):
            raise Exception(f"Le fichier {fichier} n’existe pas !!!")
        print(f"{'-' * 50}\nfichier existent\t:\t{fichier}\n{'-' * 50}")
        # if fichier[-8:] == '.parquet' : print(fichier, pd.read_parquet(fichier).info())
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

if __name__ == "__main__":
    creationParquetEbrasil(rep_source='', rep_dest='')
