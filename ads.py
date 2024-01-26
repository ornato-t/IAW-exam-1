import sqlite3

def get_public_ads():
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT A.adress, A.title, A.rooms, A.type, A.description, A.rent, A.furniture, P.name as landlord_name, P.username as landlord_username
        FROM ADVERTISEMENT A
        INNER JOIN PERSON P ON P.username = A.landlord_username
        WHERE A.available = TRUE;
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append(dict(row))

    return result