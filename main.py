'''
sentinel-2 downloader
Created by: Pooja Prajith
'''

import requests 
import os
from datetime import datetime, timedelta
from config import CLIENT_ID, CLIENT_SECRET

# Store lient id and client secret
CREDENTIALS = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET 
}

# Location, lat and lon
LOCATION = {
    "name": "California Central Valley",
    "latitude": 40.139051,
    "longitude": -123.097818
}

# ef get_access_token(client_id, client_server):
