import psycopg2


def connect():
    conn = psycopg2.connect(
        database="chat",
        user="postgres",
        password="test",
        host="127.0.0.1",
        port="5432"
    )
    conn = conn
    cur = conn.cursor()
    return conn, cur

conn, cur = connect()
cur.execute("""select * from msgs""")
rows = cur.fetchall()
print(rows)
