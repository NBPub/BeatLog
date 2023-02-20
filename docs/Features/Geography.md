# BeatLog Geography Documentation

## Contents

 - [Overview](#overview)
  - [Reference Links]()#reference-links)
 - [Location Lookup](#location-lookup)
 - [Visitor Map](#visitor-map-demo) 
  - [Custom Dates](#custom-dates) 
 - [Data Assessment](#data-assessment) 

 
## Overview

After adding the [GeoLite2-City](/docs#maxminddb) file to **BeatLog**, locations will be added to all outside IP addresses. There are a few ways to interact with location data.

### Reference Links

 - ***[Geography Table](/docs#geography-table---geoinfo)***
 - ***[Geography Settings](/docs#maxminddb)***

## Location Lookup

If a city or country name is not found during parsing, unnamed locations can be manually filled or looked up using reverse geocoding from [Nominatim](https://nominatim.org/release-docs/develop/api/Reverse/). 
The table of unnamed locations provides OpenStreetMaps and GoogleMaps links for the coordinates to help name or check the naming of locations.

*City or country names saved as "None" will be interpreted as [NULL](https://en.wikipedia.org/wiki/Null_(SQL)), currently. may change later*

![Geography_locationfill](/docs/pics/Geography_locationfill.png "(Un)named locations page with blank locations")

Location lookup pauses for one second in between each request to ensure rate limits are observed. If names were added to locations, they are indicated in a list. 
A portion of the resulting page is shown below.

![Geography_locationfilled](/docs/pics/Geography_locationfilled.png "Snippet of page after successful location naming")

How did the Nominatim service do for the top row in the table?
 - Coordinates: **(51.2993, 9.491)**
 - [OpenStreetMap](https://www.openstreetmap.org/#map=14/51.2993/9.4910), [GoogleMaps](https://www.google.com/maps/@51.2993,9.491,13z)
 - Location Filled: **Kassel, Germany**


## Visitor Map [|demo|](https://nbpub.github.io/BeatLog/#scrollspyVisitorMap)

Outside visitor locations can be plotted on an interactive map, with location markers scaled to total connections or number of visitors. 
The **Visitor Map** shows locations logged from the previous few days, or a [customized date](#custom-dates) range.

![geo_map1](/docs/pics/Map.png "Visitor map, full table not shown")

Pan and zoom on the map to see more details. Hover over markers to see location names and counts.

![geo_map2](/docs/pics/Map_tooltip.png "Visitor map, zoom and tooltip")

### Custom Dates

The form to generate **Maps** or **[Reports](/docs/Features/Report.md#overview)** over a user-defined date range is on the bottom of the Report and Geography Settings page, 
and can also be accessed from the **Options** drop-down menu.

![custom](/docs/pics/Settings_custom.png "Custom date range for Report or Visitor Map")


## Data Assessment

Geography data is grouped and presented as tables or charts in the **Geography > Data Assessment** page. 
As with the [location lookup](#location-lookup) tables, City and Country names can be edited.

![geo_table](/docs/pics/Geography_table.png "Location table with editable City and Country names")

The **Inspect** and **Clean Cache** buttons check that all the saved locations match at least one IP in the database. If a location has no associations, it can be deleted.

The **Top 10** bar charts show top countries or cities by total requests or unique IP addressess.

![geo_chart](/docs/pics/Geography_barchart.png "Location chart, top 10 Cities by unique IPs")

