"""A module to query Transport NSW (Australia) departure times."""
from datetime import datetime
from google.transit import gtfs_realtime_pb2
import requests.exceptions
import requests
import logging

ATTR_STOP_ID = 'stop_id'
ATTR_ROUTE = 'route'
ATTR_DUE_IN = 'due'
ATTR_DELAY = 'delay'
ATTR_REALTIME = 'real_time'
ATTR_DESTINATION = 'destination'
ATTR_MODE = 'mode'
ATTR_OCCUPANCY = 'occupancy'
ATTR_TRIP_ID = 'trip_id'
ATTR_VEHICLE_LATITUDE = 'latitude'
ATTR_VEHICLE_LONGITUDE = 'longitude'

logger = logging.getLogger(__name__)

class TransportNSW(object):
    """The Class for handling the data retrieval."""

    # The application requires an API key. You can register for
    # free on the service NSW website for it.

    def __init__(self):
        """Initialize the data object with default values."""
        self.stop_id = None
        self.route = None
        self.destination = None
        self.api_key = None
        self.min_due_time = None
        self.info = {
            ATTR_STOP_ID: 'n/a',
            ATTR_ROUTE: 'n/a',
            ATTR_DUE_IN: 'n/a',
            ATTR_DELAY: 'n/a',
            ATTR_REALTIME: 'n/a',
            ATTR_DESTINATION: 'n/a',
            ATTR_MODE: 'n/a',
            ATTR_OCCUPANCY: 'n/a',
            ATTR_TRIP_ID: 'n/a',
            ATTR_VEHICLE_LATITUDE: 'n/a',
            ATTR_VEHICLE_LONGITUDE: 'n/a'
            }

    def get_departures(self, stop_id, route , destination , api_key, min_due_time = 0):
        """Get the latest data from Transport NSW."""
        self.stop_id = stop_id
        self.route = route
        self.destination = destination
        self.api_key = api_key
        self.min_due_time = min_due_time

        # Build the URL including the STOP_ID and the API key
        url = \
            'https://api.transport.nsw.gov.au/v1/tp/departure_mon?' \
            'outputFormat=rapidJSON&coordOutputFormat=EPSG%3A4326&' \
            'mode=direct&type_dm=stop&name_dm=' \
            + self.stop_id \
            + '&departureMonitorMacro=true&TfNSWDM=true&version=10.2.1.42'
        auth = 'apikey ' + self.api_key
        header = {'Accept': 'application/json', 'Authorization': auth}

        # Send the query and return error if something goes wrong
        # Otherwise store the response
        try:
            response = requests.get(url, headers=header, timeout=10)
        except:
            logger.warning("Network or Timeout error")
            return self.info

        # If there is no valid request (e.g. http code 200)
        # log error and return empty object
        if response.status_code != 200:
            logger.warning("Error with the request sent; check api key")
            return self.info

        # Parse the result as a JSON object
        result = response.json()

        # If there are no stop events for the query
        # log an error and return empty object
        try:
            result['stopEvents']
        except KeyError:
            logger.warning("No stop events for this query")
            return self.info

        # Set variables
        maxresults = 1
        monitor = []
        if self.destination != '':
            for i in range(len(result['stopEvents'])):
                destination = result['stopEvents'][i]['transportation']['destination']['name']
                if destination == self.destination:
                    event = self.parseEvent(result, i)
                    if event != None:
                        monitor.append(event)
                    if len(monitor) >= maxresults:
                        # We found enough results, lets stop
                        break
        elif self.route != '':
            # Find the next stop events for a specific route
            for i in range(len(result['stopEvents'])):
                number = result['stopEvents'][i]['transportation']['number']
                if number == self.route:
                    event = self.parseEvent(result, i)
                    if event != None:
                        monitor.append(event)
                    if len(monitor) >= maxresults:
                        # We found enough results, lets stop
                        break
        else:
            # No route defined, find any route leaving next
            for i in range(0, maxresults):
                event = self.parseEvent(result, i)
                if event != None:
                    monitor.append(event)

        # If the monitor object is defined, updated the return object with core infos
        if monitor:
            self.info = {
                ATTR_STOP_ID: self.stop_id,
                ATTR_ROUTE: monitor[0][0],
                ATTR_DUE_IN: monitor[0][1],
                ATTR_DELAY: monitor[0][2],
                ATTR_REALTIME: monitor[0][5],
                ATTR_DESTINATION: monitor[0][6],
                ATTR_MODE: monitor[0][7],
                ATTR_OCCUPANCY: monitor[0][8],
                ATTR_TRIP_ID: monitor[0][9],
                ATTR_VEHICLE_LATITUDE: monitor[0][10],
                ATTR_VEHICLE_LONGITUDE: monitor[0][11]
                }
        return self.info

    def parseEvent(self, result, i):
        """Parse the current event and extract data."""
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        due = 0
        delay = 0
        real_time = 'n'
        occupancy = 'n/a'

        number = result['stopEvents'][i]['transportation']['number']
        planned = datetime.strptime(result['stopEvents'][i]
            ['departureTimePlanned'], fmt)
        destination = result['stopEvents'][i]['transportation']['destination']['name']
        mode = self.get_mode(result['stopEvents'][i]['transportation']['product']['class'])

        # See if we can capture the occupancy data
        if 'properties' in result['stopEvents'][i]['location']:
            if 'occupancy' in result['stopEvents'][i]['location']['properties']:
                occupancy = result['stopEvents'][i]['location']['properties']['occupancy']

        # See if we can capture the unique trip ID - not sure if this is ever not there though
        if 'properties' in result['stopEvents'][i]:
            if 'RealtimeTripId' in result['stopEvents'][i]['properties']:
                trip_id = result['stopEvents'][i]['properties']['RealtimeTripId']

        # Unless realtime data is available the planned is equal to estimated time
        estimated = planned
        if 'isRealtimeControlled' in result['stopEvents'][i]:
            real_time = 'y'
            estimated = datetime.strptime(result['stopEvents'][i]
                ['departureTimeEstimated'], fmt)
        # Only deal with future leave times
        if estimated > datetime.utcnow():
            due = self.get_due(estimated)
            if due > self.min_due_time:
                delay = self.get_delay(planned, estimated)

                # Now might be a good time to see if we can also find the latitude and longitude
                # Harcode for trains right now, but going forwards we need to use the mode to call the right API

                if mode == "Train":
                    mode_url = '/sydneytrains'
                elif mode == "Bus":
                    mode_url = '/buses'

                latitude = 'n/a'
                longitude = 'n/a'

                url = \
                    'https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos' \
                    + mode_url
                auth = 'apikey ' + self.api_key
                header = {'Authorization': auth}

                # Send the query and return error if something goes wrong
                # Otherwise store the response
                try:
                    response = requests.get(url, headers=header, timeout=10)
                except:
                    logger.warning("Network or Timeout error")
                    return self.info

                # If there is no valid request (e.g. http code 200)
                # log error and return empty object
                if response.status_code != 200:
                    logger.warning("Error with the request sent; check api key")
                    return self.info

                # Search the feed and see if we can find the trip_id
                # If we do, capture the latitude and longitude

                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(response.content)

                for entity in feed.entity:
                    if entity.vehicle.trip.trip_id == trip_id:
                        latitude = entity.vehicle.position.latitude
                        longitude = entity.vehicle.position.longitude
                        # We found it, so break out
                        break

                return[
                    number,
                    due,
                    delay,
                    planned,
                    estimated,
                    real_time,
                    destination,
                    mode,
                    occupancy,
                    trip_id,
                    latitude,
                    longitude
                    ]
            else:
                return None
        else:
            return None

    def get_due(self, estimated):
        """Min till next leave event."""
        due = 0
        due = round((estimated - datetime.utcnow()).seconds / 60)
        return due

    def get_delay(self, planned, estimated):
        """Min of delay on planned departure."""
        delay = 0                   # default is no delay
        if estimated >= planned:    # there is a delay
            delay = round((estimated - planned).seconds / 60)
        else:                       # leaving earlier
            delay = round((planned - estimated).seconds / 60) * -1
        return delay

    def get_mode(self, iconId):
        """Map the iconId to proper modes string."""
        modes = {
            1: "Train",
            4: "Lightrail",
            5: "Bus",
            7: "Coach",
            9: "Ferry",
            11: "Schoolbus"
        }
        return modes.get(iconId, None)
