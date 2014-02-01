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
        self.httpUpdateBind = None
        self.httpUpdatePort = None
        self.cacheFile = None
        self.catalog = {}

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
        self.user = data.get("user")
        self.group = data.get("group")
        self.dnsBind = data.get("dns_bind", "0.0.0.0")
        self.dnsPort = data.get("dns_port", 53)
        self.updateBind = data.get("update_bind", "0.0.0.0")
        self.updatePort = data.get("update_port", 7331)
        self.httpUpdateBind = data.get("http_update_bind", self.updateBind)
        self.httpUpdatePort = data.get("http_update_port", 8000)
        self.cacheFile = data.get("cache_file", "/tmp/mpddns.cache")
        catalog = data.get("catalog")

        if catalog is None:
            raise ConfigException("No catalog given")

        if not isinstance(catalog, dict):
            raise ConfigException("Catalog is not of JSON-type 'object'")

        if not len(catalog):
            raise ConfigException("Catalog is empty")
        
        for domain, config in catalog.iteritems():
            if not isinstance(config, dict):
                raise ConfigException("Configuration for domain '%s' is not of JSON-type 'object'" % domain)
            password = config.get("password")
            if password is None or not len(password):
                raise ConfigException("No password for domain '%s' given" % domain)

            self.catalog[domain.lower()] = config
