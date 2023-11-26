"""German Train System - Deutsche Bahn"""
DOMAIN = "deutschebahn"
ATTRIBUTION = "Data provided by bahn.de api"

CONF_DESTINATION = "destination"
CONF_START = "start"
CONF_OFFSET = "offset"
CONF_ONLY_DIRECT = "only_direct"
CONF_MAX_CONNECTIONS = "max_connections"
CONF_IGNORED_PRODUCTS = "ignored_products"
CONF_IGNORED_PRODUCTS_OPTIONS = {
    "STR": "Straßenbahn (STR)",
    "S": "Stadtbahn (S-Bahn)",
    "RE": "Regional Express (RE)",
    "RB": "Regional Bahn (RB)",
    "EC": "EuroCity (EC)",
    "IC": "Intercity (IC)",
    "ICE": "Intercity Express (ICE)",
    "TVG": "Train à grande vitesse (TVG)",
}
ATTR_DATA = "data"
