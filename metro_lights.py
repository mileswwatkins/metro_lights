from pprint import pprint

import requests

from config import api_key


# Get the data from WMATA
SERVICE_URL = 'https://api.wmata.com/StationPrediction.svc/json/GetPrediction/All'
data = requests.get(SERVICE_URL, headers={'api_key': api_key}).json()

pprint(data)

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
    clean_trains.append(train)

pprint(clean_trains)
