# BeatLog Guide

## Setup

This section assumes an installation similar to one provided in the example, and will walk a user through adding all the data sources to **BeatLog**.

***IN PROGRESS***

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

Log File locations must be added to **BeatLog** after initial startup. The homepage will suggest adding a logfile.
The home IP address is red, indicating it is not being ignored by fail2ban. In this case, the fail2ban **jail.local** file has yet to be [added](#fail2ban-jail).

![homepage_fresh](/docs/pics/homepage_fresh.png "Homepage without any logfiles.")

The navigation bar on top provides links to all of the pages shown below.

**access.log**

![add_log_file](/docs/pics/add_log_file.png "Adding access.log")

Now that **access.log** has been added, it is no longer in the available list. Additionally, a link to its regex page is presented. 
Before [specifying](#adding-regex-to-logs) regex methods for parsing **access.log**, [regex methods need to be added to BeatLog!](#regex-methods)

![added_log_file](/docs/pics/added_log_file.png "access.log added")


### fail2ban Jail

**jail.local**

![add_jail](/docs/pics/load_jail.png "Adding jail.local")

![added_jail](/docs/pics/loaded_jail.png "jail.local added")


### MaxMindDB

![geo_set1](/docs/pics/navbar_settings.png "Geography settings")

**GeoLite2-City.mmdb **

![geo_set2](/docs/pics/Settings_geography.png "Geography settings, MaxMindDB")

### Regex Methods

Load the default regex patterns to get started parsing logs.

![regex_load](/docs/pics/load_regex_methods.png "Empty regex methods")

![regex_loaded](/docs/pics/loaded_regex_methods.png "Default regex methods")

#### Adding Regex to Logs

Add and test regex with log files.

![Log_regex](/docs/pics/Log_regex.png "Adding patterns to a log file")

![Log_regex_test](/docs/pics/Log_regex_test.png "Testing regex")

#### Parsing

*details later*

![homepage](/docs/pics/homepage.png "BeatLog home page with all logs ready to be parsed")

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

Home IP is checked using the [ident.me](ident.me) website, when some pages are requested, and at most every 30 minutes. 
Up to date home IP addresses will ensure that the parsed connections are appropriately classified.

The default interval for home IP checks is `12` hours, starting 30 seconds after container startup. Set to `0` to disable task.

### Parse All

Without scheduling, logs are only parsed by user request. Logs will only be parsed if their *date modified* has changed since the last parsing.

The default interval for parsing all available logs is `3` hours, starting 15 minutes after container startup. Set to `0` to disable task.

## Report

*details later*

![report_top](/docs/pics/Report_Top_summary.png "Start of report, action count table")

### Home

![report_home](/docs/pics/Report_Home_summary.png "Report's summary of Home connections")

### Outside

![report_outside1](/docs/pics/Report_Outside_summary.png "Report's summary of Outside connections")
![report_outside2](/docs/pics/Report_Outside_top10_locations.png "Top 10 tables of Outside locations, note settings")
![report_outside3](/docs/pics/Report_Outside_top10.png "Top 10 tables of outside requested resources and user-agents, note separation of Known Devices")

#### Known Devices

![report_set](/docs/pics/Settings_report.png "exclude Known Devices in Report settings")

### fail2ban

![report_f2b](/docs/pics/Report_fail2ban_summary.png "Report's fail2ban summary, filtrate tables not shown")

## Beat Button

## Geography

*details later*

### Visitor Map

![geo_map1](/docs/pics/Map.png "Visitor map, full table not shown")
![geo_map2](/docs/pics/Map_tooltip.png "Visitor map, zoom and tooltip")

### Tables, Charts

![geo_table](/docs/pics/Geography_table.png "Location table with editable City and Country names")
![geo_chart](/docs/pics/Geography_barchart.png "Location chart, top 10 Cities by unique IPs")

## Custom Reports and Maps

![custom](/docs/pics/Settings_custom.png "Custom date range for Report or Visitor Map")

## Database Cleanup

*details, images later*

## Failed Regex

Any line that fails parsing will be saved and categorized according to log file. No features have been developed to assess or delete Failed Regex lines.