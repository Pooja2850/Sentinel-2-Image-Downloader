'''
Sentinel-2 downloader
Created by: Pooja Prajith
'''

import requests 
import os
from datetime import datetime, timedelta
from config import CLIENT_ID, CLIENT_SECRET

# Store client id and client secret
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

def get_access_token(client_id, client_secret):
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    # data payload required by token endpoint
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    try:
        # post request to get token
        # timeout occurs after 30 seconds 
        response = requests.post(token_url, data = data, timeout=30)

        # status code = 200 -> successful
        if response.status_code == 200:
            token_data = response.json() # converts json response to python
            access_token = token_data["access_token"] # extracts the access token from the dictionary

            print("Authentication successful.")
            return access_token

        # Any other status code other than 200 = failed. 
        else: 
            print(f"Authentication failed. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    # Catches any network related errors.
    except requests.exceptions.RequestException as e:
        print(f"Error during authentication: {e}")
        return None

if __name__ == "__main__":
    print("*" * 65)
    print("Testing Authentication")

    token = get_access_token(CREDENTIALS["client_id"], CREDENTIALS["client_secret"])

    # Prints success or failure message
    if token:
        print(f"\nSuccess. Got token: {token[:30]}...")
    else: 
        print("\nFailed to get token. Check credentials.")
        
    print("*" * 65)

# Creates a bounding box around the center point (wkt polygon)
def create_bounding_box(lat, lon):
    offset = 0.005
    min_lat = lat - offset
    max_lat = lat + offset
    min_lon = lon - offset
    max_lon = lon + offset

    wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"

    return wkt

## Still working on the function(not complete...)
def search_sentinel2_imagery(wkt, start_date, end_date, max_cloud_cover):
    print(f"Sentinel-2 imagery search")
    print(f"Data range: {start_date} to {end_date}")

    # Found under the OData documentation page in CDSE
    catalog_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

    # Query structure used from CDSE documentation page
    filter_query = (
        f"Collection/Name eq 'SENTINEL-2' and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A') and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}') and "
        f"ContentDate/Start gt {start_date}T00:00:00.000Z and "
        f"ContentDate/Start lt {end_date}T23:59:59.999Z and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {max_cloud_cover})"
    )

    query_url = f"{catalog_url}?$filter={filter_query}&$top=10"

