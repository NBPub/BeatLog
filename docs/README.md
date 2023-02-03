# BeatLog Guide <img src="https://raw.githubusercontent.com/NBPub/BeatLog/main/BeatLog/static/favicon.png" title="BeatLog!"> 

## Contents

- [Setup](#setup)
	- [Data Sources](#data-sources)
	- [Log Files](#log-files)
	- [Jail.local](#fail2ban-jail)
	- [MaxMindDB](#maxminddb)
	- [Regex](#regex-methods)
- [Parsing](#parsing)
  - [Processed Data](#processed-data)
- [Scheduled Tasks](#scheduled-tasks)
	- [Home IP](#home-ip-check)
	- [Log Check](#log-check)
- [Report](#report-demo)
	- [Home](#home-demo)
	- [Outside](#outside-demo)
	- [Settings, Known Devices](#known-devices)
	- [fail2ban](#fail2ban-demo)
- [Beat! Button](#beat-button)
- [Database Explorer](#database-explorer)
- [Geography](#geography)
	- [Fill Unnamed Locations](#location-lookup)
	- [Visitor Map](#visitor-map-demo)
	- [Data Assessment](#tables-charts)
- [Custom Reports or Maps](#custom-reports-and-maps)
- [Database Cleanup](#database-cleanup)
- [Failed Regex](#failed-regex)

## Setup

This section assumes an installation similar to one provided in the [Docker Compose example](/README.md#docker-compose), and will walk a user through adding all the data sources to **BeatLog**.

### Data Sources

The following files provide information for BeatLog to generate reports and maps:

- **NGINX reverse proxy**
	- access.log - *client requests to the server*
	- error.log - *client request errors and associated severity levels*
- **fail2ban**
	- fail2ban.log - *all activity of fail2ban service, relevant information is parsed and the rest ignored*
	- jail.local - *fail2ban settings and activated filters, checks ignored IPs*
- **MaxMindDB**
	- GeoLite2-City.mmdb - *database to match IP addressess to locations, updated twice monthly*

If you are using [SWAG](https://github.com/linuxserver/docker-swag) for your reverse proxy, the above files live in the following structure. 
These relative paths are demonstrated as volumes below. 

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

Following the example, the files can be loaded into **BeatLog** from the `/import/` directory as listed in the table below.

```yaml
    volumes:
      - /path_to/swag_config/log:/import/log # NGINX and fail2ban logs
      - /path_to/swag_config/fail2ban:/import/fail2ban # fail2ban jail.local
      - /path_to/swag_config/geoip2db:/import/geoip2db # MaxMindDB
```

| File | Path in Container |
| :----: | --- |
| access.log | `/import/log/nginx/access.log` |
| error.log | `/import/log/nginx/error.log` |
| fail2ban.log | `/import/log/fail2ban/fail2ban.log` |
| GeoLite2-City.mmdb | `/import/geoip2db/GeoLite2-City.mmdb` |

### Log Files

*!!! phasing out support for **Unauthorized** log !!!*

Log File locations must be added to **BeatLog** after initial startup. The home page will provide a link for adding Log Files, if all four have not been added. 
Paths shown in pictures may not match the file structure shown above. See the text above pictures for the correct path.

The navigation bar on top provides links to all of the pages shown below. 
Also note the home IP address is red, indicating it is not being ignored by fail2ban. In this case, the fail2ban **jail.local** file has yet to be [added](#fail2ban-jail).

![homepage_fresh](/docs/pics/homepage_fresh.png "Homepage without any logfiles.")

**✱ access.log ✱**

*/import/log/nginx/access.log*

![add_log_file](/docs/pics/add_log_file.png "Adding access.log")

Now that **access.log** has been added, it is no longer in the available list. Additionally, a link to its regex page is presented. 
Before [specifying](#adding-regex-to-logs) regex methods for parsing **access.log**, [regex methods need to be added to BeatLog!](#regex-methods)

![added_log_file](/docs/pics/added_log_file.png "access.log added")


### fail2ban Jail

The fail2ban **jail.local** will provide information on enabled filters and list ignored IP addresses. If an ignored IP matches the home IP address, it is shown in green. 
Each filter (or all at once) can be checked for its Finds, Bans, and Ignores in the past 24 hours (unique IPs, not total).  

**✱ jail.local ✱**

*/import/log/fail2ban/fail2ban.log*

![add_jail](/docs/pics/load_jail.png "Adding jail.local")

![added_jail](/docs/pics/loaded_jail.png "jail.local added")


### MaxMindDB

Specify your **GeoLite2-City** database file in the geography settings to add coordinates and location names to each parsed outside IP address. Settings can be accessed from the **Options** drop-down menu.

![geo_set1](/docs/pics/navbar_settings.png "Geography settings")

**✱ GeoLite2-City.mmdb ✱**

*/import/geoip2db/GeoLite2-City.mmdb*

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

#### ✱Adding Regex to Logs✱

Associate regex methods to Log Files. The default names should be self-explanatory.

![Log_regex](/docs/pics/Log_regex.png "Adding patterns to a log file")

Now that the regex methods/patterns have been added to **access.log**, parsing can be tested. 
*Testing Regex* will run through the current log file, and return results for each regex method. No data is saved from testing. 
In the example below, some lines failed the **primary** method but succeeded with the **secondary** method.

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
- **Update** - perform *[vacuum](https://www.postgresql.org/docs/current/sql-vacuum.html)* on log file's data table, postgresql performs this operation routinely

<details><summary>Show Log check</summary>

![homepage_check](/docs/pics/homepage_check.png "before")
![homepage_checked](/docs/pics/homepage_checked.png "after")
</details>

<details><summary>Show Log update</summary>

![homepage_update](/docs/pics/homepage_update.png "before")
![homepage_updated](/docs/pics/homepage_updated.png "after")
</details>

### Processed Data

The following tables describe how parsed logs and other data are saved into the database. 
See [PostgreSQL docs](https://www.postgresql.org/docs/current/datatype.html) for more information on data types. 
The [Mozilla HTTP docs](https://developer.mozilla.org/en-US/docs/Web/HTML) are a good reference for learning more about each column, 
and are linked where column names are ambiguous.

Wikipedia has a nice [example](https://en.wikipedia.org/wiki/Common_Log_Format#Example) of the **Common Log Format** in its article.

***home*** *and* ***geo*** *columns are determined after parsing log files*

#### Access Logs - access 

| Column | Data Type | Description |
| :----: | --- | --- |
| **date** | datetime | Timestamp of each connection, one second resolution |
| **IP** | inet | client IP address |
| **home** | Boolean | *True* if client IP matches home IP |
| **Method** | text *VARCHAR(20)* | HTTP request [method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods). *8 character limit prior to alpha-0.1.3, 20 character limit after* |
| **URL** | text | Component of resource requested by client |
| **HTTP** | integer | HTTP [network protocol](https://developer.mozilla.org/en-US/docs/Glossary/HTTP_2), typically **2** or **1.1**. It is multiplied by 10 to save as an integer. |
| **Status** | integer | HTTP status [code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status), see [here](https://www.httpstatuses.org/) for a handy list of codes and their descriptions. |
| **Bytes** | integer | Size of object returned to the client |
| **Referrer** | text | Component of resource requested by client, more info and note on spelling issues [here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referer) |
| **Tech** | text | [User-Agent](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) HTTP request header. Used to identify Known Devices. |
| **Geo** | foreign key - Geography | Corresponds to an entry in the Geography table |

Format string for [strptime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) on **date**: 
`%d/%b/%Y:%H:%M:%S`

#### Error Log - error

| Column | Data Type | Description |
| :----: | --- | --- |
| **date** | datetime | Timestamp of each connection, one second resolution |
| **IP** | inet | client IP address |
| **home** | Boolean | *True* if client IP matches home IP |
| **Level** | text | Log level, or measure of severity. See [here](https://nginx.org/en/docs/ngx_core_module.html#error_log) for more info. |
| **Message** | text | Contents of error message |
| **Geo** | foreign key - Geography | Corresponds to an entry in the Geography table |

Format string for [strptime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) on **date**: 
`%Y/%m/%d %H:%M:%S`

#### fail2ban Log - fail2ban

| Column | Data Type | Description |
| :----: | --- | --- |
| **date** | datetime | Timestamp of each connection, millisecond resolution |
| **IP** | inet | client IP address |
| **home** | Boolean | *True* if client IP matches home IP |
| **Filter** | text | fail2ban filter doing the action |
| **Action** | text | fail2ban action, only **Finds**, **Bans**, and **Ignores** are saved. |
| **Geo** | foreign key - Geography | Corresponds to an entry in the Geography table |

Format string for [strptime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) on **date**: 
`%Y-%m-%d %H:%M:%S,%f`

#### Geography Table - geoinfo

Each unique coordinate pair is saved in a **Geography** table. As described above, each log entry is associated with an entry in the **Geography** table.

| Column | Data Type | Description |
| :----: | --- | --- |
| **coords** | \[integer,integer\] | Coordinates provided by MaxMindDB. They are multiplied by **1E4** to save as integers. |
| **city** | text | City name (en) from MaxMindDB or closest name match from Nominatim API |
| **country** | text | Country name (en) from MaxMindDB or from Nominatim API |


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
If [locations](#maxminddb) are added without a name, their locations will be [looked up](#location-lookup).   

The default interval for checking and parsing all available logs is `3` hours, starting 15 minutes after container startup. Set to `0` to disable task.

## Report [|demo|](https://nbpub.github.io/BeatLog/#scrollspyTop)

The report provides valaubale information from your processed data. The duration of a "recent report", **Known Devices**, and other options can be set in the **[Report Settings](#known-devices)**. 
See [custom reports](#custom-reports-and-maps) for report generation over a chosen time range.

Below is the overall summary shown at the top of the report. The **Daily Action Counts** chart summarizes key connection counts. 

![report_top](/docs/pics/Report_Top_summary.png "Start of report, action count table")
*hover over any chart for detailed data*

**Daily Action Counts**
- fail2ban **Finds** (unique IP/filter), overlap of filters possible `... [filter] Found <IP> ...`
- fail2ban **Bans** (unique IP/filter), overlap of filters possible  `... [filter] Ban <IP>`
- outside **Visitors** (unique IP), from error and access logs
- fail2ban **Ignores** (total) `... [filter] Ignore <IP> ...`
- home **Ignorable** (total) - *see bottom row of [home summary](#home) below*

### Home [|demo|](https://nbpub.github.io/BeatLog/#scrollspyHome)

The home connections are summarized in a few tables and bar charts. I have strict fail2ban filters setup for connections that:
1. do not use `HTTP/2`, i.e. `HTTP/1.0` or `HTTP/1.1` connections
2. return 4xx [status codes](https://www.httpstatuses.org/), client errors

Therefore, I flag these connections as **home ignorable**, indicated in the bottom row of the summary table and the action count chart above. 
**Daily Action Counts** above shows a fortunate situation. Despite a number of **home ignorable** connections, no fail2ban filters registered **ignores**.
This suggests that the exceptions I have in my strict filters are allowing what I want them to.

![report_home](/docs/pics/Report_Home_summary.png "Home Summary, daily table and graphs")
![report_home2](/docs/pics/Report_Home_summary2.png "Home Summary, devices")

Note **DSub** and the blurred user-agents in the **Home Devices** table. These are used in the **Known Devices** [setting](#known-devices), to separate certain Outside connections.

As discussed above, no fail2ban home ignores were found in the report duration. If they were, they would be presented in the Home Summary, as shown below.

<details><summary>Home Ignores</summary>

![Report_Home_ignore](/docs/pics/Report_Home_ignore.png "Home Ignores button to show/hide table appears below home devices")
![Report_Home_ignored](/docs/pics/Report_Home_ignored.png "Home Ignores table")

The `404` status returns were caught by the **nginx-http** filter. These requests would have resulted in a ban if the IP were not ignored, as set in [jail.local](#fail2ban-jail).

</details>

### Outside [|demo|](https://nbpub.github.io/BeatLog/#scrollspyOutside)

The outside section provides more detail than the home section. 
The **Hit Counts by Log** chart (top-right) lists the amount of IPs that visited a certain amount of times. For unwanted visitors, the amount of hits should be low. 
The graph below indicates that most visitors (>100) only visited one time. 

Note the one address that had 5 requests. It is also shown in the **Frequent Visitors** table. The table indicates that the IP's 5 hits occured within one second, and it was promptly banned.

![report_outside1](/docs/pics/Report_Outside_summary.png "Report's summary of Outside connections")
![report_outside1](/docs/pics/Report_Outside_frequent.png "Frequent Visitors tables, updated to show data")

As referenced in the **Home Devices** table, a separate **Frequent Visitors - Known Devices** table is provided due to the report [settings](#known-devices). 
These IPs were separated based on their user-agents (tech), and are not shown in the **Hit Counts by Log** table.

A number of **Top 10** tables are presented. The data in these tables may help design fail2ban filters. Top 10 tables now show the average data returned by the requests.

![report_outside2](/docs/pics/Report_Outside_top10_locations.png "Top 10 tables of Outside locations, note settings")

Again, the report settings allow Known Devices to be separated into their own tables.

![report_outside3](/docs/pics/Report_Outside_top10.png "Top 10 tables of outside requested resources and user-agents, note separation of Known Devices")

### Known Devices

The image below shows the available **Report Settings**. All settings shown below were modified from their defaults. 
Report settings are on the same page as **Geography Settings**, and can also be accessed from the **Options** drop-down menu.

**Known Devices** can be used to separate some Outside connections from the rest of the pack. 
They are identified by their [user-agent AKA tech](#processed-data).
Once **Known Devices** have been identified, they can be separated / excluded from a number of report features.

![report_set](/docs/pics/Settings_report.png "exclude Known Devices in Report settings")

The criteria for **fail2ban home ignores** may seem redundant, provided the [discussion](#home) in the home section. 
If fail2ban ignores are found, they are matched to home request(s) based on timestamp and presented together in the **Home Ignores** table. 

***Current implementation of fail2ban Home Ignores may be susceptible to [SQL injection](https://www.psycopg.org/psycopg3/docs/basic/params.html#danger-sql-injection), use with caution***

<details><summary>usage</summary>

**Report Setting:** `(status ...)`, see [database querying](#database-explorer) for help determining setting
```sql
--SQL Selects in Report:
--Home Ignores. time selection omitted from example
SELECT  DISTINCT date_trunc('second', fail2ban.date) "time", filter, <access_info>
FROM "fail2ban" INNER JOIN "access" on date_trunc('second',fail2ban.date) = access.date
WHERE access.home=True AND fail2ban.home=True AND fail2ban.action='Ignore'

-- further specify what might have been ignored
-- 4xx status codes or non HTTP/2 connections
AND (status BETWEEN 400 AND 499 OR http<20)

```

</details>

Given that many requests can happen within a second, and **access.log**'s time resolution of one second vs. fail2ban.log's one micro-second resolution, 
speciying home connections that should be ignored (ignorable) will help match the appropriate home requests with fail2ban ignores. Excess matches may be presented otherwise.

### fail2ban [|demo|](https://nbpub.github.io/BeatLog/#scrollspyfail2ban)

The fail2ban section provides a bar-chart summarizing the filters used (and a table for un-used filters, if present). 
A section of the recent-actions table is shown in the image, which can serve as a sanity check. Are filters finding, and then banning IPs as expected with their number of retries?

![report_f2b](/docs/pics/Report_fail2ban_summary.png "Report's fail2ban summary, filtrate tables not shown")

Not shown in the image are **filtrate tables**. Any outside connections from IPs that were not found or banned by fail2ban will be listed according to their log.

<details><summary>Filtrate</summary>

![Report_fail2ban_filtrate1](/docs/pics/Report_fail2ban_filtrate1.png "Filtrate from both the Access and Error logs, number is total connections")
![Report_fail2ban_filtrate2](/docs/pics/Report_fail2ban_filtrate2.png "Buttons show/hide tables.")

These visitors were not picked up by fail2ban, at least within the duration of the report. They would be prime candidates for the ***[Beat Button](#beat-button)!***

</details>


## Beat Button

On the right side of the navigation bar is a text-box combined with a **Beat** button. This is intended as a companion when reviewing logs or the **Report**. 
Enter a valid IP address and press the button to open a new tab showing recent connections and fail2ban entries matching the IP address.

In this example, the **Top 10 Data Transfers** will be referenced to supply an IP address. 
*Also note the* **Contents** *button on the navigation bar, it appears on the Report page to provide convenient scrolling*

![beat1](/docs/pics/beat_1.png "Enter an IP address and click the button")

The connection from the table is the only one from `54.226.246.60` in the database. This same connection was Found and Banned by fail2ban.

![beat2](/docs/pics/beat_2.png "Tables showing connection and fail2ban data matching the IP")

## Database Explorer

While the [Beat Button](#beat-button) may only provide a limited result of the logs (up to 10 rows from each), 
a log's data can be fully explored through the **Database Query** page. Results are always sorted by time, and 
a specific start or end time can be specified. They default to `one week before now` and `now` on page load.

![dataview1](/docs/pics/query_1.png "Query options for Database Explorer") 

Each log be explored, and a variety of filters, settings, and log-specific pre-assembled queries are provided.

![dataview2](/docs/pics/query_2.png "Queries for each log, basic simply uses the options shown above") 

If the results are larger than the size limit, the result page provides a link to view more data.

![dataview3](/docs/pics/query_3.png "Query result table (entire table not shown).") 

If the **Next** button is used, a **Previous** button is provided on the page. 
This will only backtrack to the query from the source page. Results can be opened in new tabs/windows to maintain order for large datasets.
The **SQL** statement used to generate the table can be viewed for each result.

![dataview4](/docs/pics/query_4.png "If Next button used, a Previous button provides a link to one query back") 


## Geography

After adding the [GeoLite2-City](#maxminddb) file to **BeatLog**, locations will be added to all outside IP addresses. There are a few ways to interact with location data.

### Location Lookup

If a city or country name is not found during parsing, unnamed locations can be manually filled or looked up using reverse geocoding from [Nominatim](https://nominatim.org/release-docs/develop/api/Reverse/). 
The table of unnamed locations provides OpenStreetMaps and GoogleMaps links for the coordinates to help name or check the naming of locations.

*City or country names saved as "None" will be interpreted as [NULL](https://en.wikipedia.org/wiki/Null_(SQL)), currently. can change later*

![Geography_locationfill](/docs/pics/Geography_locationfill.png "(Un)named locations page with blank locations")

Location lookup pauses for one second in between each request to ensure rate limits are observed. If names were added to locations, they are indicated in a list. 
A portion of the resulting page is shown below.

![Geography_locationfilled](/docs/pics/Geography_locationfilled.png "Snippet of page after successful location naming")

How did the Nominatim service do for the top row in the table?
 - Coordinates: **(51.2993, 9.491)**
 - [OpenStreetMap](https://www.openstreetmap.org/#map=14/51.2993/9.4910), [GoogleMaps](https://www.google.com/maps/@51.2993,9.491,13z)
 - Location Filled: **Kassel, Germany**


### Visitor Map [|demo|](https://nbpub.github.io/BeatLog/#scrollspyVisitorMap)

Outside visitor locations can be plotted on an interactive map, with their markers scaled to total connections or number of visitors. 
The **Visitor Map** shows locations logged from the previous few days, or a [customized](#custom-reports-and-maps) date range.

![geo_map1](/docs/pics/Map.png "Visitor map, full table not shown")

Pan and zoom on the map to see more details. Hover over markers to see location names and counts.

![geo_map2](/docs/pics/Map_tooltip.png "Visitor map, zoom and tooltip")

### Tables, Charts

Geography data is grouped and presented as tables or charts in the **Geography > Data Assessment** page. 
As with the [location lookup](#location-lookup) tables, City and Country names can be edited.

![geo_table](/docs/pics/Geography_table.png "Location table with editable City and Country names")

The **Inspect** and **Clean Cache** buttons check that all the saved locations match at least one IP in the database. If a location has no associations, it can be deleted.

The **Top 10** bar charts show top countries or cities by total requests or unique IP addressess.

![geo_chart](/docs/pics/Geography_barchart.png "Location chart, top 10 Cities by unique IPs")

## Custom Reports and Maps

The form to generate **[Maps](#visitor-map-demo)** or **[Reports](#report-demo)** over a user-defined date range is on the bottom of the Report and Geography Settings page, 
and can also be accessed from the **Options** drop-down menu.

![custom](/docs/pics/Settings_custom.png "Custom date range for Report or Visitor Map")

## Database Cleanup

Data saved from log parsing can be deleted from the database, based on date.

![database_cleanup1](/docs/pics/database_cleanup1.png "Database cleanup page")

Data removal must be confirmed after estimation. Canceling will allow another estimate. 

![database_cleanup2](/docs/pics/database_cleanup2.png "Database cleanup - confirm deletion?")


## Failed Regex

Any line that fails parsing will be saved and categorized according to log file. No features have been developed to assess or delete Failed Regex lines.