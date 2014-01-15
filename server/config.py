import json
import optparse

class ConfigException(Exception):
    pass

class Config:
    def __init__(self):
        self.pidFile = None
        self.user = None
        self.group = None
        self.dnsBind = None
        self.dnsPort = None
        self.updateBind = None
        self.updatePort = None
        self.catalog = None

        self.parseCmdLine()
        self.parseConfigFile()

    def parseCmdLine(self):
        parser = optparse.OptionParser()
        parser.add_option("-c", "--config", help="config file")
        options, args = parser.parse_args()

        self.configFile = options.config
        if self.configFile is None:
            parser.print_help()
            parser.exit()

    def parseConfigFile(self):
        f = open(self.configFile, "r")
        try:
            data = json.load(f)
        except ValueError, e:
            raise ConfigException("Parsing config file to JSON failed (%s)" % str(e))

        self.pidFile = data.get("pid_file")
        self.user = data.get("user", "nobody")
        self.group = data.get("group", "nogroup")
        self.dnsBind = data.get("dns_bind", "0.0.0.0")
        self.dnsPort = data.get("dns_port", 53)
        self.updateBind = data.get("update_bind", "0.0.0.0")
        self.updatePort = data.get("update_port", 7331)
        self.catalog = data.get("catalog")

        if self.catalog is None or len(self.catalog.keys()) == 0:
            raise ConfigException("Catalog not given or empty")
