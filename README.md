# TransportNSW
Python lib to access Transport NSW information.

## How to Use

### Get an API Key
An OpenData account and API key is required to request the data. More information on how to create the free account can be found here:
https://opendata.transport.nsw.gov.au/user-guide.  You need to register an application that needs both the Trip Planner and Realtime Vehicle Positions APIs

### Get the stop IDs
The function needs the stop IDs for the source and destination, and optionally how many minutes from now the departure should be, and if you want to filter trips by a specific transport type.  The easiest way to get the stop ID is via https://transportnsw.info/stops#/. It provides the option to search for either a location or a specific platform, bus stop or ferry wharf.  Regardless of if you specify a general location for the origin or destination, the return information shows the stop_id for the actual arrival and destination platform, bus stop or ferry wharf.

If it's available, the general occupancy level and the latitude and longitude of the selected journey's vehicle (train, bus, etc) will be returned.

### API Documentation
The source API details can be found here: https://opendata.transport.nsw.gov.au/sites/default/files/2023-08/Trip%20Planner%20API%20manual-opendataproduction%20v3.2.pdf

### Parameters
```python
.get_trip(origin_stop_id, destination_stop_id, api_key, [trip_wait_time = 0], [transport_type = 0], [strict_transport_type = False], [raw_output = False], [number_of_trips = 1)
```
TransportNSW's trip planner can work better if you use the general location IDs (eg Central Station) rather than a specific Stop ID (eg Central Station, Platform 19) for the destination, depending on the transport type.  Forcing a specific end destination sometimes results in much more complicated trips.  Also note that the API expects (and returns) the Stop IDs as strings, although so far they all appear to be numeric.

### transport_type filters
```
1: Train
4: Light rail
5: Bus
7: Coach
9: Ferry
11: School bus
99: Walk
100: Walk
107: Cycle
```
If you call the function with any `travel_type` filter and set `strict_transport_type` to `True`, only journeys whose **first** leg matches the desired filter will be considered.  Otherwise the filter includes all journeys as long as **any** of the legs includes the desired travel type.

`raw_output` simply returns the entire API response string as JSON, without making any changes to it.  `number_of_trips` will define how many journeys to return in this case.

### Sample Code

The following example will return the next trip that starts from a bus stop in St. Ives (207537) five minutes from now, to Central Station's general stop ID (10101100):

**Code:**
```python
from TransportNSW import TransportNSW
tnsw = TransportNSW()
journey = tnsw.get_trip('207537', '10101100', 'YOUR_API_KEY', 5)
print(journey)
```
**Result:**
```python
{"due": 3, "origin_stop_id": "207537", "origin_name": "Mona Vale Rd at Shinfield Ave, St Ives", "departure_time": "2024-05-20T21:59:48Z", "destination_stop_id": "2000338", "destination_name": "Central Station, Platform 18, Sydney", "arrival_time": "2024-05-20T22:47:36Z", "origin_transport_type": "Bus", "origin_transport_name": "Sydney Buses Network", "origin_line_name": "195", "origin_line_name_short": "195", "changes": 1, "occupancy": "MANY_SEATS", "real_time_trip_id": "2096551", "latitude": -33.72665786743164, "longitude": 151.16305541992188}
```
Fun fact:  TransportNSW's raw API output calls itself JSON, but it uses single quotes for strings in defiance of the JSON standards.  When using this wrapper the output is formatted such that `jq`, for example, is happy with it.

* due: the time (in minutes) before the journey starts
* origin_stop_id: the specific departure stop id
* origin_name: the name of the departure location
* departure_time: the departure time, in UTC
* destination_stop_id: the specific destination stop id
* destination_name: the name of the destination location
* arrival_time: the planned arrival time at the origin, in UTC
* origin_transport_type: the type of transport, eg train, bus, ferry etc
* origin_transport_name: the full name of the transport provider
* origin_line_name & origin_line_name_short: the full and short names of the journey
* changes: how many transport changes are needed on the journey
* occupancy: how full the vehicle is, if available
* real_time_trip_id: the unique TransportNSW id for that specific journey, if available
* latitude & longitude: The location of the vehicle, if available

Please note that the origin and destination detail is just that - information about the first and last stops on the journey at the time the request was made.  We don't return any intermediate steps, transport change types etc other than the total number of changes - the assumption is that you'll know the details of your specified trip, you just want to know when the next departure is.  If you need much more detailed information then I recommend that you use the full Transport NSW trip planner website or application.

## Thank you
Thank you Dav0815 for your TransportNSW library that the vast majority of this fork is based on.  I couldn't have done it without you!
https://github.com/Dav0815/TransportNSW
