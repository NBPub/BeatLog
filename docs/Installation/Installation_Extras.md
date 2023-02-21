# BeatLog Installation Options

 - [Healthchecks](#healthchecks)
   - [BeatLog](#beatlog)
   - [PostgreSQL](#postgresql)
 - [Adminer](#adminer)
 - [Updating PostgreSQL](#postgresql-updates)
 - [Get Inside BeateLog](#inside-beatlog)
 
 **[Installation Basics](/README.md#installation)**
 
 ## Healthchecks
 
Add [healthcheck(s)](https://docs.docker.com/engine/reference/builder/#healthcheck) to indicate container status.

![Healthcheck](/docs/pics/healthy_checks.png "Happy, healthy BeatLog and PostgreSQL database.")

### BeatLog

*The port number,* `8000` *should match the container's [internal port](/README.md#parameters).*

```yaml
  beatlog:
    image: nbpub/beatlog:stable
    healthcheck:
      test: curl -I --fail http://localhost:8000 || exit 1
      interval: 300s
      timeout: 10s
      start_period: 20s
    .
    .
    .
```

### PostgreSQL

*The user,* `beatlog` *should match the* `POSTGRES_USER` *[specified](/README.md#docker-compose).*

```yaml
  db:
    image: postgres:15
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "beatlog"]
      interval: 300s
      start_period: 30s
```

## Adminer

Add an [Adminer](https://www.adminer.org/) container to interact with your database. Database adjustments outside **BeatLog** are *not* supported and could break functionality. 

![Adminer](/docs/pics/adminer.png "BeatLog tables, viewed in Adminer")

*Visit* `<server>:<adminer-port>` *and login to the postgresql database to view tables and data.*

```yaml
  adminer:
    image: adminer
    container_name: beatlog_mgmt	
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - <adminer-port>:8080
  db:
    .
    .
    .

```

## PostgreSQL Updates

**BeatLog** should work well with PostgreSQL 14 and 15. I have not tested previous versions. 
As mentioned in [basic installation parameters](/README.md#parameters), if the database data is 
[mounted](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata) to a Docker [volume](https://docs.docker.com/storage/volumes/), 
then upgrading should be as easy as deleting the old image and recreating a new container with the same volume. 
Release logs for PostgreSQL should be checked for any breaking changes.

If the volume was not mounted, upgrading PostgreSQL may erase existing data. In this case, data can be transferred from PostgreSQL containers. 
See **[Migration Between Releases](https://www.postgresql.org/docs/9.0/migration.html)** for more info, and also: 
 * [docker exec](https://docs.docker.com/engine/reference/commandline/exec/)
 * [pg_dumpall](https://www.postgresql.org/docs/current/app-pg-dumpall.html)
 * [docker cp](https://docs.docker.com/engine/reference/commandline/cp/)

The following shows how to manually copy existing database data to a new container. After following these steps, update the container information as needed in the **BeatLog** environment and restart.


```bash
# 1. enter existing container "beatlog_db"
docker exec -it beatlog_db /bin/bash

# 2. pg_dumpall into convenient directory, exit container
cd home
pg_dumpall -U beatlog > db.out
exit

# 3. copy to local directory, then into new database container "beatlog_db_NEW"
docker cp beatlog_db:/home/db.out  /path/of/choosing
docker cp /path/of/choosing/db.out  beatlog_db_NEW:/home

# 4. enter new container and execute script
docker exec -it beatlog_NEW /bin/bash
psql -f db.out -U beatlog postgres
 ```


## Inside BeatLog

Explore **BeatLog** container using [docker exec](https://docs.docker.com/engine/reference/commandline/exec/), for example, investigate Python environment:

```shell
# 1. enter existing container "beatlog"
docker exec -it beatlog /bin/sh

# 2. pip freeze to view installed packages and versions
python -m pip freeze
```

. . . Or [edit](https://en.wikipedia.org/wiki/Vi) **BeatLog's** [code](/BeatLog), and then restart the container to reflect changes:

```shell
docker exec -it beatlog /bin/sh

cd beatlog
ls # list files
vi <filname>.py # open in text editor

# edit HTML template
cd templates
vi <filename>.html
```

**vi Resources**

*alternative text editors can be installed in the container, if desired. see [alpine Linux packages](https://pkgs.alpinelinux.org/packages)*

[Colorado State University CS Dept.](https://www.cs.colostate.edu/helpdocs/vi.html)

[UITS](https://kb.iu.edu/d/adxz)
