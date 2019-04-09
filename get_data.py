import psycopg2

connection = psycopg2.connect(host='34.76.166.203', database='windy_db_8ae8878733ef6b9e', user='windy_user_8ae8878733ef6b9e', password='q')
cursor = connection.cursor()
cursor.execute('select * from regional_elspot;')
for query in cursor:
    print(str(query))
