# main.py
import asyncio
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

# Queue to send data to the other parts
data_queue = Queue()

# Central aggregation dictionary
aggregated_data = {}
file_lock = asyncio.Lock()  #


async def write_to_file(filename, data):
    """
    Write the aggregated data to a file in JSON format.
    """
    print('writing to file')
    async with file_lock:
        async with asyncio.to_thread(open, filename, 'w') as f:
            json.dump(data, f, indent=4)


async def main(domain: str):
    executor = ThreadPoolExecutor(max_workers=10)
    parent_domain_comparison = registrar_check.check_if_different(
        domain, None)
    async for subdomain, distance in subdomain_enumeration(domain):
        executor.submit(process_subdomain, subdomain,
                        distance, parent_domain_comparison)
    print('writing to json file')
    with open('filename.json', 'w') as f:
        json.dump(aggregated_data, f, indent=4)


def process_subdomain(subdomain: str, distance: int, parent_response):
    """
    This runs in a separate thread for each subdomain.
    """
    registrar_dns_diff = registrar_check.process_data(
        subdomain, parent_response)

    print(f'START LAME DELEGATION CHECK {subdomain}')
    lame_delegation = lame_delegation_check.process_data(
        subdomain)

    # Aggregate data
    aggregated_data[subdomain] = {
        'distance': distance,
        'registrar_dns_different': registrar_dns_diff,
        'lame_delegation': lame_delegation
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", type=str, help="The domain to enumerate")
    args = parser.parse_args()
    asyncio.run(main(args.domain))  # Pass the domain to main
