# TransportNSW
Python lib to access Transport NSW information.

## How to Use

### Get an API Key
An OpenData account and API key is required to request the data. More information on how to create the free account can be found here:
https://opendata.transport.nsw.gov.au/user-guide .

### Get the stop and line
The libary will expect at least the stop_id to request the next leave events. The easiest way to get the ID is using Google Maps and clicking on one of the bus, train or ferry stops. The information pane on the left will show the relevant stop ID.

Another source for the stop ID and line is  https://transportnsw.info/stops#/. It provides the option to search for a stop and the corresponding lines leaving from there. 

By default the return is the first journey that fits your criteria.  You can optionally specific a minimum 'due time' (in minutes) to see journeys further in the future, for example to give you time to get to the station.

If possible, general occupancy level and the latitude and longitude of the selected journey's vehicle (train, bus, etc) will be returned.

### API Documentation
The source API details can be found here: https://opendata.transport.nsw.gov.au/node/601/exploreapi

### Parameters
```python
.get_departures(stop_id, route, destination, api_key, minimum_due_time)
```

### Sample Code
The following example will request the next leave event for stop ID *2015133*.

**Code:**
```python
from TransportNSW import TransportNSW
tnsw = TransportNSW()
journey = tnsw.get_departures('2015133', '', '', 'YOUR_API_KEY', 0)
print(journey)
```
**Result:**
```python
{'stop_id': '2015133', 'route': 'T9 Northern Line', 'due': 2, 'delay': 0, 'real_time': 'y', 'destination': 'Gordon via Lindfield', 'mode': 'Train', 'occupancy': 'n/a', 'trip_id': '151V.1287.126.16.A.8.61670049', 'latitude': -33.89567184448242, 'longitude': 151.1886749267578}
```

* stpo_id: the departure stop ID that was specified
* route: bus, train, ferry number or line description
* due: minutes until departure
* delay: delay in minutes from the scheduled leave time
* real_time: flag if the journey has real_time information
* destination: end point of the route for that journey
* mode: The type of journey - train, bus, etc
* occupancy: The overall occupancy of the vehicle, if available
* trip_id: The unique trip ID, useful for other API calls such as geolocation
* latitude & longitude: The location of the vehicle, if available

Leaving the line field empty will return any bus/train/ferry leaving next from a given stop.

**Code:**
```python
journey = tnsw.get_departures('209516', '', '', 'YOUR_API_KEY', 0)
```

Setting a destination will return the first journey from that stop_id on the specified route.  Example for ferries leaving Balmain Warf towards Circular Quay

**Code:**
```python
journey = tnsw.get_departures('10102008','','Circular Quay' 'YOUR_API_KEY')
```

### Errors
No leave event with wrong stop ID or not matching route.
```
{'stop_id': 'n/a', 'route': 'n/a', 'due': 'n/a', 'delay': 'n/a', 'real_time': 'n/a', destination: 'n/a'}
```
