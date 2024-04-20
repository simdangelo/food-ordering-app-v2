import psycopg2

def create_postgres_connection():
    connection = psycopg2.connect(
        host='localhost',
        database='database',
        user='user',
        password='password',
        port=5432
    )
    cursor = connection.cursor()
    return connection, cursor
