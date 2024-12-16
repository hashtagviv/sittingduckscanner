import os
from datetime import datetime
import json

def add_issues(json_data):
    for record in json_data:
        if record['lame_delegation']:
            record['issues'] = ['lame delegation']

def label_vulnerable_domains(json_data):
    for record in json_data:
        record['is_vulnerable'] = record.get('registrar_dns_different', False) and record.get('lame_delegation', False)
        print(record['is_vulnerable'])
    return json_data

def filter_vulnerable_domains(json_data):
    return [record for record in json_data if record['is_vulnerable'] == True]

def extract_file_timestamp(filename):
     filename = filename.rstrip('.json')
     return datetime.strptime(f"{filename.split('_')[1]}_{filename.split('_')[2]}", "%Y-%m-%d_%H-%M-%S")

def get_new_subdomain_file(latest_file, second_latest_file, folder_name):
    latest_file = os.path.join(folder_name, latest_file)
    second_latest_file = os.path.join(folder_name, second_latest_file)

    latest_file_data = []
    second_latest_file_data = []

    with open(latest_file, 'r') as file:
        for line in file:
            record = json.loads(line.strip())     
            latest_file_data.append(record)

    with open(second_latest_file, 'r') as file:
        for line in file:
            record = json.loads(line.strip())     
            second_latest_file_data.append(record)

    latest_file_subdomains_list = {e['subdomain'] for e in latest_file_data}
    second_latest_file_subdomains_list = {e['subdomain'] for e in second_latest_file_data}

    new_subdomains_list = latest_file_subdomains_list - second_latest_file_subdomains_list

    new_subdomains = [e for e in latest_file_data if e['subdomain'] in new_subdomains_list]

    add_issues(new_subdomains)
    add_issues(latest_file_data)
    # label_vulnerable_domains(new_subdomains)
    label_vulnerable_domains(latest_file_data)
    latest_file_data = filter_vulnerable_domains(latest_file_data)
    temp_file = f'temp_files/temp_file.json'
    temp_whole_latest_file = f'temp_files/temp_whole_latest_file.json'
    with open(temp_file, 'w') as file:
        for e in new_subdomains:
            json.dump(e, file)
            file.write('\n')

    with open(temp_whole_latest_file, 'w') as file:
        for e in latest_file_data:
            json.dump(e, file)
            file.write('\n')
    
    return temp_file, temp_whole_latest_file

def get_new_subdomain_json_and_label_vulnerable_domains(domain):
    """
    return the lastest scan file and the new subdomain file
    """
    folder_name = f'history/{domain}'
    
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
        new_subdomain_file, vulnerable_subdomain_file = get_new_subdomain_file(latest_file, second_latest_file, folder_name)

    return new_subdomain_file, vulnerable_subdomain_file