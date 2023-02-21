# Database Features Documentation

 - [Explorer](#database-explorer)
   - [Query](#query)
   - [Results](#results)
 - [Cleanup](#database-cleanup)
 - [Failed Regex](#failed-regex) 
 
## Database Explorer

While the [Beat Button](/docs/Features/Report.md#beat-button) only provides a limited result (up to 10 rows from each log), 
a log's data can be fully explored through the **Database Query** page. 

![dataview1](/docs/pics/query_1.png "Query options for Database Explorer") 

Results are always sorted by time, with a specific start or end time specified. 
They default to `Starting : one week before now` and `Ending : now` on page load.

*[Review parsed data and database schema](/docs#processed-data)*

### Query

Each log's database table can be explored, and a variety of filters, settings, and log-specific pre-assembled queries are provided.

![dataview2](/docs/pics/query_2.png "Queries for each log, basic simply uses the options at the top of the page") 

<details><summary>Query Descriptions</summary>

| Log - Query | Description |
| :----: | --- |
| **ALL** - Basic | Simply use the options specified at the top of the page. They default to all entries, going back from now, limited to 50 rows per page. |
| --- | --- | --- |
| **Access** - Ignorable | Hits matching *Home Ignorable* [specification](/docs/Features/Report.md#home-ignorable), if set. |
| **Access** - Known Devices | Hits with user-agents matching *Known Devices* [specification](/docs/Features/Report.md#known-devices), if set. |
| **Access** - Filtrate | Outside hits with IPs not banned by fail2ban. Matches limited to one-week blocks. |
| **Access** - Regex2 | Log data processed by the *default* secondary [regex method](/docs#adding-regex-to-logs). They lack [data](/docs#access-logs---access) for HTTP protocol version and request method. |
| **Access** - HTTP v X | Hits with the specified HTTP network protocol [version](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Evolution_of_HTTP). One grouping for `2.0` and another for `1.0, 1.1` |
| **Access** - HTTP Xxx | Hits with the specified HTTP response [status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) grouping. see [Neat Reference](https://www.httpstatuses.org/) |
| --- | --- | --- |
| **Error** - IP v X | Internet Protocol address [version](https://en.wikipedia.org/wiki/IP_address#IP_versions). `IPv4` or `IPv6` |
| **Error** - Filtrate | Outside hits with IPs not banned by fail2ban. Matches limited to one-week blocks. |
| **Error** - Level | All available Error Log [severity levels](https://en.wikipedia.org/wiki/Syslog#Severity_level) for entries are provided. Parsed data [info](/docs##error-log---error)  |
| --- | --- | --- |
| **fail2ban** - Ignores | fail2ban entries with the "Ignore" action. I have fail2ban ignore my local, "Home", IP to allow me to tailor filters.  |
| **fail2ban** - Match Ignores | Attempt to match fail2ban ignores with home hits on the access log. Home Ignorable [specification](/docs/Features/Report.md#home-ignorable) may improve matching. Same table as shown in [report](https://nbpub.github.io/BeatLog/#scrollspyHomeIgs). |
| **fail2ban** - Filter | query for each fail2ban filter |

</details>

### Results

Coordinates, Cities, and Counties are added if any of the results have [geoinfo](/docs#maxminddb). 
Unlike the report, the data is not styled in any way, providing a raw view of the database. 
Data styling is retained for ***Match Ignores***, however, which attempts to combine associated entries from 
the **[fail2ban](/docs#fail2ban-log---fail2ban)** and **[access](/docs#access-logs---access)**logs. 
*[Report demo example](https://nbpub.github.io/BeatLog/#scrollspyHomeIgs)*

If the results are larger than the size limit, the result page provides a link to view more data. 

![dataview3](/docs/pics/query_3.png "Query result table (entire table not shown).") 

If the **Next** button is used, a **Previous** button is provided on the page. 
This will only backtrack to the query its the source page. 
For this reason, it may be beneficial to open **Next** results in a new tab or window.

The **SQL** statement used to generate the table can be viewed for each result. 

![dataview4](/docs/pics/query_4.png "If Next button used, a Previous button provides a link to one query back") 

Conveniently, it can be copied to the clipboard with a click.

![dataview5](/docs/pics/query_5.png "Copy SQL statement to clipboard") 
![dataview6](/docs/pics/query_6.png "Paste SQL statement somewhere") 

*This action may be disabled by web browser, [SSL certificate](https://github.com/FiloSottile/mkcert) may be required.*

## Database Cleanup


Data saved from log parsing can be deleted from the database, based on date.

![database_cleanup1](/docs/pics/database_cleanup1.png "Database cleanup page")

Data removal must be confirmed after estimation. Canceling will allow another estimate. 

![database_cleanup2](/docs/pics/database_cleanup2.png "Database cleanup - confirm deletion?")

## Failed Regex

Any line that fails parsing will be saved and categorized according to log file. 
No features have been developed to assess or delete Failed Regex lines.