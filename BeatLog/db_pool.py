from .db import conninfo # connection parameters

# ConnectionPool, open after Gunicorn fork
# each worker uses their own pool

from psycopg_pool import ConnectionPool
pool = ConnectionPool(conninfo,timeout=15,min_size=3,max_size=5,open=False)  

# NullConnection pool, https://www.psycopg.org/psycopg3/docs/advanced/pool.html#null-connection-pools
# behaves as if a new database connection is created and returned with each request

# from psycopg_pool import NullConnectionPool
# pool = NullConnectionPool(conninfo)