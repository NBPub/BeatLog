# Simple JSON API

- [Motivation](#motivation)
- [API Help Page](#api-help-page)
- [Query Parameters](#data-options)
  - [Data Summary](#summary)
	- [home](#home)
	- [outside](#outside)
	- [fail2ban](#fail2ban)
	- [geo](#geo)
	- [*all*](#all)
  - [Bandwidth](#bandwidth)
	- [examples](#bandwidth-examples)
- [More to come?](#more)

## Motivation

***PAGE UPDATES IN PROGRESS, information may not match either "current" or "latest" tag***

<details><summary>Initial</summary>

*Tackle [Issue 1](https://github.com/NBPub/BeatLog/issues/1)*!

Over the course of developing an API for easy data retrieval, I decided I didn't want it to be a tool or replacement for crafting SQL queries. 
I think **BeatLog** is mostly meant\* to parse log data into a database to make it easily accessible. 
The **[Report](/docs#report-demo)** and **[Database Explorer](/docs#database-explorer)**\*\* cover presentations of the data in ways I like to see.

All this to say, I designed the API to return simple data summaries from the past 24 hours. 
In this way, it can be easily used in dashboard or alert systems. 
I'll probably keep tabs of [home ignores](#home) and [filtrate](#outside) on my homepage, for example.

\**As noted in the [installation options](/README.md#extra-options), Adminer can provide a nice interface for running SQL commands against the database.*

\*\**The code, [db_query](/BeatLog/db_query.py) and [db_view](/BeatLog/db_view.py#L77), for Database Explorer query creation provides a good start for building SQL queries based on user inputs.*
</details>

## API Help Page

`<your-base-URL>/api/help/`

**BeatLog** provides an API help page which provides links to all available options and the ability to preview returns. 
The various options will be detailed on this page, with example returns provided. 

![API_1](/docs/pics/API_1.png "The API help page shows current options for the JSON API.")



# Query Parameters

As shown in the image, the [API Help Page](#api-help-page) will provide links to the various options, which follow the scheme: `<your-base-URL>/api/v1/<QUERY>/<OPTION>`. 
Invalid queries will return a [422](https://www.httpstatuses.org/422) response.

## Data Summary

intro, data summary for past 24 hours

```
I designed the API to return simple data summaries from the past 24 hours. 
In this way, it can be easily used in dashboard or alert systems. 
I'll probably keep tabs of [home ignores](#home) and [filtrate](#outside) on my homepage, for example.
```

![API_2](/docs/pics/API_2.png "...")

The following datatypes are returned:

- `string` - most items are strings, noted by quotation marks. `"212 MB` All keys are strings. Times may vary from the example, depending on your locale.
- `number` - simple integer, not encased in quotation markes. `3`
- `array` - IP lists, and the [geo]() returns provide arrays (mix of above). They are encased in brackets and items are comma separated. `["Zhengzhou, China", 10]

Note the structure of the various returns shown below. `"time_bounds"` are included with every return.


<details><summary id="home"><b>home</b></summary>

**Notes:**

 - "IP" will return array even if one entry
 - "IP_duration" will return "All of time" if only one homeIP in database, as shown on the [home page](/docs#parsing)
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

<details><summary id="outside"><b>outside</b></summary>

**Notes:**

 - The following are unique IPs, not total
   - "banned"
   - "filtrate" *outside IPs from access log that aren't banned*
   - "known_visitors" *outside IPs from access log that are [known devices](/docs#known-devices)*, ***only present if Known Devices specified in settings***
   - "visitors" *outside IPs from access and error logs*
 - `"data"` will be `null` *(note, not string)*, if log data does not exist. Numbers will be `0`

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

<details><summary id="fail2ban"><b>fail2ban</b></summary>

**Notes:**

 - "ignored_IPs" will return array even if one entry
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

<details><summary id="geo"><b>geo</b></summary>

**Notes:**

 - "top_hits" and "top_visitors" provide an array of `["<location>", <integer>]`
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

<details><summary id="all"><b>all</b></summary>

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

intro, discuss options

![API_3](/docs/pics/API_3.png "...")

Describe data

- `string` - most items are strings, noted by quotation marks. `"212 MB` Everything but `bytes`
- `number` - simple integer, not encased in quotation markes. `3`
- `array` - IP lists, and the [geo]() returns provide arrays (mix of above). They are encased in brackets and items are comma separated. `["Zhengzhou, China", 10]

example return
```JSON
{
  "bandwidth": {
    "bytes": 251967,
    "hits": 829,
    "data_per_hit": "303 bytes",
    "data": "246 kB",
    "query": {
      "field": "http",
      "value": "10"
    }
  }
}
```

### Examples

List some examples

<details><summary>═════════</summary>

Stuff

</details>



## More?

submit issue link

 * **Parsing Check** - show time difference between last modified and last parsed for each log
 * **fail2ban Jail Check** - update fail2ban jail if changed or return that it's up to date
 * **geo Check** - count of unnamed locations and locations without an associated IP address
 * **Log Parse** - parse log if modified since last parse
 * **geo Fill** - attempt to name unnamed locations, if present