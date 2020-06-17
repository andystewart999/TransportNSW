# TransportNSW
Python lib to access Transport NSW information.

## How to Use

### Get an API Key
An OpenData account and API key is required to request the data. More information on how to create the free account can be found here:
https://opendata.transport.nsw.gov.au/user-guide.  You need to register an application that needs both the Trip Planner and Realtime Vehicle Positions APIs

### Get the stop IDs
The library needs the stop ID for the source and destination, and optionally how many minutes from now the departure should be.  The easiest way to get the stop ID is via https://transportnsw.info/stops#/. It provides the option to search for either a location or a specific platform, bus stop or ferry wharf.  Regardless of if you specify a general location for the origin or destination, the return information shows the stop_id for the actual arrival and destination platform, bus stop or ferry wharf.

If it's available, the general occupancy level and the latitude and longitude of the selected journey's vehicle (train, bus, etc) will be returned.

### API Documentation
The source API details can be found here: https://opendata.transport.nsw.gov.au/node/601/exploreapi

### Parameters
```python
.get_trip(origin_stop_id, destination_stop_id, api_key, [trip_wait_time = 0])
```

### Sample Code
The following example will return the next trip from Gordon Station to Pymble Station, without specifying a platform.

**Code:**
```python
from TransportNSW import TransportNSW
tnsw = TransportNSW()
journey = tnsw.get_trip('10101121', '10101123', 'YOUR_API_KEY')
print(journey)
```
**Result:**
```python
{'due': 5, 'origin_stop_id': '207263', 'origin_name': 'Gordon Station', 'origin_detail': 'Platform 3', 'departure_time': '2020-06-14T10:21:30Z', 'destination_stop_id': '2073162', 'destination_name': 'Pymble Station', 'destination_detail': 'Platform 2', 'arrival_time': '2020-06-14T10:23:30Z', 'transport_type': 'Train', 'transport_name': 'Sydney Trains Network', 'line_name': 'T1 North Shore & Western Line', 'line_name_short': 'T1', 'occupancy': 'UNKNOWN', 'real_time_trip_id': '104P.1379.110.128.T.8.61720413', 'latitude': -33.76505661010742, 'longitude': 151.1614227294922}
```

* due: the time (in minutes) before the vehicle arrives 
* origin_stop_id: the specific departure stop id
* origin_name: the name of the general departure location
* origin_detail: the specific departure location
* arrival_time: the arrival time at the origin
* transport_type: the type of transport, eg train, bus, ferry etc
* transport_name: the full name of transport providere
* line_name & line_name_short: the full and short names of the journey
* occupancy: how full the vehicle is
* real_time_trip_id: the unique TransportNSW id for that specific journey
* latitude & longitude: The location of the vehicle, if available

### To do: 
* Add an option to filter by specific transport type, useful if the general departure and arrival ids are being used
* Add an option to show brief vs verbose information

## Thank you
Thank you Dav0815 for your TransportNSW library that the vast majority of this fork is based on.  I couldn't have done it without you!

https://github.com/Dav0815/TransportNSW
