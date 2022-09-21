# BeatLog Guide

## Contents

- [Setup](#setup)
	- [Data Sources](#data-sources)
	- [Log Files](#log-files)
	- [Jail.local](#fail2ban-jail)
	- [MaxMindDB](#maxminddb)
	- [Regex](#regex-methods)
- [Parsing](#parsing)
- [Scheduled Tasks](#scheduled-tasks)
	- [Home IP](#home-ip-check)
	- [Log Check](#log-check)
- [Report](#report)
- [Beat! Button](#beat-button)
- [Geography](#geography)
- [Custom Reports or Maps](#custom-reports-and-maps)
- [Database Cleanup](#database-cleanup)
- [Failed Regex](#failed-regex)

## Setup

This section assumes an installation similar to one provided in the example, and will walk a user through adding all the data sources to **BeatLog**.

### Data Sources

The following files provide information for BeatLog to generate reports and maps:

- **NGINX**
	- access.log - *client requests to the server*
	- error.log - *various issues and associated severity levels*
	- unauthorized.log - *redundant to **access.log**, captures requests with [401 HTTP status codes](https://www.httpstatuses.org/401)*
- **fail2ban**
	- fail2ban.log - *all activity of fail2ban service, relevant information is parsed and the rest ignored*
	- jail.local - *fail2ban settings and activated filters, checks whether "home" IP is ignored*
- **MaxMindDB**
	- GeoLite2-City.mmdb - *database to match IP addressess to locations, updated twice monthly*

If you are using [SWAG](https://github.com/linuxserver/docker-swag) for your reverse proxy, the above files live in the following structure. 
These relative paths are demonstrated as volumes in the provided [Docker Compose example](/README.md#docker-compose). 

Following the example, the files can be loaded into **BeatLog** from the `/import/` directory.

```
SWAG Config
│
└───log
│   │
│   └───fail2ban
│   │    │   fail2ban.log
│   │      
│   └───nginx
│   │    │   access.log
│   │    │   error.log
│   │    │   unauthorized.log
│   │    │   ...  
│   │   ...
│ 
└───fail2ban 
│   │   jail.local
│   │   ...
│
└───geoip2db
│   │   GeoLite2-City.mmdb 
│ ...
```

### Log Files

Log File locations must be added to **BeatLog** after initial startup. The home page will provide a link to add a Log File, if all four have not been added.

The navigation bar on top provides links to all of the pages shown below. 
Also note the home IP address is red, indicating it is not being ignored by fail2ban. In this case, the fail2ban **jail.local** file has yet to be [added](#fail2ban-jail).

![homepage_fresh](/docs/pics/homepage_fresh.png "Homepage without any logfiles.")

**✱ access.log ✱**

![add_log_file](/docs/pics/add_log_file.png "Adding access.log")

Now that **access.log** has been added, it is no longer in the available list. Additionally, a link to its regex page is presented. 
Before [specifying](#adding-regex-to-logs) regex methods for parsing **access.log**, [regex methods need to be added to BeatLog!](#regex-methods)

![added_log_file](/docs/pics/added_log_file.png "access.log added")


### fail2ban Jail

The fail2ban **jail.local** will provide information on enabled filters and ignored IP addresses. If an ignored IP matches the home IP address, it is shown in green. 
Each filter (or all at once) can be checked for its Finds, Bans, and Ignores in the past 24 hours.  

**✱ jail.local ✱**

![add_jail](/docs/pics/load_jail.png "Adding jail.local")

![added_jail](/docs/pics/loaded_jail.png "jail.local added")


### MaxMindDB

Specify your **GeoLite2-City** database file in the geography settings to add coordinates and location names to each parsed outside IP address. Settings can be accessed from the **Options** drop-down menu.

![geo_set1](/docs/pics/navbar_settings.png "Geography settings")

**✱ GeoLite2-City.mmdb ✱**

![geo_set2](/docs/pics/Settings_geography.png "Geography settings, MaxMindDB")

While here, a user-agent header may be specified for reverse geocoding. This is required to [look-up](#location-lookup) unnamed locations. 
Refer to the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/).

### Regex Methods

Load the default regex patterns to get started parsing logs.

![regex_load](/docs/pics/load_regex_methods.png "Empty regex methods")

The default methods should provide everything needed to parse the four different logs. Each one is shown below, and the *access_secondary* pattern is highlighted. 
If any of the default methods are deleted, they can be reloaded again with the button shown above. If a pattern is edited or saved with the same name as a default method, it will not be overwritten.

![regex_loaded](/docs/pics/loaded_regex_methods.png "Default regex methods")

*Note:* **unauthorized.log** *follows the same patterns as* **access.log**

#### Adding Regex to Logs

Add and test regex with log files. The default names should be self-explanatory.

![Log_regex](/docs/pics/Log_regex.png "Adding patterns to a log file")

Now that the regex methods/patterns have been added to **access.log**, parsing can be tested. 
*Testing Regex* will run through the current log file, and return results for each regex method. No data is saved from testing. 
In the example below, the **primary** and **secondary** methods have parsed all lines, 
but some lines failed the **primary** method and succeeded with the **secondary** method.

![Log_regex_test](/docs/pics/Log_regex_test.png "Testing regex")

## Parsing

Once all the logs have been added, the home page will appear similar to the image shown below. If you have yet to parse any logs, then it should look different. 
From the home page, you can parse logs individually, or all at once using the **Parse All** button on the navigation bar. 
Individual log parsing will open a new page with detailed results. Parsing all logs returns the home page with brief alerts for each log.

![homepage](/docs/pics/homepage.png "BeatLog home page with all logs ready to be parsed")

A few other functions are available from the home page:
- **Location** - edit log file's location or delete log file
- **Regex** - adjust or test regex methods used to parse log file
- **Check** - update log file's *date modified*, if it is different from when the log was last parsed, it will be highlighted

<details><summary>Show Log check</summary>

![homepage_check](/docs/pics/homepage_check.png "before")
![homepage_checked](/docs/pics/homepage_checked.png "after")

</details>

- **Update** - perform *vacuum* on log file's data table, postgresql performs this operation routinely

<details><summary>Show Log update</summary>

![homepage_update](/docs/pics/homepage_update.png "before")
![homepage_updated](/docs/pics/homepage_updated.png "after")

</details>


## Scheduled Tasks

Routine home IP checks and log parsing can be scheduled using the `check_IP` and `check_Log` environmental variables.

Example log of scheduled tasks:
```
[2022-09-17 12:57:04,665] INFO in scheduler_tasks: Scheduled Home IP check skipped
[2022-09-17 13:11:37,683] INFO in scheduler_tasks: 
unauthorized: unauthorized has not changed since last parse.
access: Parsing completed, 374 lines added in 2s.
fail2ban: Parsing completed, 11 lines added in 0s.
error: Parsing completed, 2 lines added in 0s
```

### Home IP check

Home IP is checked using the [ident.me](ident.me) website. It happens when actively using **BeatLog** (requesting pages), and at most every 30 minutes. 
Up to date home IP addresses will ensure that the parsed connections are appropriately classified.

The default interval for home IP checks is `12` hours, starting 30 seconds after container startup. Set to `0` to disable task.

### Log Check

Without scheduling, logs are only [parsed](#parsing) by user request. Logs will only be parsed if their *date modified* has changed since the last parsing.

The default interval for checking and parsing all available logs is `3` hours, starting 15 minutes after container startup. Set to `0` to disable task.

## Report

The report provides valaubale information from your processed data. The duration of a "recent report", **Known Devices**, and other options can be set in the **[Settings](#known-devices)**. 
See [custom reports](#custom-reports-and-maps) for report generation over a chosen time range.

Below is the overall summary shown at the top of the report. The action count table summarizes key connection counts. 
The image shows the hover action of bar charts in the report.

![report_top](/docs/pics/Report_Top_summary.png "Start of report, action count table")

**Action Count Table**
- fail2ban **finds** (unique IP/filter), overlap of filters possible
- fail2ban **bans** (unique IP/filter), overlap of filters possible 
- outside **visitors** (unique IP), from error and access logs
- fail2ban **ignores** (total)
- home **ignorable** (total) - *see bottom row of [home summary](#home) below*

### Home

The home connections are summarized in a few tables and bar charts. I have strict fail2ban filters setup for connections that:
1. do not use `HTTP/2`, i.e. `HTTP/1.0` and `HTTP/1.1` connections
2. return 4xx status codes, client errors

Therefore, I flag these connections from "home", and add these connections as **home ignorable** to the action count table above. 
The action count table above shows a fortunate situation. Despite a number of **home ignorable** connections, no fail2ban filters registered **ignores**.
This suggests that the exceptions I have in my strict filters are allowing what I want them to.

![report_home](/docs/pics/Report_Home_summary.png "Report's summary of Home connections")

As discussed above, no fail2ban home ignores logged. If they were, they would be presented in the Home Summary. 
Note **DSub** and the blurred user-agents in the table above. These devices are used in the **Known Devices** [setting](#known-devices), shown below.

### Outside

The outside section provides more detail than the home section. 
The **Hit Counts by Log** chart lists the amount of IPs that visited a certain amount of times. For unwanted visitors, the amount of hits should be low. 
The graph below indicates that most visitors (>100) only visited one time. 

Note the one address that had 5 requests. It is also shown in the **Frequent Visitors** table. The table indicates that the IP's 5 hits occured within one second, and it was promptly banned.

![report_outside1](/docs/pics/Report_Outside_summary.png "Report's summary of Outside connections")

As referenced in the **Home Devices** table, a separate **Frequent Visitors - Known Devices** table is provided due to the report [settings](#known-devices). 
These IPs were separated based on their user-agents (tech), and are not shown in the **Hit Counts by Log** table.

A number of **Top 10** tables are presented. The data in these tables may help design fail2ban filters.

![report_outside2](/docs/pics/Report_Outside_top10_locations.png "Top 10 tables of Outside locations, note settings")

Again, the report settings allow Known Devices to be separated into their own tables.

![report_outside3](/docs/pics/Report_Outside_top10.png "Top 10 tables of outside requested resources and user-agents, note separation of Known Devices")

### Known Devices

The image below shows the available **Report Settings**. The only default left in the settings below is the 3 day duration of the Recent Report. 
Report settings are on the same page as **Geography Settings**, and can also be accessed from the **Options** drop-down menu.

**Known Devices** can be used to separate some Outside connections from the rest of the pack. These may be particular apps on your mobile phone, or a particular outside visitor (IP) to your server. 
Provide criteria for a [SQL select](https://www.postgresql.org/docs/current/sql-select.html) statement to tell **BeatLog** how to exclude them; beware that report generation may fail with invalid SQL syntax. 
In this example, Outside connections with particular user-agents (AKA tech) are separated.
 
Once **Known Devices** have been identified, they can be separated / excluded from a number of report features.

![report_set](/docs/pics/Settings_report.png "exclude Known Devices in Report settings")

The criteria for **fail2ban home ignores** may seem redundant, provided the [discussion](#home) in the home section. 
If fail2ban ignores are found, they are matched to the nearest home request and presented together in the **Home Ignores** table. 
Given that many requests can happen within a second, and that **access.log** has a time resolution of one second vs. fail2ban.log having a one micro-second resolution, 
speciying home connections that should be ignored (ignorable) will help match the appropriate home requests with fail2ban ignores.

### fail2ban

The fail2ban section provides a bar-chart summarizing the filters used (and a table for un-used filters, if present). 
A section of the recent-actions table is shown in the image, this can serve as a sanity check. Are filters finding, and then and banning IPs as expected with their number of retries?

![report_f2b](/docs/pics/Report_fail2ban_summary.png "Report's fail2ban summary, filtrate tables not shown")

Not shown in the image are **filtrate tables**. Any outside connections from IPs that were not found or banned by fail2ban will be listed according to their log.

## Beat Button

On the right side of the navigation bar is a text-box combined with a green **Beat** button. This is intended as a companion when reviewing logs or the **Report**. 
Enter a valid IP address and press the button to open a new tab showing recent connections and fail2ban entries matching the IP address.

![beat1](/docs/pics/beat_1.png "The IP matching the top data transfer will be investigated")

*Also note the contents button on the navigation bar. This appears when on the Report page to provide convenient scrolling to various report sections*

![beat2](/docs/pics/beat_2.png "Tables showing connection and fail2ban data matching the IP")

## Geography

After adding the [GeoLite2-City](#maxminddb) file to **BeatLog**, locations will be added to all outside IP addresses. There are a few ways to interact with location data.

### Location Lookup

If a city or country name is not found during parsing, unnamed locations can be manually filled or looked up using reverse geocoding from [Nominatim](https://nominatim.org/release-docs/develop/api/Reverse/). 
The table of unnamed locations provides OpenStreetMaps and GoogleMaps links for the coordinates to help name or check the naming of locations. 

![Geography_locationfill](/docs/pics/Geography_locationfill.png "(Un)named locations page with blank locations")

Location lookup pauses for one second in between each request to ensure rate limits are observed. If names were added to locations, they are indicated in a list.

![Geography_locationfilled](/docs/pics/Geography_locationfill.png "Snippet of page after successful location naming")

How did the Nominatim service do for the top row in the table?

**Fill Example**
 - Coordinates: **(51.2993, 9.491)**
 - [OpenStreetMap](https://www.openstreetmap.org/#map=14/51.2993/9.4910)
 - [GoogleMaps](https://www.google.com/maps/@51.2993,9.491,13z)
 - Location Filled: **Kassel, Germany**


### Visitor Map

Outside visitors can be plotted on a map, with the markers scaled to a location's total connections or number of visitors. 
The **Visitor Map** shows visitors from the previous few days, or the date range can be [customized](#custom-reports-and-maps).

![geo_map1](/docs/pics/Map.png "Visitor map, full table not shown")

Pan and zoom on the map to see more details. Hover over markers to see a counts.

![geo_map2](/docs/pics/Map_tooltip.png "Visitor map, zoom and tooltip")

### Tables, Charts

Geography data is grouped and presented as tables or charts in the **Geography > Data Assessment** page. 
As with the [location lookup](#location-lookup) tables, City and Country names can be edited.

![geo_table](/docs/pics/Geography_table.png "Location table with editable City and Country names")

The **Top 10** bar charts show top countries or cities by total requests or unique IP addressess.

![geo_chart](/docs/pics/Geography_barchart.png "Location chart, top 10 Cities by unique IPs")

## Custom Reports and Maps

The form to generate **[Maps](#visitor-map)** or **[Reports](#report)** over a user-defined date range is on the bottom of the Report and Geography Settings page, 
and can also be accessed from the **Options** drop-down menu.

![custom](/docs/pics/Settings_custom.png "Custom date range for Report or Visitor Map")

## Database Cleanup

Data saved from log parsing can be deleted from the database, based on timestamp.

![database_cleanup1](/docs/pics/database_cleanup1.png "Database cleanup page")

Data removal is confirmed after estimation. Canceling will allow another estimate. 

![database_cleanup2](/docs/pics/database_cleanup2.png "Database cleanup - confirm deletion?")


## Failed Regex

Any line that fails parsing will be saved and categorized according to log file. No features have been developed to assess or delete Failed Regex lines.