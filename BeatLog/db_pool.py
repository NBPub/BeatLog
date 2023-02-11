from .db import conninfo # connection parameters

# ConnectionPool, open after Gunicorn fork
# each worker uses their own pool, see also: https://www.psycopg.org/psycopg3/docs/advanced/pool.html#null-connection-pools

from psycopg_pool import ConnectionPool
pool = ConnectionPool(conninfo,timeout=15,min_size=3,max_size=5,open=False)  