"""  A module to query Transport NSW (Australia) departure times.         """
"""  First created by Dav0815 ( https://pypi.org/user/Dav0815/)           """
"""  Extended by AndyStewart999 ( https://pypi.org/user/andystewart999/ ) """

from datetime import datetime, timedelta
from google.transit import gtfs_realtime_pb2
import requests.exceptions
import requests
import logging
import re

ATTR_DUE = 'due'

ATTR_ORIGIN_STOP_ID = 'origin_stop_id'
ATTR_ORIGIN_NAME = 'origin_name'
ATTR_ORIGIN_DETAIL = 'origin_detail'
ATTR_DEPARTURE_TIME = 'departure_time'

ATTR_DESTINATION_STOP_ID = 'destination_stop_id'
ATTR_DESTINATION_NAME = 'destination_name'
ATTR_DESTINATION_DETAIL = 'destination_detail'
ATTR_ARRIVAL_TIME = 'arrival_time'

ATTR_TRANSPORT_TYPE = 'transport_type'
ATTR_TRANSPORT_NAME = 'transport_name'
ATTR_LINE_NAME = 'line_name'
ATTR_LINE_NAME_SHORT = 'line_name_short'

ATTR_OCCUPANCY = 'occupancy'

ATTR_REAL_TIME_TRIP_ID = 'real_time_trip_id'
ATTR_LATITUDE = 'latitude'
ATTR_LONGITUDE = 'longitude'

logger = logging.getLogger(__name__)

class TransportNSW(object):
    """The Class for handling the data retrieval."""

    # The application requires an API key. You can register for
    # free on the service NSW website for it.
    # You need to register for both the Trip Planner and Realtime Vehicle Position APIs

    def __init__(self):
        """Initialize the data object with default values."""
        self.origin_id = None
        self.destination_id = None
        self.api_key = None
        self.trip_wait_time = None
        self.info = {
            ATTR_DUE : 'n/a',
            ATTR_ORIGIN_STOP_ID : 'n/a',
            ATTR_ORIGIN_NAME : 'n/a',
            ATTR_ORIGIN_DETAIL : 'n/a',
            ATTR_DEPARTURE_TIME : 'n/a',
            ATTR_DESTINATION_STOP_ID : 'n/a',
            ATTR_DESTINATION_NAME : 'n/a',
            ATTR_DESTINATION_DETAIL : 'n/a',
            ATTR_ARRIVAL_TIME : 'n/a',
            ATTR_TRANSPORT_TYPE : 'n/a',
            ATTR_TRANSPORT_NAME : 'n/a',
            ATTR_LINE_NAME : 'n/a',
            ATTR_LINE_NAME_SHORT : 'n/a',
            ATTR_OCCUPANCY : 'n/a',
            ATTR_REAL_TIME_TRIP_ID : 'n/a',
            ATTR_LATITUDE : 'n/a',
            ATTR_LONGITUDE : 'n/a'
            }

    def get_trip(self, name_origin, name_destination , api_key, trip_wait_time = 0):
        """Get the latest data from Transport NSW."""
        fmt = '%Y-%m-%dT%H:%M:%SZ'

        self.name_origin = name_origin
        self.destination = name_destination
        self.api_key = api_key
        self.trip_wait_time = trip_wait_time

        # This query always uses the current date and time - but add in any 'trip_wait_time' minutes
        now_plus_wait = datetime.now() + timedelta(minutes = trip_wait_time)
        itdDate = now_plus_wait.strftime('%Y%m%d')
        itdTime = now_plus_wait.strftime('%H%M')

        # Build the URL
        url = \
            'https://api.transport.nsw.gov.au/v1/tp/trip?' \
            'outputFormat=rapidJSON&coordOutputFormat=EPSG%3A4326' \
            '&depArrMacro=dep&itdDate=' + itdDate + '&itdTime=' + itdTime + \
            '&type_origin=any&name_origin=' + name_origin + \
            '&type_destination=any&name_destination=' + name_destination + \
            '&calcNumerOfTrips=1&TfNSWDM=true&version=10.2.1.42'
        auth = 'apikey ' + self.api_key
        header = {'Accept': 'application/json', 'Authorization': auth}

        # Send the query and return an error if something goes wrong
        # Otherwise store the response
        try:
            response = requests.get(url, headers=header, timeout=10)
        except:
            logger.warning("Network or Timeout error")
            return self.info

        # If there is no valid request (e.g. http code isn't 200)
        # log error and return empty object
        if response.status_code != 200:
            logger.warning("Error with the request sent; check api key")
            return self.info

        # Parse the result as a JSON object
        result = response.json()

        # The API will always return a valid trip, so it's just a case of grabbing what we need...
        origin = result['journeys'][0]['legs'][0]['origin']
        destination = result['journeys'][0]['legs'][0]['destination']
        transportation = result['journeys'][0]['legs'][0]['transportation']

        # Origin info
        origin_stop_id = origin['id']
        origin_name_temp = origin['name']
        origin_name = origin_name_temp.split(', ')[1]
        origin_detail = origin_name_temp.split(', ')[2]
        origin_departure_time = origin['departureTimeEstimated']

	# How long until it leaves?
        due = self.get_due(datetime.strptime(origin_departure_time, fmt))

        # Destination info
        destination_stop_id = destination['id']
        destination_name_temp = destination['name']
        destination_name = destination_name_temp.split(', ')[1]
        destination_detail = destination_name_temp.split(', ')[2]
        destination_arrival_time = destination['arrivalTimeEstimated']

        # Trip type info - train, bus, etc
        mode_temp = transportation['product']['class']
        mode = self.get_mode(mode_temp)
        mode_name = transportation['product']['name']

        # RealTimeTripID info so we can try and get the current location
        realtimetripid = transportation['properties']['RealtimeTripId']

        # Line info
        line_name_short = transportation['disassembledName']
        line_name = transportation['number']

        # Occupancy info, if it's there
        occupancy = 'UNKNOWN'
        if 'properties' in destination:
            if 'occupancy' in destination['properties']:
                occupancy = destination['properties']['occupancy']

        # Now might be a good time to see if we can also find the latitude and longitude
        # Using the Realtime Vehicle Positions API
        latitude = 'n/a'
	longitued = 'n/a'

        # Build the URL
        url = \
            'https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos' \
             + self.get_url(mode)
        auth = 'apikey ' + self.api_key
        header = {'Authorization': auth}

        response = requests.get(url, headers=header, timeout=10)

        # Only try and process the results if we got a good return code
        if response.status_code == 200:
            # Search the feed and see if we can find the trip_id
            # If we do, capture the latitude and longitude

            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)

            # Unfortunately we need to do some mucking about for train-based trip_ids
            # Define the appropriate regular expression to search for - usually just the full text
            bFindLocation = True

            if mode == 'Train':
                triparray = realtimetripid.split('.')
                if len(triparray) == 7:
                    trip_id_wild = triparray[0] + '.' + triparray[1] + '.' + triparray[2] + '.+.' + triparray[4] + '.' + triparray[5] + '.' + triparray[6]
                else:
                    # Hmm, it's not the right length (this happens rarely) - give up
                    bFindLocation = False
            else:
                trip_id_wild = realtimetripid

            if bFindLocation:
                reg = re.compile(trip_id_wild)

                for entity in feed.entity:
                    if bool(re.match(reg, entity.vehicle.trip.trip_id)):
                        latitude = entity.vehicle.position.latitude
                        longitude = entity.vehicle.position.longitude
                        # We found it, so break out
                        break

        self.info = {
            ATTR_DUE: due,
            ATTR_ORIGIN_STOP_ID : origin_stop_id,
            ATTR_ORIGIN_NAME : origin_name,
            ATTR_ORIGIN_DETAIL : origin_detail,
            ATTR_DEPARTURE_TIME : origin_departure_time,
            ATTR_DESTINATION_STOP_ID : destination_stop_id,
            ATTR_DESTINATION_NAME : destination_name,
            ATTR_DESTINATION_DETAIL : destination_detail,
            ATTR_ARRIVAL_TIME : destination_arrival_time,
            ATTR_TRANSPORT_TYPE : mode,
            ATTR_TRANSPORT_NAME: mode_name,
            ATTR_LINE_NAME : line_name,
            ATTR_LINE_NAME_SHORT : line_name_short,
            ATTR_OCCUPANCY : occupancy,
            ATTR_REAL_TIME_TRIP_ID : realtimetripid,
            ATTR_LATITUDE : latitude,
            ATTR_LONGITUDE : longitude
            }
        return self.info

    def get_mode(self, iconId):
        """Map the iconId to a full text string"""
        modes = {
            1: "Train",
            4: "Lightrail",
            5: "Bus",
            7: "Coach",
            9: "Ferry",
            11: "Schoolbus"
        }
        return modes.get(iconId, None)

    def get_url(self, mode):
        """Map the journey mode to the proper real time location URL """
	
        url_options = {
            "Train"     : "/sydneytrains",
            "Lightrail" : "/lightrail/innerwest",
            "Bus"       : "/buses",
            "Coach"     : "/buses",
            "Ferry"     : "/ferries/sydneyferries",
            "Schoolbus" : "/buses"
        }
        return url_options.get(mode, None)

    def get_due(self, estimated):
        """Min until departure"""
        due = 0
        due = round((estimated - datetime.utcnow()).seconds / 60)
        return due

    def utc_to_local(self, utc_dt):
        """ Convert UTC time to local time """
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
