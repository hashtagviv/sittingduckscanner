# main.py
import asyncio
import threading
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from asyncio import Queue
from utils.iterate_subdomains import subdomain_enumeration
import utils.lame_delegation_check as lame_delegation_check
import utils.compare_registrar_provider as registrar_check

REGISTRAR_CHECK_TITLE = 'Registrar Different from DNS Provider?'
LAME_DELEGATION_TITLE = 'Lame delegation?'
VULNERABLE_NS_TITLE = 'Vulnerable Nameservers'

# Central aggregation dictionary
aggregated_data = {}
file_lock = threading.Lock()
aggregated_data_lock = threading.Lock()

def generate_filename(domain):
    return domain + ".json"

def initialize_file(filename):
    with open(filename, 'w'):
        pass
    return filename

def write_to_file(filename, data):
    """
    Write the aggregated data to a file in JSON format.
    """
    print('writing to file...')
    with file_lock: 
        with open (filename, 'a') as f:
            f.write(json.dumps(data) + "\n")


async def main(domain: str):
    filename = initialize_file(generate_filename(domain))
    executor = ThreadPoolExecutor(max_workers=10)
    parent_domain_dns_registrat_diff = registrar_check.check_if_different(
        domain, None)
    lame_delegation_answer, nameservers = lame_delegation_check.process_data(domain, aggregated_data)
    aggregated_data[domain] = {
            'distance': 0,
            'registrar_dns_different': parent_domain_dns_registrat_diff,
            'lame_delegation': lame_delegation_answer,
            'flagged_name_servers' : nameservers
        }
    write_to_file(filename, {domain : aggregated_data[domain]})
    async for subdomain in subdomain_enumeration(domain):
        executor.submit(process_subdomain, subdomain, parent_domain_dns_registrat_diff,filename)
    # print('writing to json file')
    # with open('filename.json', 'w') as f:
    #     json.dump(aggregated_data, f, indent=4)


def process_subdomain(subdomain: str, parent_response, filename):
    """
    This runs in a separate thread for each subdomain.
    """
    print(f'PROCESSING subdomain {subdomain}')
    subdomain = subdomain.replace('www.','')
    depth = subdomain.count('.') - 1
    try:
        with aggregated_data_lock:
            if subdomain in aggregated_data:
                print(f'{subdomain} already processed')
                raise Exception("Subdomain already processed") 
    except:
        return 
    registrar_dns_diff = registrar_check.process_data(
        subdomain, parent_response, aggregated_data)

    print(f'START LAME DELEGATION CHECK {subdomain}')
    lame_delegation, nameservers = lame_delegation_check.process_data(
        subdomain, aggregated_data)

    try:
        with aggregated_data_lock:
            print(f'writing to cache {subdomain}')
            if subdomain in aggregated_data:
                print(f'{subdomain} already processed')
                raise Exception("Subdomain already processed") 
            aggregated_data[subdomain] = {
                'depth': depth,
                'registrar_dns_different': registrar_dns_diff,
                'lame_delegation': lame_delegation,
                'flagged_name_servers' : nameservers
            }
    except Exception as e:
        return
    write_to_file(filename, {subdomain : aggregated_data[subdomain]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", type=str, help="The domain to enumerate")
    args = parser.parse_args()
    asyncio.run(main(args.domain))
