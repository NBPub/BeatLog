# Simple JSON API

***Page updates in progress***

- [Motivation](#motivation)
- [API Help Page](#api-help-page)
- [Query Parameters](#api-query-parameters)
  - [Data Summary](#data-summary)
	- [home](#home)
	- [outside](#outside)
	- [fail2ban](#fail2ban)
	- [geo](#geo)
	- [*all*](#all)
  - [Bandwidth](#bandwidth)
    - [Syntax](#bandwidth-option-syntax)  
    - [Example Return](#example-bandwidth-return)
	- [Query Guide](#bandwidth-query-guide)
- [More to come?](#more)

## Motivation

Provide simple data retrieval from the database in JSON format. The API will *not* be comprehensive means of crafting SQL queries.<sup>1</sup>
The **[Report](/docs/Features/Report.md#contents)** and **[Database Explorer](/docs/Features/Database.md#database-explorer)**<sup>2</sup> cover 
more complex data retrievals I like to reference often.

<sup>1</sup>*As noted in the [installation extras](/docs/Installation/Installation_Extras.md#beatlog-installation-options), Adminer can provide a nice interface for running SQL commands against the database.*<br>
<sup>2</sup>*The code for Database Explorer, [db_query](/BeatLog/db_query.py) and [db_view](/BeatLog/db_view.py#L77), provides a good start for building SQL queries based on user inputs, if further development is desired.*

## API Help Page

`<your-base-URL>/api/help/`

**BeatLog** provides an API help page which provides links to all available API calls and the ability to preview their returns on the page itself. 
The available options will also be detailed on this page, with example returns provided and data types discussed. 

![API_1](/docs/pics/API_1.png "The API help page shows current options for the JSON API.")



# API Query Parameters

`<your-base-URL>/api/v1/<QUERY>/<OPTION>`

As shown in the images below, the [API Help Page](#api-help-page) will provide links for valid query parameters. 
Invalid queries should return a [422](https://www.httpstatuses.org/422) or [404](https://www.httpstatuses.org/404) response.

## Data Summary

`<your-base-URL>/api/v1/summary/<OPTION>`

The **Data Summary** options are meant to provide simple statistics from the last 24 hours, and are designed similarly to the [report](/docs/Features/Report.md#demonstration-page) sections.
It was the first API call added to **BeatLog** and is meant to be easily integrated in dashboard or notification systems. 
For example, I now keep tabs of [home ignores](#home) and [filtrate](#outside) on my homepage. 

![API_dash](/docs/pics/API_dash.png "Link to BeatLog on my homepage dashboard")

You could also create an alert if the current home IP address is not being ignored by [fail2ban](/docs#fail2ban-jail).


![API_2](/docs/pics/API_2.png "BeatLog API help page - Data Summary")

The following data types are returned for the **Data Summary** options:

- `string` - most items are strings, noted by quotation marks. `"<some-value>"` All keys are strings. Time format may vary from the examples, depending on your locale.
- `number` - simple integer, not encased in quotation markes. `3` OR `<some-integer>`
- `array` - "IP" and "ignored_IPs" keys are lists strings, and the [geo option](#geo) returns arrays of mixed data types. The values within arrays are encased in brackets and comma separated. `["Zhengzhou, China", 10]`

Note the structure of the various example returns shown below. 
`"time_bounds"` are included with every return.

<details><summary id="home"><b>home  +</b></summary>

`<your-base-URL>/api/v1/summary/home`

**Notes:**

 - "IP" will return array even if only one entry
 - "IP_duration" will return "All of time" if only one home IP in database, as shown on the [home page](/docs#parsing)
 - `"data"` will be `null` *(note, not string)*, if log data does not exist. Numbers will be `0`. IP information should still be returned.

```JSON
{
  "home": {
    "IP": [
      "192.168.1.1", "192.168.1.2"
    ],
    "IP_duration": "2 days, 4:22:38",
    "data": "212 MB",
    "error": 3,
    "ignores": 0,
    "total": 933
  },
  "time_bounds": {
    "end": "02/12/23 23:29:17",
    "start": "02/11/23 23:29:17"
  }
}
```
</details>

<details><summary id="outside"><b>outside  +</b></summary>

`<your-base-URL>/api/v1/summary/outside`

**Notes:**

 - The following are unique IPs, not total connections
   - "banned" outside IPs from fail2ban with  `action=Ban`
   - "filtrate" outside IPs from access and error logs that aren't banned by fail2ban
   - "known_visitors" outside IPs from access log that are [known devices](/docs/Features/Report.md#known-devices), ***only present if Known Devices specified in settings***
   - "visitors" outside IPs from access and error logs
 - `"data"` will be `null` (note, not string), if log data does not exist. Numbers will be `0`

```JSON
{
  "outside": {
    "banned": 29,
    "data": "40 kB",
    "error": 8,
    "filtrate": 0,
    "known_visitors": 2,
    "total": 50,
    "visitors": 31
  },
  "time_bounds": {
    "end": "02/12/23 23:29:17",
    "start": "02/11/23 23:29:17"
  }
}
```
</details>

<details><summary id="fail2ban"><b>fail2ban +</b></summary>

`<your-base-URL>/api/v1/summary/fail2ban`

**Notes:**

 - "ignored_IPs" will return array even if only one entry
 - empty return `"fail2ban":{}` provided if [jail.local](/docs#fail2ban-jail) is not established.

```JSON
{
  "fail2ban": {
    "Bans": {
      "nginx-crit-err": 1,
      "nginx-noscript": 13
    },
    "Finds": {
      "nginx-crit-err": 1,
      "nginx-noscript": 14
    },
    "Ignores": {},
    "enabled_filters": [
      "nginx-noscript",
      "nginx-crit-err"
    ],
    "ignored_IPs": [
      "<IP_1>",
      "192.168.0.0/16"
    ]
  },
  "time_bounds": {
    "end": "02/12/23 23:29:17",
    "start": "02/11/23 23:29:17"
  }
}
```
</details>

<details><summary id="geo"><b>geo  +</b></summary>

`<your-base-URL>/api/v1/summary/geo`

**Notes:**

 - "top_hits" and "top_visitors" provide an array of `["<City, Country>", <relevant number>]`
 - empty return `"geo":{}` provided if no locations exist 
   - Enable [MaxMind](/docs#maxminddb) to add locations to IP addresses.

```JSON
{
  "geo": {
    "locations": 45,
    "top hits": [
      "Zhengzhou, China",
      10
    ],
    "top visitors": [
      "Zhengzhou, China",
      3
    ]
  },
  "time_bounds": {
    "end": "02/12/23 23:29:17",
    "start": "02/11/23 23:29:17"
  }
}
```
</details>

<details><summary id="all"><b>all +</b></summary>

`<your-base-URL>/api/v1/summary/all`

**Notes:**

 - All above options combined
 - `"time_bounds"` are the same for each group

```JSON
{
  "fail2ban": {
...see above...
  },
  "geo": {
...see above...
  },
  "home": {
...see above...
  },
  "outside": {
...see above...
  },
  "time_bounds": {
...see above...
  }
}
```
</details>

## Bandwidth

`<your-base-URL>/api/v1/bandwidth/<OPTION>`

The **Bandwidth** query returns data transfer statistics from the [Access Log table](/docs#access-logs---access) in the database. 
The keys and their data types are listed below. If a valid query returns 0 hits, data values will be <em>`null`</em> instead of their listed *type*.
 
- `"bytes"` - sum of raw bytes, as stored in the database. *number*
- `"hits"` - number of connections (rows) returned by the query. *number*
- `"data"` - [human readable](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADMIN-DBSIZE) format of bytes. *string*
- `"data_per_hit"` - human readable format of bytes divided by hits *string*
- `"query"` - *JSON object* desribing query. Contains: 
	- "field" and "value" keys 
	- possible "time_bounds" *object* containing "start" and "end" keys. See more [below](#bandwidth-option-syntax).

![API_3](/docs/pics/API_3.png "BeatLog API help page - Bandwidth")

### Bandwidth Option Syntax

  - **Required filter:** `<FIELD>=<VALUE>`<br>`<FIELD>` must be a valid column (capitalization is ignored). `<VALUE>` may be anything to match to the field. Values for some fields must be a specific data type.
    - Review the [documentation](/docs#access-logs---access) for valid fields and and their data types. Valid data types are also listed in the [query guide](#bandwidth-query-guide) below.
	- If `<VALUE>` is `None`, it will be interpreted as `NULL` for the SQL query. 
	  - `url=None` as a query option would translate to `WHERE url IS NULL` *vs.* `url=/` *which would translate to* `WHERE url='/'`
    - For the **URL**, **referrer**, and **tech** fields, pattern matching can be employed. The SQL query will use `<FIELD> LIKE <VALLUE>` instead of `<FIELD> = <VALLUE>`
	  - To enable, include at least one `%` in the `<VALUE>`. A value cannot only be `%`
	  - Escapse a `%` meant to be taken literally by adding a backslash before it `\%`
	  - See more: [PostgreSQL documentation](https://www.postgresql.org/docs/current/functions-matching.html#FUNCTIONS-LIKE)
 <br>
 
 - **Optional date filter:** `date=<START>-<END>,. . . `<br>`<START>` and `<END>` must be [UNIX timestamps](https://unixtime.org/) with one second resolution (10 digit integer).
    - `<START>` and `<END>` must be separated by a dash. Date specification and field/value pairs must be comma separated.<br>*as shown above*
    - If date is specified, it must come before the field/value pair.
    - Times will be converted to your timezone, if [configured](/README.md#parameters) (as done with parsed data).
	- Specifying `<START>` greater than or equal to `<END>` ensures an empty result

<details><summary id="example-bandwidth-return"><b>example call and return</b></summary>

`<your-base-URL>/api/v1/bandwidth/date=1676613051-1676699451,referrer=%http://%`

**Notes:**

 - Optional date filter used, so it comes first in the query
   - If date was not specified, `"time_bounds"` would not be returned within the `"query"` *object*
 - The value for **referrer** contains at least one `%`, so pattern matching is used
   - `%http://%` means any referrer that contains the text `http://`


```JSON
{
  "bandwidth": {
    "bytes": 1312,
    "data": "1312 bytes",
    "data_per_hit": "328 bytes",
    "hits": 4,
    "query": {
      "field": "referrer",
      "time_bounds": {
        "end": "02/18/23 22:28:53",
        "start": "02/17/23 22:28:53"
      },
      "value": "%http://%"
    }
  }
}
```
</details>

### Bandwidth Query Guide

`<FIELD>=<VALUE>`

As mentioned, the capitalization of the speficied field does not matter. 
Links to PostgreSQL documentation are provided, when applicable.

| Field | Example Query | Guidance for Values |
| :----: | --- | --- |
| **date** | `date=1676613051-1676699451,` | *discussed above, must be formatted as UNIX timestamps with appropriate delimiters* |
| **IP** | `ip=192.168.1.1` | must be an [IP address](https://www.postgresql.org/docs/current/datatype-net-types.html#DATATYPE-INET) |
| **home** | `home=1` OR `home=False` | must be a [boolean](https://www.postgresql.org/docs/current/datatype-boolean.html) |
| **Method** | `method=PUT` SAME AS `method=put` | automatically converted to all upper case to match database |
| **URL** | `url=/robots.txt` OR `url=/%` | pattern matching available. 2nd example:<br>*starts with "/"* |
| **HTTP** | `http=20` | must be an [integer](https://www.postgresql.org/docs/current/datatype-numeric.html#DATATYPE-INT), note that HTTP version is multipled by 10 in the database |
| **Status** | `status=200` | must be an integer, [HTTP status code reference](https://www.httpstatuses.org/) |
| **Bytes** | `bytes=250` | must be an integer, seems silly to use this as a filter. Have at it! |
| **Referrer** | `referrer=https://www.google.com/` OR `referrer=%google%` | pattern matching available. 2nd example:<br>*contains "google"*  |
| **Tech** | `tech=Mozilla/5.0 zgrab/0.x` OR `tech=%iOS%` | pattern matching available. 2nd example:<br>*contains "iOS"*  |
| **Geo** | `geo=22` | must be an integer. Currently matches the rowid on the [geography table](/docs#geography-table---geoinfo). May be further developed to make matching more human friendly. |

Still not sure about Field/Value pairs? The **Top 10 Tables** in the [BeatLog report](/docs/Features/Report.md#outside-demo) are a good place to start. 
You can query the most popular values for a `<FIELD>` from the entire database with the following SQL:

```sql
SELECT <FIELD>, COUNT(*) FROM access 
WHERE home=False # optional, only outside connections
GROUP BY <FIELD>
ORDER BY COUNT DESC 
LIMIT 10
```


## More?

Submit an [issue](https://github.com/NBPub/BeatLog/issues/new) if you have ideas for API calls.

 * **Parsing Check** - show time difference between last modified and last parsed for each log
 * **fail2ban Jail Check** - update fail2ban jail if changed or return that it's up to date
 * **geo Check** - count of unnamed locations and locations without an associated IP address
 * **Log Parse** - parse log if modified since last parse
 * **geo Fill** - attempt to name unnamed locations, if present
 * **geo list** - provide list of all geo data `SELECT DISTINCT geo FROM access WHERE geo IS NOT NULL ORDER BY geo`