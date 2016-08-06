from pprint import pprint
import json

import requests

from config import api_key


# STATIONS_URL = 'https://api.wmata.com/Rail.svc/json/jLines'
ROUTES_URL = 'https://api.wmata.com/TrainPositions/StandardRoutes?contentType=json'
POSITIONS_URL = 'https://api.wmata.com/TrainPositions/TrainPositions?contentType=json'
HEADERS = {'api_key': api_key}

# stations = json.loads(requests.get(STATIONS_URL, headers=HEADERS).text)

routes = json.loads(requests.get(ROUTES_URL, headers=HEADERS).text)['StandardRoutes']

positions = json.loads(requests.get(POSITIONS_URL, headers=HEADERS).text)['TrainPositions']
positions = [
    p for p in positions if
    p['ServiceType'] in ('Normal', 'Special') and
    p['CarCount'] != 0 and
    p['DestinationStationCode'] is not None
]

for train in positions:
    previous_station_circuit = None
    current_circuit = None
    next_station_circuit = None
    destination_is_behind = False

    for route in [r for r in routes if r['LineCode'] == train['LineCode']]:
        for circuit in route['TrackCircuits']:
            # If solution has already been found going the other direction, skip this direction
            if previous_station_circuit and next_station_circuit:
                break

            if circuit['StationCode'] == train['DestinationStationCode']:
                destination_is_behind = True
            if circuit['CircuitId'] == train['CircuitId']:
                current_circuit = circuit
            if circuit['StationCode'] is not None:
                if current_circuit is None:
                    previous_station_circuit = circuit
                else:
                    next_station_circuit = circuit
                    break

    if previous_station_circuit is None or next_station_circuit is None:
        continue
    if destination_is_behind:
        (previous_station_circuit, next_station_circuit) = (next_station_circuit, previous_station_circuit)

    # print('previous', previous_station_circuit)
    # print('current', current_circuit)
    # print('next', next_station_circuit)

    progress = (
        float(current_circuit['SeqNum'] - previous_station_circuit['SeqNum']) /
        float(next_station_circuit['SeqNum'] - previous_station_circuit['SeqNum'])
    )
    print(
        "{LineCode} Line train {TrainId} is {progress_pct}% of the way from {previous_station} to {next_station}".format(**{
            'LineCode': train['LineCode'],
            'TrainId': train['TrainId'],
            'progress_pct': int(progress * 100),
            'previous_station': previous_station_circuit['StationCode'],
            'next_station': next_station_circuit['StationCode']
    }))
