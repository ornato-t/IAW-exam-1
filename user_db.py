import sqlite3

def add_user(user):
    try:
        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = 'INSERT INTO PERSON(username, email, password, name, landlord) VALUES(?, ?, ?, ?, ?)'

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

def user_exists(username):
    """
    Checks whether a user exists in the database

    :returns: True if a username is contained in the database, False otherwise
    """
    try:
        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = 'SELECT 1 FROM PERSON WHERE username = ?'

        cursor.execute(sql, (username,))
        user = cursor.fetchone()

        if user is not None:
            return True
        else:
            return False
    except Exception as e:
        print("ERROR", e)
        return False
    finally:
        cursor.close()
        conn.close()