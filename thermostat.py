import os
import datetime
import requests
import time
from w1thermsensor import W1ThermSensor

import logging
import logging.handlers
logger = logging.getLogger("thermostat")
logger.setLevel(logging.DEBUG)

#add console handler for logger
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

#add file handler for logger
fh = logging.FileHandler('log.csv')
logger.addHandler(fh)

sensor = W1ThermSensor()

# Create an ordered list of start times with thermostat setpoint temperatures
schedule = [
    {
        "time": "2:30",
        "on": 83,
        "off": 78
    },
    {
        "time": "4:30",
        "on": 83,
        "off": 78
    },
    {
        "time": "7:00",
        "on": 95,
        "off": 83
    },
    { #basically unmanaged time
        "time": "8:00",
        "on": 95,
        "off": 69
    },
    {
        "time": "18:00",
        "on": 82,
        "off": 77
    }
]

def date_from_time(time):
    '''
    Given a time, get a datetime object for today at that time
    '''
    date = datetime.date.today().strftime("%Y/%m/%d")
    dt = datetime.datetime.strptime(f"{date} {time}", "%Y/%m/%d %H:%M")
    return dt

def build_ranges():
    '''
    Use the schedule to create a set of ranges, from the last entry yesterday to
    the first entry tomorrow. This set of ranges can be used to determine which
    part of the schedule the current datetime is in
    '''
    yesterday = date_from_time(schedule[-1]["time"]) - datetime.timedelta(days=1)
    ranges = [
        {
            "dt": yesterday,
            "on": schedule[-1]["on"],
            "off": schedule[-1]["off"]
        }
    ]
    tomorrow = date_from_time(schedule[0]["time"]) + datetime.timedelta(days=1)
    for entry in schedule:
        ranges.append({
            "dt": date_from_time(entry["time"]),
            "on": entry["on"],
            "off": entry["off"]

        })
    ranges.append({
        "dt": tomorrow,
        "on": schedule[0]["on"],
        "off": schedule[0]["off"]
    })
    return ranges

def get_current_range(now):
    '''
    Find out the on and off setpoint temperatures are for the current datetime
    '''
    schedule = build_ranges()
    current = schedule[0] #will check against this twice
    for entry in schedule:
        if current["dt"] <= now < entry["dt"]:
            return current
        current = entry

def begin_cool():
    #print(f"https://maker.ifttt.com/trigger/master_ac_on/with/key/{os.getenv('IFTTT_KEY')}")
    requests.post(f"https://maker.ifttt.com/trigger/master_ac_on/with/key/{os.getenv('IFTTT_KEY')}")


def end_cool():
    #print(f"https://maker.ifttt.com/trigger/master_ac_off/with/key/{os.getenv('IFTTT_KEY')}")
    requests.post(f"https://maker.ifttt.com/trigger/master_ac_off/with/key/{os.getenv('IFTTT_KEY')}")

def update():
    temp = sensor.get_temperature(W1ThermSensor.DEGREES_F)
    now = datetime.datetime.now()
    r = get_current_range(now)
    if temp < r["off"]:
        action = "off"
        end_cool()
    elif temp > r["on"]:
        action = "on"
        begin_cool()
    else:
        action = "none"
    logger.debug(f'{now.strftime("%Y/%m/%d %H:%M")}, {temp}, {r["on"]}, {r["off"]}, {action}')

logger.debug(f'time,temp,on,off,action')
while True:
    update()
    time.sleep(30)
