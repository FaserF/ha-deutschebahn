"""German Train System - Deutsche Bahn"""
DOMAIN = "deutschebahn"
ATTRIBUTION = "Data provided by bahn.de api"

CONF_DESTINATION = "destination"
CONF_START = "start"
CONF_OFFSET = "offset"
CONF_ONLY_DIRECT = "only_direct"
CONF_MAX_CONNECTIONS = "maximum count of connections that will be fetched"
CONF_UPDATE_INTERVAL = "refresh time in seconds"
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
