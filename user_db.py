import sqlite3

def add_user(user):
    try:
        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = 'INSERT INTO PERSON(username, email, password, name, landlord) VALUES(?, ?, ?, ?, ?)'

        cursor.execute(sql, (user['username'], user['email'], user['password'], user['name'], True if user['client_type'] == 'landlord' else False))

        return True
    except Exception as e:
        print('ERROR', str(e))
        
        return False
    finally:
        cursor.close()
        conn.close()

def get_user(username):
    try:
        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = 'SELECT username, email, password, name, landlord FROM PERSON WHERE username = ?'

        cursor.execute(sql, (username,))
        user = cursor.fetchone()

        return user
    except Exception as e:
        print("ERROR", e)
        return None
    finally:
        cursor.close()
        conn.close()