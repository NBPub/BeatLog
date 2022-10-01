from pathlib import Path
from datetime import datetime
import re
from configparser import ConfigParser

class LogFile:
    def __init__(self, location):
        self.location = Path(location)
        self.name = self.location.stem
        self.modified = datetime.fromtimestamp(self.location.stat().st_mtime)
        self.lastParsed = [datetime(1,1,1), self.modified] # timestamps of (last line parsed, log modified)   
        
class RegexMethod:
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.groups = list(self.pattern.groupindex)

class Jail:
    def __init__(self, location):
        self.location = Path(location)
        self.modified = datetime.fromtimestamp(self.location.stat().st_mtime)
        self.update_status()
        
    def update_status(self):
        # read file at location
        config = ConfigParser()
        config.read(self.location)       
        # ignoreIP(s)
        self.ignoreIP = config.get('DEFAULT','ignoreip').split(',')
        self.ignoreIP = [val.replace(' ','') for val in self.ignoreIP]
        # store enabled filters as dictionary[], json will be dumped into db
        filters = []     
        for jail in config.sections():
            if jail == 'ssh':
                continue
            if config.getboolean(jail, 'enabled') == True:
                filters.append({
                    'name': jail, 
                    'log': Path(config.get(jail, 'logpath')).name.replace('.log',''),
                    'retry': config.getint(jail, 'maxretry')
                    })
        self.enabled_filters = {'enabled': filters}           
        del config           
