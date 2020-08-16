import os
import datetime
import requests
import time
from w1thermsensor import W1ThermSensor

sensor = W1ThermSensor()

# Create an ordered list of start times with thermostat setpoint temperatures
schedule = [
    {
        "time": "5:00",
        "on": 75,
        "off": 73
    },
    {
        "time": "18:00",
        "on": 73,
        "off": 71
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

def get_current_range():
    '''
    Find out the on and off setpoint temperatures are for the current datetime
    '''
    now = datetime.datetime.now()
    schedule = build_ranges()
    current = schedule[0] #will check against this twice
    for entry in schedule:
        if current["dt"] <= now < entry["dt"]:
            print("found")
            return current
        current = entry

def begin_cool():
    print("turning on AC")
    requests.post(f"https://maker.ifttt.com/trigger/master_ac_on/with/key/{os.getenv('IFTTT_KEY')}")


def end_cool():
    print("turning off AC")
    requests.post(f"https://maker.ifttt.com/trigger/master_ac_off/with/key/{os.getenv('IFTTT_KEY')}")

def update():
    temp = sensor.get_temperature(W1ThermSensor.DEGREES_F)
    print("The temperature is %s f" % temp)
    r = get_current_range()
    print(f'on: {r["on"]}, off: {r["off"]}, starttime: {r["dt"].strftime("%Y/%m/%d %H:%M")}')
    if temp < r["off"]:
        end_cool()
    if temp > r["on"]:
        begin_cool()

while True:
    update()
    time.sleep(60)
