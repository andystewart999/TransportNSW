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
The source API details can be found here: https://opendata.transport.nsw.gov.au/sites/default/files/2023-08/Trip%20Planner%20API%20manual-opendataproduction%20v3.2.pdf

### Parameters
```python
.get_trip(origin_stop_id, destination_stop_id, api_key, [trip_wait_time = 0])
```

TransportNSW's trip planner works much better if you use the general location IDs (eg Central Station) rather than a specific platform id (eg Central Station, Platform 19).  Forcing a specific platform sometimes results in much more complicated trips.

### Sample Code
The following example will return the next trip from a bus stop in St. Ives to Central Station, without specifying a specific destination platform.

**Code:**
```python
from TransportNSW import TransportNSW
tnsw = TransportNSW()
journey = tnsw.get_trip('207537', '10101100', 'YOUR_API_KEY')
print(journey)
```
**Result:**
```python
{'due': 23, 'origin_stop_id': '207537', 'origin_name': 'St Ives, Mona Vale Rd at Shinfield Ave', 'departure_time': '2020-06-28T10:10:00Z', 'destination_stop_id': '2000338', 'destination_name': 'Sydney, Central Station, Platform 18', 'arrival_time': '2020-06-28T11:02:00Z', 'origin_transport_type': 'Bus', 'origin_transport_name': 'Sydney Buses Network', 'origin_line_name': '195', 'origin_line_name_short': '195', 'changes': 1, 'occupancy': 'UNKNOWN', 'real_time_trip_id': '612993', 'latitude': 'n/a', 'longitude': 'n/a'}
```

* due: the time (in minutes) before the journey starts 
* origin_stop_id: the specific departure stop id
* origin_name: the name of the departure location
* departure_time: the departure time
* destination_stop_id: the specific destination stop id
* destination_name: the name of the destination location
* arrival_time: the arrival time at the origin
* origin_transport_type: the type of transport, eg train, bus, ferry etc
* origin_transport_name: the full name of transport providere
* origin_line_name & origin_line_name_short: the full and short names of the journey
* changes: how many transport changes are needed
* occupancy: how full the vehicle is, if available
* real_time_trip_id: the unique TransportNSW id for that specific journey
* latitude & longitude: The location of the vehicle, if available

Please note that the origin and destination detail is just that.  We don't return any intermediate steps, transport change types etc other than the total number of changes.  The assumption is that you'll know the details of your specified trip, you just want to know when the next departure is.  If you need much more detailed information then I recommend that you use the full Transport NSW trip planner website or application.

## Thank you
Thank you Dav0815 for your TransportNSW library that the vast majority of this fork is based on.  I couldn't have done it without you!
https://github.com/Dav0815/TransportNSW
