# BeatLog Report Documentation

## Contents

 - [Overview](#overview)
   - [Settings](#settings)
     - [Known Devices](#known-devices)
	 - [Home Ignorable](#home-ignorable)
     - [Custom Dates](#custom-dates)
   - [Demonstration Page](#demonstration-page)
 - [Home](#home-demo)
 - [Outside](#outside-demo)
 - [fail2ban](#fail2ban-demo)
 - [Beat! Button](#beat-button)
 
 
## Overview

The report provides valaubale information from your processed data. 
The duration of a "recent report", **Known Devices**, and other options can be set in the **[Report Settings](#known-devices)**. 
See the **[custom dates](#custom-dates) setting** for report generation over a chosen time range.

Below is the overall summary shown at the top of the report. 
The **Daily Action Counts** chart summarizes key connection counts. 

![report_top](/docs/pics/Report_Top_summary.png "Start of report, action count table")
*hover over any chart for detailed data*

**Daily Action Counts**
- fail2ban **Finds** (unique IP/filter), overlap of filters possible `... [filter] Found <IP> ...`
- fail2ban **Bans** (unique IP/filter), overlap of filters possible  `... [filter] Ban <IP>`
- outside **Visitors** (unique IP), from error and access logs
- fail2ban **Ignores** (total) `... [filter] Ignore <IP> ...`
- home **Ignorable** (total) - *see bottom row of [home summary](#home-demo)*

## Settings

The image shows the available **Report Settings**. All the settings shown were modified from their defaults. 
Report settings are on the same page as **Geography Settings**, and can also be accessed from the **Options** drop-down menu.

![report_set](/docs/pics/Settings_report.png "exclude Known Devices in Report settings")

Some special **Report Settings** are discussed next.

### Known Devices

**Known Devices** can be used to separate some **Outside** connections from the rest of the pack. 
They are identified by their [user-agent AKA tech](/docs#processed-data).
Once **Known Devices** have been identified, they can be separated / excluded from a number of report features.

### Home Ignorable

The setting for **fail2ban home ignores** may seem redundant, provided the [upcoming discussion](#home-demo) in the home section. 
If fail2ban ignores are found, they are matched to home request(s) based on timestamp and presented together in the **Home Ignores** table. 

Given that many requests can happen within a second, and **[access.log](/docs#access-logs---access)**'s 
time resolution of one second vs. **[fail2ban.log](/docs#fail2ban-log---fail2ban)**'s one milli-second resolution, 
speciying home connections that should be ignored (ignorable) will help match the appropriate home requests with fail2ban ignores. 
Excess matches may be presented otherwise.

***Current implementation of fail2ban Home Ignores may be susceptible to [SQL injection](https://www.psycopg.org/psycopg3/docs/basic/params.html#danger-sql-injection), use with caution***

<details><summary>usage</summary>

**Report Setting:** `(status ...)`, see [database querying](/docs/Features/Database.md#database-explorer) for help determining setting
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

*it is unlikely that you will do harm to your database with bad **fail2ban Home Ignores** setting, but it is probably that your Report will not load and result in a 500 error. Container logs may help*

### Custom Dates

The form to generate **[Maps](/docs/Features/Geography.md#visitor-map-demo)** or **Reports** over a user-defined date range is on the bottom of the Report and Geography Settings page, 
and can also be accessed from the **Options** drop-down menu.

![custom](/docs/pics/Settings_custom.png "Custom date range for Report or Visitor Map")

### [Demonstration Page](https://nbpub.github.io/BeatLog/#scrollspyTop)

You can get a sense of how the report looks and feels by checking out the **[demonstration page](https://nbpub.github.io/BeatLog/#scrollspyTop)**. 
Some links on the page are disabled, and some data has been modified or redacted for sharing. 
Links to the various sections of the demo report will be provided with each section on the page.


## Home [|demo|](https://nbpub.github.io/BeatLog/#scrollspyHome)

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

The `404` status returns were caught by the **nginx-http** filter. These requests would have resulted in a ban if the IP were not ignored, as set in [jail.local](/docs#fail2ban-jail).

</details>

## Outside [|demo|](https://nbpub.github.io/BeatLog/#scrollspyOutside)

The outside section provides more detail than the home section. 
The **Hit Counts by Log** chart (top-right) lists the amount of IPs that visited a certain amount of times. For unwanted visitors, the amount of hits should be low. 
The graph below indicates that most visitors (>100) only visited one time. 

Note the one address that had 5 requests. It is also shown in the **Frequent Visitors** table. The table indicates that the IP's 5 hits occured within one second, and it was promptly banned.

![report_outside1](/docs/pics/Report_Outside_summary.png "Report's summary of Outside connections")
![report_outside1](/docs/pics/Report_Outside_frequent.png "Frequent Visitors tables, updated to show data")

As referenced in the **Home Devices** table, a separate **Frequent Visitors - Known Devices** table is provided due to the report [settings](#known-devices). 
These IPs were separated based on their user-agents (tech), and are not shown in the **Hit Counts by Log** table.

A number of **Top 10** tables are presented. The data in these tables may help design fail2ban filters. Top 10 tables also show the average data returned by the requests.

![report_outside2](/docs/pics/Report_Outside_top10_locations.png "Top 10 tables of Outside locations, note settings")

Again, the report settings allow Known Devices to be separated into their own tables.

![report_outside3](/docs/pics/Report_Outside_top10.png "Top 10 tables of outside requested resources and user-agents, note separation of Known Devices")

## fail2ban [|demo|](https://nbpub.github.io/BeatLog/#scrollspyfail2ban)

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

In this example, the **[Top 10 Data Transfers](#outside-demo)** will be referenced to supply an IP address. 
*Also note the* **Contents** *button on the navigation bar, it appears on the Report page to provide convenient scrolling*

![beat1](/docs/pics/beat_1.png "Enter an IP address and click the button")

The connection from the table is the only one from `54.226.246.60` in the database. This same connection was Found and Banned by fail2ban.

![beat2](/docs/pics/beat_2.png "Tables showing connection and fail2ban data matching the IP")

The **[Database Explorer](/docs/Features/Database.md#database-explorer)** can provide deeper looks into a visitor, if 10 hits is not enough.