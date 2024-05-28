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
.get_trip(origin_stop_id, destination_stop_id, api_key, [journey_wait_time = 0], [transport_type = 0], [strict_transport_type = False], [raw_output = False], [journeys_to_return = 1])
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
If you call the function with a `transport_type` filter and set `strict_transport_type` to `True`, only journeys whose **first** leg matches the desired filter will be considered.  Otherwise the filter includes a journey if **any** of the legs includes the desired travel type.

`raw_output` simply returns the entire API response string as JSON, without making any changes to it.

### Sample Code

The following example will return the next trip that starts from Pymble Station (207310) five minutes from now, to Gordon Station (207210).  Note that specific platforms, such as Gordon Station, Platform 3 (207263) haven't been specified so any platform combination will be accepted:

**Code:**
```python
from TransportNSW import TransportNSW
tnsw = TransportNSW()
journey = tnsw.get_trip('207537', '10101100', 'YOUR_API_KEY', 5)
print(journey)
```
**Result:**

Unless `raw_output` is `True`, the return output always returns an array of journeys, even if `journeys_to_return` is 1.  The journey array is preceded by how many journeys were requested, and how many were actually returned that contained usable data:

```json
{
  "journeys_to_return": 1,
  "journeys_with_data": 1,
  "journeys": [
    {
      "due": 6,
      "origin_stop_id": "2073161",
      "origin_name": "Pymble Station, Platform 1, Pymble",
      "departure_time": "2024-05-28T22:40:24Z",
      "destination_stop_id": "207261",
      "destination_name": "Gordon Station, Platform 1, Gordon",
      "arrival_time": "2024-05-28T22:42:30Z",
      "origin_transport_type": "Train",
      "origin_transport_name": "Sydney Trains Network",
      "origin_line_name": "T1 North Shore & Western Line",
      "origin_line_name_short": "T1",
      "changes": 0,
      "occupancy": "UNKNOWN",
      "real_time_trip_id": "161E.1378.133.60.A.8.80758268",
      "latitude": "n/a",
      "longitude": "n/a"
    }
  ]
}
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
