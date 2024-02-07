import sqlite3
from datetime import date, datetime, timedelta
from enum import Enum

import ads

class Slot(Enum):
    FIRST = '9-12'
    SECOND = '12-14'
    THIRD = '14-17'
    FOURTH = '17-20'

    @staticmethod
    def parse(num):
        match num:
            case 0:
                return Slot.FIRST.value
            case 1:
                return Slot.SECOND.value
            case 2:
                return Slot.THIRD.value
            case 3:
                return Slot.FOURTH.value
            case 4:
                raise Exception('Unexpected time slot formatting')

def get_visits_next_week(advertisement_id):
    """
    Fetches the list of accepted visits scheduled for a certain property in the next week

    :returns: A list of time slots containing the available time slots (unavailable slots have already scheduled visits)
    """
    slots = get_time_slots()

    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT date, time
        FROM VISIT V
        WHERE ADVERTISEMENT_id = ? AND status = 'accepted'
    """
    cursor.execute(sql, (advertisement_id,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    for row in rows:
        ad = dict(row)
        date_obj = datetime.strptime(ad['date'], '%Y-%m-%d %H:%M:%S')
        ad['date'] = date_obj.strftime('%d/%m/%Y')

        for day in slots:
            if day['date'] == ad['date']:
                for slot in day['slots']:
                    if slot['pos'] == ad['time']:
                        slot['available'] = False

    return slots

def has_user_visited(username, advertisement_id):
    """
    Checks if a user has already visited a house

    :returns: True if the user has already visited the house, False otherwise
    """
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT COUNT (*) as visits
        FROM VISIT
        WHERE ADVERTISEMENT_id = ? AND visitor_username = ? AND status = 'accepted';
    """
    cursor.execute(sql, (advertisement_id, username))
    res = cursor.fetchone()

    cursor.close()
    conn.close()

    res = dict(res)
    if res['visits'] > 0:
        return True

    return False

def is_user_waiting_visit(username, advertisement_id):
    """
    Checks if a user has booked a house and is awaiting a confirmation

    :returns: True if the user has has a pending visit, False otherwise
    """
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT COUNT (*) as visits
        FROM VISIT
        WHERE ADVERTISEMENT_id = ? AND visitor_username = ? AND status = 'pending';
    """
    cursor.execute(sql, (advertisement_id, username))
    res = cursor.fetchone()

    cursor.close()
    conn.close()

    res = dict(res)
    if res['visits'] > 0:
        return True

    return False

def insert_visit(username, advertisement_id, date, time, virtual):
    try:
        conn = sqlite3.connect('database/database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = 'INSERT INTO VISIT(date, time, visitor_username, ADVERTISEMENT_id, virtual, status) VALUES(?, ?, ?, ?, ?, ?)'

        cursor.execute(sql, (date, time, username, advertisement_id, virtual, 'pending'))
        conn.commit()

        return True
    except Exception as e:
        print('ERROR', str(e))
        conn.rollback()
        
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_visits(username):
    """
    Fetches the list of visits booked by a user and basic information on the relevant properties

    :returns: A list of visit reservations
    """
    slots = get_time_slots()

    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT V.date, V.time, V.virtual, V.status, V.refusal_reason, 
            A.title as ad_title, A.adress as ad_adress, A.type as ad_type, A.furniture as ad_furniture, A.rooms as ad_rooms, 
            P.path AS ad_image,
			PE.name as landlord_name
        FROM VISIT V
        INNER JOIN ADVERTISEMENT A ON A.id = V.ADVERTISEMENT_id
        INNER JOIN PICTURES P ON P.ADVERTISEMENT_id = A.id
		INNER JOIN PERSON PE ON A.landlord_username = PE.username
        WHERE V.visitor_username = ?
        GROUP BY A.ID;
    """
    cursor.execute(sql, (username,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    results = []
    for row in rows:
        res = dict(row)
        date_obj = datetime.strptime(res['date'], '%Y-%m-%d %H:%M:%S')
        res['date'] = date_obj.strftime('%d/%m/%Y')
        res['time'] = Slot.parse(res['time'])
        res['virtual'] = res['virtual'] == True
        res['ad_rooms'] = ads.get_rooms(res['ad_rooms'])
        res['ad_furniture'] = ads.get_furniture(res['ad_furniture'], res['ad_type'])
        res['ad_type'] = ads.get_type(res['ad_type'])

        results.append(res)
    
    return results

def get_landlord_visits(username):
    """
    Fetches the list of visits booked to all properties belonging to a landlord and basic information on the relevant properties

    :returns: A list of visit reservations
    """
    slots = get_time_slots()

    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = """
        SELECT V.date, V.time, V.virtual, V.status, V.refusal_reason, 
            A.title as ad_title, A.adress as ad_adress, A.type as ad_type, A.furniture as ad_furniture, A.rooms as ad_rooms, 
            P.path AS ad_image,
			PE.name as user_name
        FROM VISIT V
        INNER JOIN ADVERTISEMENT A ON A.id = V.ADVERTISEMENT_id
        INNER JOIN PICTURES P ON P.ADVERTISEMENT_id = A.id
		INNER JOIN PERSON PE ON V.visitor_username = PE.username
        WHERE A.landlord_username = ?
        GROUP BY A.ID;
    """
    cursor.execute(sql, (username,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    results = []
    for row in rows:
        res = dict(row)
        date_obj = datetime.strptime(res['date'], '%Y-%m-%d %H:%M:%S')
        res['date'] = date_obj.strftime('%d/%m/%Y')
        res['time'] = Slot.parse(res['time'])
        res['virtual'] = res['virtual'] == True
        res['ad_rooms'] = ads.get_rooms(res['ad_rooms'])
        res['ad_furniture'] = ads.get_furniture(res['ad_furniture'], res['ad_type'])
        res['ad_type'] = ads.get_type(res['ad_type'])

        results.append(res)
    
    return results
# HELPER FUNCTIONS

def get_time_slots():
    """
    Returns a list of dictionaries for all the time slots in the next 7 days

    :returns: a dict with the following structure: {date: string, slots: {time: string, available: boolean, pos: int}[]}
    """ 
    tomorrow = date.today() + timedelta(days=1)

    next_seven_days = []
    for i in range(7):
        next_day = tomorrow + timedelta(days=i)
        next_day = next_day.strftime('%d/%m/%Y')

        day_dict = {
            'date': next_day,
            'slots': []
        }

        for j, slot in enumerate(Slot, start=0):
            day_dict['slots'].append({
                'time': slot.value,
                'available': True,
                'pos': j
            })

        next_seven_days.append(day_dict)

    return next_seven_days