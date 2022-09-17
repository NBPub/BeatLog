from datetime import datetime, timedelta
import warnings

def init_tasks(check_IP, check_Log, scheduler):
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
                from .db_pool import pool
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        _, task_log = home_ip(conn,cur)
                        if task_log and type(task_log) == timedelta: 
                            scheduler.app.logger.info("Scheduled Home IP check complete")
                            # check if IP is ignored by Jail, would get IP instead of _ from home_ip                        
                        elif task_log:
                            scheduler.app.logger.error(f"Scheduled Home IP check error\n{task_log}")
                        else:
                            scheduler.app.logger.info("Scheduled Home IP check skipped")        
        if check_Log > 0:
            @scheduler.task(
                "interval",
                id="log_parse",
                hours=check_Log,
                start_date=(datetime.now()+timedelta(minutes=15)).isoformat(timespec='seconds').replace('T',' '),
            )
            def parse_task():
                """Parse Existing logs"""
                from .ops_parse import parse_all
                from .db_pool import pool
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        result = parse_all(conn,cur)
                        if result != {}:
                            task_log = ".".join([f'\n{key}: {val[0]}' for key,val in result.items()])
                        else:
                            task_log = "No logs parsed during scheduled task"
                scheduler.app.logger.info(task_log)

