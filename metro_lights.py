from pprint import pprint

import requests

from config import api_key


LINE_INFO_URL = 'https://api.wmata.com/Rail.svc/json/jLines'
STATION_LIST_URL = 'https://api.wmata.com/Rail.svc/json/jPath'
STATION_TO_STATION_URL = 'https://api.wmata.com/Rail.svc/json/jSrcStationToDstStationInfo'
REAL_TIME_URL = 'https://api.wmata.com/StationPrediction.svc/json/GetPrediction/All'

# Get metadata on each line
data = requests.get(LINE_INFO_URL, headers={'api_key': api_key}).json()
lines = {x['LineCode'] : x for x in data['Lines']}

for (line, line_info) in lines.iteritems():
    # Get every station on the line
    station_list_query_string = {
        'FromStationCode': line_info['StartStationCode'],
        'ToStationCode': line_info['EndStationCode']
    }
    data = requests.get(
        STATION_LIST_URL,
        params=station_list_query_string,
        headers={'api_key': api_key}
    ).json()
    lines[line]['Route'] = data['Path']

    # Get scheduled time between each station
    for station_num in range(1, len(lines[line]['Route'])):
        station_to_station_query_string = {
            'FromStationCode': lines[line]['Route'][station_num - 1]['StationCode'],
            'ToStationCode': lines[line]['Route'][station_num]['StationCode']
        }
        data = requests.get(
            STATION_TO_STATION_URL,
            params=station_to_station_query_string,
            headers={'api_key': api_key}
        ).json()
        lines[line]['Route'][station_num]['TimeToPrev'] = data['StationToStationInfos'][0]['RailTime']
    lines[line]['Route'][0]['TimeToPrev'] = 0
    for station in lines[line]['Route']:
        del station['LineCode']
        del station['SeqNum']
        # Interesting information, but probably not necessary for this project
        del station['DistanceToPrev']

    lines[line]['EndStationCodes'] = [
        x for x in [
            lines[line].pop('EndStationCode'),
            lines[line].pop('InternalDestination1'),
            lines[line].pop('InternalDestination2')
        ] if x
    ]
    del lines[line]['LineCode']

# pprint(lines)

# Get the real-time data from WMATA
data = requests.get(REAL_TIME_URL, headers={'api_key': api_key}).json()

# Clean the data, filter out bad information
BAD_DESTINATION_CODES = (None, )
BAD_MIN_CODES = ('---', )
ZERO_MINUTE_CODES = ('ARR', 'BRD')

trains = data['Trains']
clean_trains = []
for train in trains:
    if train['DestinationCode'] in BAD_DESTINATION_CODES or \
            train['Min'] in BAD_MIN_CODES:
        continue
    if train['Min'] in ZERO_MINUTE_CODES:
        train['Min'] = '0'
    train['Min'] = int(train['Min'])

    # Ignore trains in waiting at terminus stations
    if train['Car'] is None:
        continue
    # I believe that "2-car" trains are 7000-series cars
    train['Car'] = int(train['Car'])

    clean_trains.append(train)

# pprint(clean_trains)

for train in clean_trains:
    line = lines[train['Line']]

    # For now, skip trains that are going in the opposite direction
    if train['DestinationCode'] not in line['EndStationCodes']:
        continue

    (station_info, ) = [x for x in line['Route'] if x['StationCode'] == train['LocationCode']]
    percentage_of_way_to_station = float(train['Min']) / float(station_info['TimeToPrev'])

    print('---')
    print(train)
    print(station_info)
    print(percentage_of_way_to_station)
