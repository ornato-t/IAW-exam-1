import sqlite3

def add_user(user):
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'INSERT INTO PERSON(username, email, password, name, landlord) VALUES(?, ?, ?, ?, ?)'

    try:
        cursor.execute(sql, (user['username'], user['email'], user['password'], user['name'], True if user['client_type'] == 'landlord' else False))
        conn.commit()

        return True
    except Exception as e:
        print('ERROR', str(e))
        conn.rollback()
        
        return False
    finally:
        cursor.close()
        conn.close()