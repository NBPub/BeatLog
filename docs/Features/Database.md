# Database Features Documentation

 - [Explorer](#database-explorer)
   - [Query](#query)
   - [Results](#results)
 - [Cleanup](#database-cleanup)
 - [Failed Regex](#failed-regex) 
 
*[Review parsed data and database schema](/docs#processed-data)*
 
## Database Explorer

`*/db_view/`

While the [Beat! Button](/docs/Features/Report.md#beat-button) only provides a limited result (up to 10 rows from each log), 
a log's data can be fully explored through the **Database Query** page. 

![dataview1](/docs/pics/query_1.png "Query options for Database Explorer") 

Results are always sorted by time, with a specific start or end time specified. 
They default to `Starting : one week before now` and `Ending : now` on page load.


### Query

A variety of filters, settings, and log-specific pre-assembled queries are provided.
The image above shows the **Basic** options. 
The optional *Location* and *IP Address* filters can be toggled; *IP Address* form is not shown.

Detailed query descriptions follow the image.

![dataview2](/docs/pics/query_2.png "Queries for each log, basic simply uses the options at the top of the page") 

<details><summary><b>Query Descriptions</b></summary>

| Log - Query | Description |
| :----: | --- |
| **ALL** - Basic | Simply use the options specified at the top of the page. They default to all entries, going back from now, limited to 50 rows per page. |
| <br> |<br> |
| **Access** - Ignorable | Hits matching *Home Ignorable* [specification](/docs/Features/Report.md#home-ignorable), if set. |
| **Access** - Known Devices | Hits with user-agents matching *Known Devices* [specification](/docs/Features/Report.md#known-devices), if set. |
| **Access** - Filtrate | Outside hits with IPs not banned by fail2ban. Matches limited to one-week blocks. |
| **Access** - Regex2 | Log data processed by the *default* secondary [regex method](/docs#adding-regex-to-logs). They lack [data](/docs#access-logs---access) for HTTP protocol version and request method. |
| **Access** - HTTP v X | Hits with the specified HTTP network protocol [version](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Evolution_of_HTTP). One grouping for `2.0` and another for `1.0, 1.1` |
| **Access** - HTTP Xxx | Hits with the specified HTTP response [status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) grouping. see [Neat Reference](https://www.httpstatuses.org/) |
| <br> |<br> |
| **Error** - IP v X | Internet Protocol address [version](https://en.wikipedia.org/wiki/IP_address#IP_versions). `IPv4` or `IPv6` |
| **Error** - Filtrate | Outside hits with IPs not banned by fail2ban. Matches limited to one-week blocks. |
| **Error** - Level | All available Error Log [severity levels](https://en.wikipedia.org/wiki/Syslog#Severity_level) for entries are provided. [Parsed data info](/docs#error-log---error)  |
| <br> |<br> |
| **fail2ban** - Ignores | fail2ban entries with the "Ignore" [action](/docs#fail2ban-log---fail2ban). *I have fail2ban ignore my local, "Home IP", to allow me to tailor filters.*  |
| **fail2ban** - Match Ignores | Attempt to match fail2ban ignores with home hits on the access log. Home Ignorable [specification](/docs/Features/Report.md#home-ignorable) may improve matching. Same table as shown in [report](https://nbpub.github.io/BeatLog/#scrollspyHomeIgs). |
| **fail2ban** - Filter | query for each fail2ban filter |

</details>

### Results

Coordinates, Cities, and Counties are added to the Results table if any of the results have [location data](/docs#maxminddb). 
Unlike the report, the presented data is not styled in any way, providing a raw view of the database. 
Data styling is retained for ***Match Ignores***, however, which attempts to combine associated entries from 
the **[fail2ban](/docs#fail2ban-log---fail2ban)** and **[access](/docs#access-logs---access)** logs. 

If the there are more results than the size limit, the page provides a link to view more data. 

![dataview3](/docs/pics/query_3.png "Query result table (entire table not shown).") 

If the **Next** button is used, a **Previous** button is provided on the resulting page. 
This will only backtrack to its source page. 
For this reason, it may be beneficial to open **Next** results in a new tab or window.

The **SQL** statement used to generate the table can be viewed for each result. 

![dataview4](/docs/pics/query_4.png "If Next button used, a Previous button provides a link to one query back") 

Conveniently, it can be copied to the clipboard with a click.

![dataview5](/docs/pics/query_5.png "Copy SQL statement to clipboard") 
![dataview6](/docs/pics/query_6.png "Paste SQL statement somewhere") 

*This action may be disabled by web browser, [SSL certificate](https://github.com/FiloSottile/mkcert) may be required.*

## Database Cleanup

`*/data_cleaning/`

Data saved from log parsing can be deleted from the database, based on date.

![database_cleanup1](/docs/pics/database_cleanup1.png "Database cleanup page")

Data removal must be confirmed after estimation. Canceling will allow another estimate. 

![database_cleanup2](/docs/pics/database_cleanup2.png "Database cleanup - confirm deletion?")

## Failed Regex

`*/failed_regex/`

Any line that fails [parsing](/docs#parsing) will be saved and categorized according to log file. 
Currently, **BeatLog** provides limited interaction with the failed lines. You can clear a log's failed regex or view a sample of the failed lines.
I have not had any parsing failures using my [default regex methods](/docs#regex-methods), 
therefore I didn't specify a **Secondary** regex method to generate failed lines for an example.

*Individual log parsing result indicates failed lines, investigate on Failed Regex page:*

![failed_lines_1](/docs/pics/failed_lines_1.png "Log Parse result") ![failed_lines_2](/docs/pics/failed_lines_2.png "Failed Regex page shows logs with lines that failed to parse")
![failed_lines_3](/docs/pics/failed_lines_3.png "View up to 20 failed lines")

I have some ideas of things to add:
  - [Test Regex](/docs#adding-regex-to-logs) for log's failed lines
    - provide more detailed information on how/where regex failed
    - check **Time Skip** method only
  - Attempt to parse again and save into database
  - . . .
  
Please submit any parsing failures you encounter with the default methods and/or features you might want with the failed lines. 

