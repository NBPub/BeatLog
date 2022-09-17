# Connect to DB, open pool for future connections, return error on failure
def db_connect(host, user, pw, db, port):
    conninfo = f"host={host} dbname={db} port={port} user={user} password={pw}"    
    try:
        import psycopg
        with psycopg.connect(conninfo) as conn:
            make_tables(conn)
        from .db_pool import pool
        pool.open()
    except Exception as e:
        return str(e)    
    return False

# Table Initialization
def make_tables(conn):
    with conn.cursor() as cur:
        # Regex Methods
        cur.execute("""CREATE TABLE IF NOT EXISTS regex_methods (
                        name VARCHAR PRIMARY KEY,
                        pattern text NOT NULL,
                        groups text[] NOT NULL)
                    """)                  
        # Log Files            
        cur.execute("""CREATE TABLE IF NOT EXISTS logfiles (
                        Location text NOT NULL,
                        Name VARCHAR(12) PRIMARY KEY,
                        Modified timestamp,
                        lastParsed timestamp[1][2],
                        regex_1 text REFERENCES regex_methods ON DELETE SET NULL,
                        regex_2 text REFERENCES regex_methods ON DELETE SET NULL,
                        regex_time text REFERENCES regex_methods ON DELETE SET NULL)
                    """)       
        # Home IP History
        cur.execute("""CREATE TABLE IF NOT EXISTS homeIP (
                        row serial,
                        IP inet NOT NULL,
                        Date timestamp NOT NULL,
                        duration interval)
                    """)                 
        # f2b Jail for active filters
        cur.execute("""CREATE TABLE IF NOT EXISTS jail (
                        Location text NOT NULL,
                        Date timestamp NOT NULL,
                        lastcheck timestamp NOT NULL,
                        filters jsonb,
                        ignoreIPs text[])
                    """)      
        # Report and Geography Settings, initialize if not exists
        cur.execute("""CREATE TABLE IF NOT EXISTS settings (
                        ReportDays smallint DEFAULT 3,
                        HomeIgnores text,
                        KnownDevices text,
                        KD_visit boolean DEFAULT FALSE,
                        KD_frequent boolean DEFAULT FALSE,
                        KD_data boolean DEFAULT FALSE,
                        KD_refurl boolean DEFAULT FALSE,
                        KD_loc boolean DEFAULT FALSE,
                        LocationTable boolean DEFAULT FALSE,
                        MaxMindDB text,
                        MapDays smallint DEFAULT 3,
                        MapCount boolean DEFAULT FALSE,
                        NominatimAgent text)
                    """)  
        if not cur.execute('SELECT * FROM settings').fetchone():
            cur.execute('INSERT INTO settings (knowndevices,homeignores, maxminddb,\
                                nominatimagent) VALUES (%s,%s,%s,%s)', (None,)*4)        
        # Storage of Location Coordinates / Names
        cur.execute("""CREATE TABLE IF NOT EXISTS geoinfo (
                        id serial PRIMARY KEY,
                        coords integer[1][2] NOT NULL,
                        city text,
                        country text)
                    """)   
        # Tables for historical logs, regex failures
        cur.execute("""CREATE TABLE IF NOT EXISTS access (
                        Date timestamp NOT NULL,
                        IP inet,
                        Home boolean,
                        Method VARCHAR(8),
                        URL text,
                        http smallint,
                        Status smallint,
                        Bytes integer,
                        Referrer text,
                        Tech text,
                        geo smallint REFERENCES geoinfo ON DELETE SET NULL)
                    """)
        cur.execute("""CREATE TABLE IF NOT EXISTS error (
                        Date timestamp NOT NULL,
                        IP inet,
                        Home boolean,
                        Level VARCHAR(6),
                        Message text,
                        geo smallint REFERENCES geoinfo ON DELETE SET NULL)
                    """)  
        cur.execute("""CREATE TABLE IF NOT EXISTS fail2ban (
                        Date timestamp NOT NULL,
                        IP inet,
                        Home boolean,
                        Filter text,
                        Action VARCHAR(10),
                        geo smallint REFERENCES geoinfo ON DELETE SET NULL)
                    """)
        cur.execute("""CREATE TABLE IF NOT EXISTS unauthorized (LIKE access)
                    """)  
        cur.execute("""CREATE TABLE IF NOT EXISTS failedregex (
                        line text,
                        log VARCHAR(12) REFERENCES logfiles ON DELETE CASCADE)
                    """)      
    return
    