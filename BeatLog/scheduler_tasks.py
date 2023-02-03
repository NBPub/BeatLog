from datetime import datetime, timedelta
import warnings
import psycopg

def init_tasks(check_IP, check_Log, scheduler, conninfo):    
    with warnings.catch_warnings(): # (see:) from pytz_deprecation_shim import PytzUsageWarning
        warnings.simplefilter("ignore", category=RuntimeWarning)
        if check_IP > 0:
            @scheduler.task(
                "interval",
                id="home_ip",
                hours=check_IP,
                start_date=(datetime.now()+timedelta(seconds=30)).isoformat(timespec='seconds').replace('T',' '),
            )
            def homeIP_task():
                """Check home IP"""
                from .ops_log import home_ip
                try:
                    with psycopg.connect(conninfo) as conn:
                        cur = conn.cursor()
                        _, task_log = home_ip(conn,cur) # return duration as timedelta, error as string, or None (first entry / no change to first)
                        if task_log and type(task_log) == str:
                            scheduler.app.logger.error(f"Scheduled Home IP check error\n{task_log}")                                         
                        else:
                            scheduler.app.logger.info("Scheduled Home IP check complete")
                except Exception as e:
                    scheduler.app.logger.info(f'Scheduled Home IP check error: {str(e)}')    
        if check_Log > 0:
            @scheduler.task(
                "interval",
                id="log_parse",
                hours=check_Log,
                start_date=(datetime.now()+timedelta(minutes=15)).isoformat(timespec='seconds').replace('T',' '),
            )
            def parse_task():
                """Parse Existing logs, fill geo as needed"""
                from .ops_parse import parse_all
                from .ops_geo import location_fill
                try:
                    with psycopg.connect(conninfo) as conn:
                        cur = conn.cursor()
                        result = parse_all(conn,cur)
                        if result != {}:
                            task_log = ".".join([f'\n{key}: {val[0]}' for key,val in result.items()])
                        else:
                            task_log = "No logs parsed during scheduled task"
                        scheduler.app.logger.info(f'Scheduled Log check complete {task_log}')
                        # Geo Fill
                        indicator, result = location_fill(conn,cur)
                        if indicator[1] != 'warning':
                            scheduler.app.logger.info(f'\tLocation Fill: {indicator[0]}')
                        if result != []:
                            scheduler.app.logger.info('.  '.join(result))   
                except Exception as e:
                    scheduler.app.logger.info(f'Scheduled Log check error: {str(e)}')

