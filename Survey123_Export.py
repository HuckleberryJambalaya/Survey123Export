from arcgis.gis import GIS
import os
import zipfile
import shutil
import requests
import time

# ArcGIS Online Credentials
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"

# Define Paths
SAVE_FOLDER = r"C:\Users\YourUserName\Documents\Python Stuff\arcgis_downloads"

# List of surveys to export and download
SURVEYS = {
    "LAYER ID 1": "LAYER NAME 1",
    "LAYER ID 2": "LAYER NAME 2",
    "LAYER ID 3": "LAYER NAME 3"
}

def export_survey_gdb(username, password, surveys):
    # Base URL for ArcGIS API
    base_url = "https://www.arcgis.com/sharing/rest"
    
    # Authenticate and obtain a token
    auth_url = f"{base_url}/generateToken"
    auth_data = {
        'username': username,
        'password': password,
        'referer': 'https://survey123.arcgis.com',
        'f': 'json'
    }
    response = requests.post(auth_url, data=auth_data)
    try:
        auth_response = response.json()
    except requests.exceptions.JSONDecodeError:
        print("Error: Unable to authenticate. Response:", response.text)
        return
    
    token = auth_response.get('token')
    if not token:
        print("Failed to authenticate. Response:", auth_response)
        return
    print("Successfully authenticated.")
    
    # Loop through each survey and request export
    for survey_id, survey_name in surveys.items():
        export_url = f"{base_url}/content/users/{username}/export"
        export_params = {
            'itemId': survey_id,
            'title': survey_name,
            'exportFormat': 'File Geodatabase',
            'token': token,
            'f': 'json'
        }
        export_response = requests.post(export_url, data=export_params)
        try:
            export_info = export_response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"Error: Unable to request export for {survey_name}. Response:", export_response.text)
            continue
        
        if 'exportItemId' not in export_info:
            print(f"Export request failed for {survey_name}. Response:", export_info)
            continue
        
        export_item_id = export_info['exportItemId']
        print(f"Export started for {survey_name}: {export_item_id}")

        # Add a 15-second delay to allow the export to complete
        print("Waiting 15 seconds for the export to complete...")
        time.sleep(15)

def download_and_process_gdb(username, password, gdb_names, save_folder):
    # Authenticate with ArcGIS Online
    gis = GIS("https://organizationname.maps.arcgis.com", username, password)

    for gdb_name in gdb_names:
        print(f"\nProcessing: {gdb_name}")

        # Search for the geodatabase in "My Content"
        items = gis.content.search(query=gdb_name, item_type="File Geodatabase")

        if not items:
            print(f"Error: Geodatabase '{gdb_name}' not found.")
            continue

        item = items[0]  # Assuming the first match is the correct one
        print(f"Found geodatabase: {item.title}")

        # Download the item
        zip_path = item.download(save_path=save_folder)
        print(f"Downloaded to: {zip_path}")

        # Ensure the .zip file has the correct name
        zip_filename = f"{gdb_name}.zip"
        correct_zip_path = os.path.join(save_folder, zip_filename)

        if zip_path != correct_zip_path:
            os.rename(zip_path, correct_zip_path)
            print(f"Renamed .zip file to: {correct_zip_path}")

        # Check if the file exists and is not empty
        if not os.path.exists(correct_zip_path) or os.path.getsize(correct_zip_path) == 0:
            print(f"Error: File '{correct_zip_path}' is missing or empty.")
            continue

        # Extract and rename the .gdb
        temp_extract_folder = os.path.join(save_folder, "temp_extracted")

        try:
            with zipfile.ZipFile(correct_zip_path, 'r') as zip_ref:
                # Test if the ZIP file is valid
                test_result = zip_ref.testzip()
                if test_result is not None:
                    print(f"Error: ZIP file is corrupted. First bad file: {test_result}")
                    continue

                zip_ref.extractall(temp_extract_folder)
                print(f"Extracted contents to temporary folder: {temp_extract_folder}")

            # Find the actual .gdb folder inside the extracted contents
            extracted_items = os.listdir(temp_extract_folder)
            gdb_folder = next((item for item in extracted_items if item.endswith(".gdb")), None)

            if gdb_folder:
                gdb_source_path = os.path.join(temp_extract_folder, gdb_folder)
                gdb_destination_path = os.path.join(save_folder, f"{gdb_name}.gdb")

                # Move and rename the .gdb folder
                shutil.move(gdb_source_path, gdb_destination_path)
                print(f"Renamed and moved '{gdb_folder}' to '{gdb_destination_path}'")

                # Cleanup
                shutil.rmtree(temp_extract_folder)
                print("Temporary extraction folder removed.")

            else:
                print("Error: No .gdb folder found inside the extracted files.")

        except zipfile.BadZipFile:
            print(f"Error: File '{correct_zip_path}' is not a valid ZIP file.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

# Step 1: Export surveys as geodatabases
export_survey_gdb(USERNAME, PASSWORD, SURVEYS)

# Step 2: Download and process the exported geodatabases
download_and_process_gdb(USERNAME, PASSWORD, SURVEYS.values(), SAVE_FOLDER)