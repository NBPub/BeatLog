from os import getenv
from psycopg_pool import ConnectionPool
pool = ConnectionPool(f"host={getenv('db_host', 'localhost')} \
    dbname={getenv('db_database', 'beatlog')} port={getenv('db_port', '5432')} \
    user={getenv('db_user', 'beatlog')} password={getenv('db_password')}", 
    open=False)  