import sqlite3
from datetime import date, datetime, timedelta
from enum import Enum

class Slot(Enum):
    FIRST = '9-12'
    SECOND = '12-14'
    THIRD = '14-17'
    FOURTH = '17-20'

def get_visits_next_week(advertisement_id):
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
        date_obj = datetime.strptime(ad['date'], '%Y-%m-%d')
        ad['date'] = date_obj.strftime('%d/%m/%Y')

        for day in slots:
            if day['date'] == ad['date']:
                for slot in day['slots']:
                    if slot['pos'] == ad['time']:
                        slot['available'] = False

    return slots



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