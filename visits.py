import sqlite3
from datetime import date, datetime, timedelta
from enum import Enum

class Slot(Enum):
    FIRST = '9-12'
    SECOND = '12-14'
    THIRD = '14-17'
    FOURTH = '17-20'

def get_visits_next_week(current_user):
    # TODO: run query
    return get_time_slots()




def get_time_slots():
    """
    Returns a list of dictionaries for all the time slots in the next 7 days

    :returns: a dict with the following structure: {date: string, slots: {date: string, time: string, available: boolean, pos: int}[]}
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
                'date': next_day,
                'time': slot.value,
                'available': True,
                'pos': j
            })

        next_seven_days.append(day_dict)

    return next_seven_days