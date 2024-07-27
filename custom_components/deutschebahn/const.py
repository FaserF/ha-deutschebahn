"""German Train System - Deutsche Bahn"""
DOMAIN = "deutschebahn"
ATTRIBUTION = "Data provided by bahn.de api"

CONF_DESTINATION = "destination"
CONF_START = "start"
CONF_OFFSET = "offset"
CONF_ONLY_DIRECT = "only_direct"
CONF_MAX_CONNECTIONS = "max_connections"
CONF_UPDATE_INTERVAL = "scan_interval"
CONF_IGNORED_PRODUCTS = "ignored_products"
CONF_IGNORED_PRODUCTS_OPTIONS = {
    "BUS": "Busverkehr (BUS)",
    "STR": "Straßenbahn (STR)",
    "S": "Stadtbahn (S-Bahn)",
    "RE": "Regional Express (RE)",
    "RB": "Regional Bahn (RB)",
    "EC": "EuroCity (EC)",
    "IC": "Intercity (IC)",
    "ICE": "Intercity Express (ICE)",
    "TGV": "Train à grande vitesse (TGV)",
    "EST": "LGV Est européenne",
}
ATTR_DATA = "data"
