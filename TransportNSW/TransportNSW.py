"""  A module to query Transport NSW (Australia) departure times.         """
"""  First created by Dav0815 ( https://pypi.org/user/Dav0815/)           """
"""  Extended by AndyStewart999 ( https://pypi.org/user/andystewart999/ ) """

from datetime import datetime, timedelta
from google.transit import gtfs_realtime_pb2
import requests.exceptions
import requests
import logging
import re

ATTR_DUE_IN = 'due'

ATTR_ORIGIN_STOP_ID = 'origin_stop_id'
ATTR_ORIGIN_NAME = 'origin_name'
ATTR_DEPARTURE_TIME = 'departure_time'

ATTR_DESTINATION_STOP_ID = 'destination_stop_id'
ATTR_DESTINATION_NAME = 'destination_name'
ATTR_ARRIVAL_TIME = 'arrival_time'

ATTR_ORIGIN_TRANSPORT_TYPE = 'origin_transport_type'
ATTR_ORIGIN_TRANSPORT_NAME = 'origin_transport_name'
ATTR_ORIGIN_LINE_NAME = 'origin_line_name'
ATTR_ORIGIN_LINE_NAME_SHORT = 'origin_line_name_short'
ATTR_CHANGES = 'changes'

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
            ATTR_DUE_IN : 'n/a',
            ATTR_ORIGIN_STOP_ID : 'n/a',
            ATTR_ORIGIN_NAME : 'n/a',
            ATTR_DEPARTURE_TIME : 'n/a',
            ATTR_DESTINATION_STOP_ID : 'n/a',
            ATTR_DESTINATION_NAME : 'n/a',
            ATTR_ARRIVAL_TIME : 'n/a',
            ATTR_ORIGIN_TRANSPORT_TYPE : 'n/a',
            ATTR_ORIGIN_TRANSPORT_NAME : 'n/a',
            ATTR_ORIGIN_LINE_NAME : 'n/a',
            ATTR_ORIGIN_LINE_NAME_SHORT : 'n/a',
            ATTR_CHANGES : 'n/a',
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

        # Build the entire URL
        url = \
            'https://api.transport.nsw.gov.au/v1/tp/trip?' \
            'outputFormat=rapidJSON&coordOutputFormat=EPSG%3A4326' \
            '&depArrMacro=dep&itdDate=' + itdDate + '&itdTime=' + itdTime + \
            '&type_origin=any&name_origin=' + name_origin + \
            '&type_destination=any&name_destination=' + name_destination + \
            '&calcNumberOfTrips=1&TfNSWDM=true&version=10.2.1.42'
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
        #print (result)

        # The API will always return a valid trip, so it's just a case of grabbing what we need...
        # We're only reporting on the origin and destination, it's out of scope to discuss the specifics of the ENTIRE journey
        # This isn't a route planner, just a 'how long until the next journey I've specified' tool
        # The assumption is that the travelee will know HOW to make the defined journey, they're just asking WHEN it's happening next

        legs = result['journeys'][0]['legs']
        first_leg = self.find_first_leg(legs)
        last_leg = self.find_last_leg(legs)
        changes = self.find_changes(legs)

        print (first_leg)
        print (last_leg)
        print (changes)

        origin = result['journeys'][0]['legs'][first_leg]['origin']
        # probably tidy this up when we start to get occupancy data back
        first_destination = result['journeys'][0]['legs'][first_leg]['destination']
        destination = result['journeys'][0]['legs'][last_leg]['destination']
        transportation = result['journeys'][0]['legs'][first_leg]['transportation']


        # Origin info
        origin_stop_id = origin['id']
        origin_name = origin['name']
        origin_departure_time = origin['departureTimeEstimated']

	# How long until it leaves?
        due = self.get_due(datetime.strptime(origin_departure_time, fmt))

        # Destination info
        destination_stop_id = destination['id']
        destination_name = destination['name']
        destination_arrival_time = destination['arrivalTimeEstimated']

        # Origin type info - train, bus, etc
        origin_mode_temp = transportation['product']['class']
        origin_mode = self.get_mode(origin_mode_temp)
        origin_mode_name = transportation['product']['name']

        # RealTimeTripID info so we can try and get the current location later
        realtimetripid = 'n/a'
        if 'properties' in transportation:
            if 'RealtimeTripId' in transportation['properties']:
                realtimetripid = transportation['properties']['RealtimeTripId']

        # Line info
        origin_line_name_short = transportation['disassembledName']
        origin_line_name = transportation['number']

        # Occupancy info, if it's there
        occupancy = 'UNKNOWN'
        if 'properties' in first_destination:
            if 'occupancy' in first_destination['properties']:
                occupancy = first_destination['properties']['occupancy']

        # Now might be a good time to see if we can also find the latitude and longitude
        # Using the Realtime Vehicle Positions API
        latitude = 'n/a'
        longitude = 'n/a'

        if realtimetripid != 'n/a':
            # Build the URL
            url = \
                'https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos' \
                 + self.get_url(origin_mode)
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

                if origin_mode == 'Train':
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
            ATTR_DUE_IN: due,
            ATTR_ORIGIN_STOP_ID : origin_stop_id,
            ATTR_ORIGIN_NAME : origin_name,
            ATTR_DEPARTURE_TIME : origin_departure_time,
            ATTR_DESTINATION_STOP_ID : destination_stop_id,
            ATTR_DESTINATION_NAME : destination_name,
            ATTR_ARRIVAL_TIME : destination_arrival_time,
            ATTR_ORIGIN_TRANSPORT_TYPE : origin_mode,
            ATTR_ORIGIN_TRANSPORT_NAME: origin_mode_name,
            ATTR_ORIGIN_LINE_NAME : origin_line_name,
            ATTR_ORIGIN_LINE_NAME_SHORT : origin_line_name_short,
            ATTR_CHANGES: changes,
            ATTR_OCCUPANCY : occupancy,
            ATTR_REAL_TIME_TRIP_ID : realtimetripid,
            ATTR_LATITUDE : latitude,
            ATTR_LONGITUDE : longitude
            }
        return self.info


    def find_first_leg(self, legs):
        # Find the first non-footpath leg
        leg_count = len(legs)
        for leg in range (0, leg_count, 1):
            leg_class = legs[leg]['transportation']['product']['class']
            #print (leg_class)
            if leg_class < 100:
                # 100 is the class for walking, anything less is a train, bus, etc
                return leg

        # Hmm, we didn't find one
        return None


    def find_last_leg(self, legs):
        # Find the last non-footpath leg
        leg_count = len(legs)
        for leg in range (leg_count - 1, -1, -1):
            leg_class = legs[leg]['transportation']['product']['class']
            #print (leg_class)
            if leg_class < 100:
                # 100 is the class for walking, anything less is a train, bus, etc
                return leg

        # Hmm, we didn't find one
        return None

    def find_changes(self, legs):
        # Find out how often we have to change
        changes = 0
        leg_count = len(legs)

        for leg in range (0, leg_count, 1):
            leg_class = legs[leg]['transportation']['product']['class']
            if leg_class < 100:
                # 100 is the class for walking, anything less is a train, bus, etc
                changes = changes + 1

        return changes - 1


    def get_mode(self, iconId):
        """Map the iconId to a full text string"""
        modes = {
            1: "Train",
            4: "Light rail",
            5: "Bus",
            7: "Coach",
            9: "Ferry",
            11: "School bus"
        }
        return modes.get(iconId, None)


    def get_url(self, mode):
        """Map the journey mode to the proper real time location URL """

        url_options = {
            "Train"      : "/sydneytrains",
            "Light rail" : "/lightrail/innerwest",
            "Bus"        : "/buses",
            "Coach"      : "/buses",
            "Ferry"      : "/ferries/sydneyferries",
            "School bus" : "/buses"
        }
        return url_options.get(mode, None)


    def get_due(self, estimated):
        """Min until departure"""
        due = 0
        if estimated > datetime.utcnow():
            due = round((estimated - datetime.utcnow()).seconds / 60)
        return due
