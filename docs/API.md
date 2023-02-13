## Motivation

Simple retrieval of summary data

not meant to be a replacement/method for running custom SQL queries to database, should just do that instead

(that being said, db_query code is good start for that vision)

## API Help Page

`<your-base-URL>/api/help/

![API_1](/docs/pics/API_1.png "The API help page shows current options for the JSON API.")

## Data Options

stuff about options, invalid spec will give 422 return

### home

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

### outside

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


### fail2ban

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

### geo

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

### all

```JSON
{
  "fail2ban": {
...
  },
  "geo": {
...
  },
  "home": {
...
  },
  "outside": {
...
  },
  "time_bounds": {
    "end": "02/12/23 23:29:17",
    "start": "02/11/23 23:29:17"
  }
}
```

## More?

submit issue link

 * **Parsing Check** - show time difference between last modified and last parsed for each log
 * **fail2ban Jail Check** - update fail2ban jail if changed or return that it's up to date
 * **geo Check** - count of unnamed locations and locations without an associated IP address
 * **Log Parse** - parse log if modified since last parse
 * **geo Fill** - attempt to name unnamed locations, if present