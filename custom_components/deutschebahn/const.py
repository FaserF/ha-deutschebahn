"""German Train System - Deutsche Bahn"""
from datetime import timedelta

DOMAIN = "deutschebahn"
ATTRIBUTION = "Data provided by bahn.de api"

CONF_DESTINATION = "to"
CONF_START = "from"
CONF_OFFSET = "offset"
CONF_ONLY_DIRECT = "only_direct"

DEFAULT_OFFSET = timedelta(minutes=0)
DEFAULT_ONLY_DIRECT = False