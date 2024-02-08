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

    advert['rooms'] = get_rooms(advert['rooms'])
    advert['furniture'] = get_furniture(advert['furniture'], advert['type'])
    advert['type'] = get_type(advert['type'])
    advert['rent_num'] = advert['rent']
    advert['rent'] = get_rent(advert['rent'])
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