import os
import datetime
import json

def extract_file_timestamp(filename):
     return datetime.strptime(f"{filename.split('_')[1]}_{filename.split('_')[2]}", "%Y-%m-%d_%H-%M-%S")

def get_new_subdomain_file(latest_file, second_latest_file, folder_name):
    latest_file = os.path.join(folder_name, latest_file)
    second_latest_file = os.path.join(folder_name, second_latest_file)

    with open(latest_file, 'r') as file:
        latest_file_data = json.load(file)

    with open(second_latest_file, 'r') as file:
        second_latest_file_data = json.load(file)

    latest_file_subdomains_list = {e['subdomain'] for e in latest_file_data}
    second_latest_file_subdomains_list = {e['subdomain'] for e in second_latest_file_data}

    new_subdomains_list = latest_file_subdomains_list - second_latest_file_subdomains_list

    new_subdomains = [e for e in new_subdomains_list if e['subdomain'] in new_subdomains_list]

    temp_file = os.path.join(folder_name, 'temp_file.json')
    with open(temp_file, 'w') as file:
        json.dump(new_subdomains, file, indent=4)
    
    return temp_file

def get_new_subdomain_json(domain):
    """
    return the lastest scan file and the new subdomain file
    """
    folder_name = f'../history/{domain}'
    
    scanned_files = [f for f in os.listdir(folder_name) if os.path.isfile(os.path.join(folder_name, f))]

    file_count = len(scanned_files)
    if file_count == 0:
        print("Error in processing domain")
        return None
    elif file_count == 1:
        latest_file = scanned_files[0]
        new_subdomain_file = latest_file
    else:
        scanned_files = sorted(scanned_files, key=extract_file_timestamp, reverse=True)
        latest_file = scanned_files[0]
        second_latest_file = scanned_files[1]
        new_subdomain_file = get_new_subdomain_file(latest_file, second_latest_file, folder_name)

    return new_subdomain_file