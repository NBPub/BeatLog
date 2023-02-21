## Background

***psycogp3** [ConnectionPool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#connection-pools) vs. [NullConnectionPool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#null-connection-pools)*

BeatLog [alpha-0.1.3](https://github.com/NBPub/BeatLog/releases/tag/alpha-0.1.3) and prior had alternate versions using a NullConnectionPool, due to early issues implementing the ConnectionPool. 
These issues have been resolved, and alternative versions of BeatLog utilizing a NullConnectionPool will not be provided.
This page shows the previous changes used for the alternate versions.

## Code

The following changes will provide a NullConnectionPool:

### __init__.py

[File](/BeatLog/__init__.py)

**Changes**: errorhandler for 500 status returns should not do a poolcheck. Remove poolcheck and provide a simple error message.

```python
@app.errorhandler(500)
def error_page(e):
	# pool checks not performed for NullConnectionPool, simple message below
	message = ['Probable database connection error. Apologies for the convenience, retry attempt or restart container.', 'danger']
	
	# remove/comment lines until . . .
	
	return render_template('app_error500.html', e=e, message=message), 500      
```

### db_pool.py

[File](/BeatLog/db_pool.py)

**Changes**: Utilize NullConnection Pool instead of connection pool. Replace contents with code below.

```python
from .db import conninfo # connection parameters

# NullConnection pool, https://www.psycopg.org/psycopg3/docs/advanced/pool.html#null-connection-pools
# behaves as if a new database connection is created and returned with each request

from psycopg_pool import NullConnectionPool
pool = NullConnectionPool(conninfo)   
```

### home.py

[File](/BeatLog/home.py)

**Changes**: Remove poolcheck before each app request. Remove / comment code below.

```python
@bp.before_app_request
def pool_check(): # function should not be used for NullConnectionPool
    if pool._closed:
        pool.open() # open on first request
        pool.check() # check to populate pool
    pool.check() # check to clean pool     
```

## Connection Pool Logging

Check on the (Null)ConnectionPool status in the application's logs. Add to top of [create_app](/BeatLog/__init__.py) function.

```python
# pool logging for development
try: 
    pool_logger = logging.getLogger("psycopg.pool")
    pool_logger.setLevel(logging.INFO)
    pool_logger.handlers = app.logger.handlers
    app.logger = pool_logger
except Exception as e:
    app.logger.info(f'Error with pool logging, {e}')
```

See [ConnectionPool class](https://github.com/psycopg/psycopg/blob/master/psycopg_pool/psycopg_pool/pool.py) for details.