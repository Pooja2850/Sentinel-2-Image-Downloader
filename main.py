'''
Sentinel-2 Downloader
Created by: Pooja Prajith
'''

import requests 
import os
from datetime import datetime, timedelta
from config import CDSE_USERNAME, CDSE_PASSWORD


# Location, lat and lon
LOCATION = {
    "name": "California Central Valley",
    "latitude": 40.139051,
    "longitude": -123.097818
}

def get_access_token(username, password):
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    # Data payload required by token endpoint
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password"
    }

    try:
        # Post request to get token
        # timeout occurs after 30 seconds 
        response = requests.post(token_url, data = data, timeout=30)

        # Status code = 200 -> successful
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

# Creates a bounding box around the center point (wkt polygon)
def create_bounding_box(lat, lon):
    offset = 0.005
    min_lat = lat - offset
    max_lat = lat + offset
    min_lon = lon - offset
    max_lon = lon + offset

    wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"

    return wkt

# Search for Sentinel-2 imagery using the Copernicus OData API
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

    try:
        # Send request to Copernicus catalogue API
        response = requests.get(query_url, timeout = 30)

        if response.status_code == 200:
            data = response.json()
            products = data.get('value', [])

            print(f"Found {len(products)} images.") 

            # Print the first few products
            for i, product in enumerate(products[:3]):
                print(f" {i+1}. {product['Name']}")

            return products
        
        else:
            print(f"Search failed: {response.status_code}")
            return []

    except Exception as e:
        print(f"Error: {e}")
        return []


def download_imagery(product_id, product_name, access_token, output_dir):
    print("Downloading imagery.")
    print(f"Product: {product_name}")
    print(f"Product ID: {product_id}")

    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"Copernicus_Sentinel2_NIR_{timestamp}.zip" # filename includes datasource, imagetype and timestamp

    output_path = os.path.join(output_dir, file_name)

    download_url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"

    # Authorization header containing access token for download
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"Saving to: {output_path}")
    print(f"Download URL: {download_url}")

    try:
        # Send GET request to download product
        response = requests.get(download_url, headers=headers, stream=True, timeout=300)

        if response.status_code == 200:
            # Retrieve file size from response headers
            total_size = int(response.headers.get('content-length', 0))
            print(f"File size: {total_size / (1024*1024):.2f} MB")

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

             # Confirm successful download           
            print("Download complete.")
            print(f"File saved: {output_path}")
            return output_path
        else:
            print(f"Download failed: {response.status_code}")
            print(f"Response: {response.text}")                                                                                                                                                                                                             
            return None

    except Exception as e:
        print(f"Error during download: {e}")
        return None

if __name__ == "__main__":
    print("*" * 65)
    print("SENTINEL-2 DOWNLOADER - FULL TEST")

    # Authenticate with Copernicus Data Space API
    print("Authentication")
    token = get_access_token(CDSE_USERNAME, CDSE_PASSWORD)

    if not token:
        print("Cannot continue without token")
    else: 
        print("Create Bounding box")
        wkt = create_bounding_box(LOCATION["latitude"], LOCATION["longitude"])
        print("Created search area.")

        # Define the time range for imagery search
        print("Search for imagery") 
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Filters include location, data range, and max cloud coverage
        products = search_sentinel2_imagery(
            wkt=wkt,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            max_cloud_cover=30
        )
        
        # If image products found, download the first image
        if products: 
            print("Download First Image")
            first_product = products[0]

            print("\nGetting fresh token for download.")
            fresh_token = get_access_token(CDSE_USERNAME, CDSE_PASSWORD)

            # Download the imagery dataset locally
            downloaded_file = download_imagery(
                product_id=first_product['Id'],
                product_name=first_product['Name'],
                access_token=fresh_token,
                output_dir="./sentinel2_downloads"  # Creates folder in current directory
            )
            
            if downloaded_file:
                print("\n" + "=" * 65)
                print("Success!")
                print("=" * 65)
                print(f"\nDownloaded: {downloaded_file}")
                print("\nThis file contains:")
                print("All Sentinel-2 bands (B1-B12, B8A)")
                print("Including NIR bands (B08, B8A)")
                print("=" * 65)
        else:
            print("\n No products found to download")

    print("*" * 65)