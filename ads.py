import sqlite3
import locale

def get_public_ads(sort_price):
    """
    Queries the database and returns a list of advertisements

    :param sort_price: whether the list should be sort by price (if false sorts by number of rooms)
    :returns: a list of all advertisements on the site, sorted according to the parameter
    """ 
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT A.id, A.adress, A.title, A.rooms, A.type, A.description, A.rent, A.furniture, P.name as landlord_name, P.username as landlord_username, PI.path as image
        FROM ADVERTISEMENT A
        INNER JOIN PERSON P ON P.username = A.landlord_username
        INNER JOIN PICTURES PI ON PI.ADVERTISEMENT_id = A.id
        WHERE A.available = TRUE
        GROUP BY A.id;
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        ad = dict(row)
        ad['rooms'] = get_rooms(ad['rooms'])
        ad['furniture'] = get_furniture(ad['furniture'], ad['type'])
        ad['type'] = get_type(ad['type'])
        ad['rent_num'] =ad['rent']
        ad['rent'] = get_rent(ad['rent'])

        result.append(ad)

    if sort_price:
        return sorted(result, key=lambda x: x['rent_num'], reverse=True)
    else:
        return sorted(result, key=lambda x: x['rooms'], reverse=False)

def get_ad_by_id(id):
    """
    Queries the database and returns a matching advertisement

    :param id: the id of the advertisement to be searched
    :returns: the advertisement
    """ 
    advert = get_ad_by_id_raw(id)

    if advert is None:
        return None

    advert['rooms'] = get_rooms(advert['rooms'])
    advert['furniture'] = get_furniture(advert['furniture'], advert['type'])
    advert['type'] = get_type(advert['type'])
    advert['rent_num'] = advert['rent']
    advert['rent'] = get_rent(advert['rent'])

    return advert

def get_ad_by_id_raw(id):
    """
    Queries the database and returns a matching advertisement. 
    Same as get_ad_by_id() but returns the data in the SQLite raw format, without any processing applied to it

    :returns: the advertisement or None
    """
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT A.id, A.adress, A.title, A.rooms, A.type, A.description, A.rent, A.furniture, A.available,
            P.name as landlord_name, P.username as landlord_username, 
            GROUP_CONCAT(PI.path) AS images
        FROM ADVERTISEMENT A
        INNER JOIN PERSON P ON P.username = A.landlord_username
        INNER JOIN PICTURES PI ON PI.ADVERTISEMENT_id = A.id
        WHERE A.id = ?
        LIMIT 1;
    """
    cursor.execute(sql, (id,))
    res = cursor.fetchone()

    cursor.close()
    conn.close()

    if res is None or res[0] is None:
        return None

    advert = dict(res)
    advert['images'] = advert['images'].split(',')

    return advert

def get_landlord_ads(username):
    """
    Queries the database and returns a list of advertisements belonging to a given landlord

    :returns: a list of all advertisements on the site
    """ 
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT A.id, A.adress, A.title, A.description, A.available,
            PI.path as image
        FROM ADVERTISEMENT A
        INNER JOIN PICTURES PI ON PI.ADVERTISEMENT_id = A.id
        WHERE A.landlord_username = ?
        GROUP BY A.id;
    """, (username,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        ad = dict(row)
        ad['available'] = ad['available'] == True

        result.append(ad)

    return result

def insert_ad(title, adress, description, rooms, rent, ad_type, furniture, available, pictures, landlord_username):
    """
    Inserts a new advertisement and its pictures into the database

    :returns: True if the insertion was succesful, False in case of errors
    """
    try:
        # Cast non string types
        rooms = int(rooms)
        rent = int(rent)
        furniture = furniture == 'true'
        available = available == 'true'

        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        sql = 'INSERT INTO ADVERTISEMENT(adress, title, rooms, type, description, rent, furniture, available, landlord_username) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)'

        cursor.execute(sql, (adress, title, rooms, ad_type, description, rent, furniture, available, landlord_username))
        id = cursor.lastrowid   # ID of the inserted advertisement

        pictures = [(picture_path, id) for picture_path in pictures]    # Map list of paths to list of tuples
        sql_picture = 'INSERT INTO PICTURES(path, ADVERTISEMENT_id) VALUES(?, ?)'
        cursor.executemany(sql_picture, pictures)   # This is ran as a signle INSERT statement

        conn.commit()
        return True
    except Exception as e:
        print('ERROR', str(e))
        conn.rollback()
        
        return False
    finally:
        cursor.close()
        conn.close()

def edit_ad(title, description, rooms, rent, ad_type, furniture, available, pictures, landlord_username, advertisement_id):
    """
    Edits an existing advertisement. If any pictures were provided it deletes the existing ones and replaces them with the new ones

    :returns: True if the edit was succesful, False in case of errors
    """
    try:
        # Cast non string types
        rooms = int(rooms)
        rent = float(rent)
        furniture = furniture == 'true'
        available = available == 'true'

        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        sql = """
            UPDATE ADVERTISEMENT
            SET title = ?, rooms = ?, type = ?, description = ?, rent = ?, furniture = ?, available = ?
            WHERE id = ? AND landlord_username = ?
        """

        cursor.execute(sql, (title, rooms, ad_type, description, rent, furniture, available, advertisement_id, landlord_username))

        # Update pictures
        if len(pictures) > 0:
            # Delete previously saved pictures
            sql_delete = 'DELETE FROM PICTURES WHERE ADVERTISEMENT_id = ?'
            cursor.execute(sql_delete, (advertisement_id,))

            # Insert new pictures
            pictures = [(picture_path, advertisement_id) for picture_path in pictures]    # Map list of paths to list of tuples
            sql_insert = 'INSERT INTO PICTURES(path, ADVERTISEMENT_id) VALUES(?, ?)'
            cursor.executemany(sql_insert, pictures)   # This is ran as a signle INSERT statement

        conn.commit()
        return True
    except Exception as e:
        print('ERROR', str(e))
        conn.rollback()
        
        return False
    finally:
        cursor.close()
        conn.close()

def get_ad_images(advertisement_id):
    """
    Fetches a list of image paths from the database
    """
    try:
        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = """
            SELECT GROUP_CONCAT(path) AS images
            FROM PICTURES
            WHERE ADVERTISEMENT_id = ?
        """
        cursor.execute(sql, (advertisement_id,))
        res = cursor.fetchone()

        if res is None or res[0] is None:
            return []

        advert = dict(res)
        return advert['images'].split(',')
    except Exception as e:
        print("ERROR", str(e))
        return []
    finally:
        cursor.close()
        conn.close()

def get_ad_landlord(advertisement_id):
    """
    Fetches the username of the landlord of a given advertisement

    :returns: the landlord's username
    """
    try:
        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = """
            SELECT landlord_username
            FROM ADVERTISEMENT
            WHERE id = ?
            LIMIT 1;
        """
        cursor.execute(sql, (advertisement_id,))
        res = cursor.fetchone()

        if res is None or res[0] is None:
            return None

        advert = dict(res)
        return advert['landlord_username']
    except Exception as e:
        print("ERROR", str(e))
        return None
    finally:
        cursor.close()
        conn.close()

# HELPER FUNCTIONS

def get_rooms(num):
    """
    Pretty prints the number of rooms in a house. Returns '5+' if the house has more than 5 rooms

    :param num: the number of rooms
    :returns: a string representation of the number of rooms
    """ 

    if num > 5:
        return '5+'
    else:
        return str(num)

def get_type(house_type):
    """
    Translates the "type" DB row format into plain Italian

    :param house_type: house type in the DB format
    :returns: a string representation of the house type
    """

    match house_type:
        case 'detached':
            return 'Casa indipendente'
        case 'flat':
            return 'Appartamento'
        case 'loft':
            return 'Loft'
        case 'villa':
            return 'Villa'
        case _: # Default case if no other cases are matched, this should never happen
            return house_type

def get_furniture(furniture, house_type):
    """
    :param furniture: furniture boolean attribute, from the DB
    :param house_type: the type of house in the DB format
    :returns: a string representation of the furniture status
    """

    result = ''

    if furniture == False:
        result = 'non'
    
    if house_type == 'detached' or house_type == 'villa':
        result += ' arredata'
    else:
        result += ' arredato'

    return result

def get_rent(num):
    """
    :param num: rent attribute, from the DB
    :returns: a string representation of the rent parameter with the Italian number formatting (point as a thousand separator, comma as a decimal separator)
    """
    
    locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
    return locale.format("%.2f", num, grouping=True)