import sqlite3

def get_public_ads():
    """
    Queries the database and returns a list of advertisements

    :returns: a list of all advertisements on the site
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
        ad['rent'] = get_rent(ad['rent'])
        print(ad)
        result.append(ad)

    return result

def get_rooms(num):
    """
    Pretty prints the number of rooms in a house. Returns '5+' if the house has more than 5 rooms

    :param num: the number of rooms
    :returns: a string representation of the number of rooms
    """ 

    if num > 5:
        return '5+'
    else:
        return num

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

    return result.capitalize()

def get_rent(num):
    """
    :param num: rent attribute, from the DB
    :returns: a string representation of the rent parameter, truncated to two decimal positions and with a comma as a separator
    """

    return f'{num:.2f}'.replace('.', ',')