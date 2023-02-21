# BeatLog Documentation <img src="https://raw.githubusercontent.com/NBPub/BeatLog/main/BeatLog/static/favicon.png" title="BeatLog!"> 


## Documentation Pages

- **Installation**
  - [Docker Compose](/README.md#installation)
    - [Parameter Details](/README.md#parameters)
  - [Extras](/docs/Installation/Installation_Extras.md#beatlog-installation-options) 
  - [Local Installation](/docs/Installation/Local_Installation.md#beatlog-local-installation)
- ***Setup Guide***
  - *[this page](#setup-guide-contents))*
- **Features**
  - [Report](/docs/Features/Report.md#contents)
  - [Geography](/docs/Features/Geography.md#contents)
  - [Database](/docs/Features/Database.md#contents)
  - [JSON API](/docs/Features/API.md#simple-json-api)
- **BeatLog History**
  - [Detailed Changelog](/docs/Installation/Changelog.md#contents)
  - [NullConnectionPool](/docs/Installation/NullConnectionPool.md#background)  

## Setup Guide Contents

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

While here, a user-agent header may be specified for reverse geocoding. This is required to [look-up](/docs/Features/Geography.md#location-lookup) unnamed locations. 
Refer to the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/).

### Regex Methods

Load the default regex patterns to get started parsing logs.

![regex_load](/docs/pics/load_regex_methods.png "Empty regex methods")

The default methods should provide everything needed to parse the three different logs. Each one is shown below, and the *access_secondary* pattern is highlighted. 
If any of the default methods are deleted, they can be reloaded again with the button shown above. If a pattern is edited or saved with the same name as a default method, it will not be overwritten.

![regex_loaded](/docs/pics/loaded_regex_methods.png "Default regex methods")


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

Example log of scheduled tasks: *comments added by me, they are not part of the log*
```python
[2022-09-17 12:57:04] [1] [INFO] Scheduled Home IP check complete
[2022-09-17 13:11:37] [1] [INFO] Scheduled Log check complete 
access: Parsing completed, 374 lines added in 2s.
fail2ban: Parsing completed, 11 lines added in 0s.
error: Parsing completed, 2 lines added in 0s

# if locations are enabled and unnamed coordinates exist and a nominatim agent is specified
# --> attempt location fill
[2022-09-17 13:11:41] [1] [INFO] Location Fill: 3 locations named out of 4 in 5 seconds
[2022-09-17 13:11:41] [1] [INFO] (35.0,33.0) named Kannavia, Cyprus. (34.0021,-81.0423) named Columbia, United States. (28.5,-10.0) named caïdat d'Aouint Lahna, Morocco
[2022-09-17 13:11:41] [1] [INFO] Error -- 'address' for (-43.0,67.0)

# address not found for one location, manual update required
# see links below
```

### Home IP check

Home IP is checked using the [ident.me](ident.me) website. It happens when actively using **BeatLog** (requesting pages), and at most every 30 minutes. 
Up to date home IP addresses will ensure that the parsed connections are appropriately classified.

The default interval for home IP checks is `12` hours, starting 30 seconds after container startup. Set to `0` to disable task.

### Log Check

Without scheduling, logs are only [parsed](#parsing) by user request. Logs will only be parsed if their *date modified* has changed since the last parsing. 
If [locations](#maxminddb) are added without a name, their locations will be [looked up](/docs/Features/Geography#location-lookup).   

The default interval for checking and parsing all available logs is `3` hours, starting 15 minutes after container startup. Set to `0` to disable task.