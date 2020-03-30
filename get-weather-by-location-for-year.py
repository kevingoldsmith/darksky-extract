from darksky.api import DarkSky
from darksky.types import languages, units, weather
import configparser
import os
import argparse
import json
import configparser
import datetime
import copy

CONFIG_FILE = 'config.ini'
DATA_DIR = 'data'

def convert_dict_datetimes_to_iso(dict_to_convert):
    for dict_item in dict_to_convert.items():
        if isinstance(dict_item[1], datetime.datetime):
            dict_to_convert[dict_item[0]] = dict_item[1].isoformat()
    return dict_to_convert


def convert_forecast_to_json(forecast):
    return_val = {'latitude': forecast.latitude, 'longitude': forecast.longitude, 'hour_offset': forecast.offset, 'timezone': forecast.timezone }
    return_val['alerts'] = []
    for alert_item in forecast.alerts:
        return_val['alerts'].append(convert_dict_datetimes_to_iso(alert_item.__dict__.copy()))
    return_val['currently'] = convert_dict_datetimes_to_iso(forecast.currently.__dict__.copy())
    return_val['daily'] = []
    for daily_data in forecast.daily.data:
        return_val['daily'].append(convert_dict_datetimes_to_iso(daily_data.__dict__.copy()))
    return_val['flags'] = copy.deepcopy(forecast.flags.__dict__)
    return_val['hourly'] = []
    for hourly_data in forecast.hourly.data:
        return_val['hourly'].append(convert_dict_datetimes_to_iso(hourly_data.__dict__.copy()))
    return_val['minutely'] = []
    for minute_data in forecast.minutely.data:
        return_val['minutely'].append(convert_dict_datetimes_to_iso(minute_data.__dict__.copy()))
    
    return return_val


parser = argparse.ArgumentParser()
parser.add_argument("year", help="the year you want to create locations for", type=int)
args = parser.parse_args()
year = args.year

config_parser = configparser.ConfigParser()
config_parser.read(CONFIG_FILE)
secret_key = config_parser.get('Darksky API', 'secret_key')
foursquare_data_dir = config_parser.get('paths', 'locations_data_dir')

darksky = DarkSky(secret_key)

if not os.path.exists(foursquare_data_dir):
    print('ERROR: Location file path is incorrect: {}'.format(foursquare_data_dir))
    exit(1)

location_file = os.path.join(foursquare_data_dir, 'locations_{0}.json'.format(year))
if not os.path.exists(location_file):
    print('ERROR: Location file path is incorrect: {}'.format(location_file))
    exit(1)

locations_by_day = {}
weather_by_day = {}
with open(location_file, 'r') as f:
    locations_by_day = json.load(f)

for day in sorted(locations_by_day.keys()):
    locations_list = locations_by_day[day]
    for location in locations_list:
        timestamp = datetime.datetime.fromisoformat(location['timestamp'])
        latitiude = location['latitude']
        longitude = location['longitude']
        forecast = darksky.get_time_machine_forecast(latitiude, longitude, extend=False, lang=languages.ENGLISH, values_units=units.US, exclude=[weather.MINUTELY], timezone='UTC', time=timestamp)
        if not day in weather_by_day:
            weather_by_day[day] = []
        weather_by_day[day].append(convert_forecast_to_json(forecast))

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

with open(os.path.join(DATA_DIR, 'weather_{}.json'.format(year)), 'w') as f:
    f.write(json.dumps(weather_by_day, indent=2))
