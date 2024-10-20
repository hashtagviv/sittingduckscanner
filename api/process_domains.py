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
from classes.nameserver_cache import NSCache
from classes.aggregate_data_cache import AggregateDataCache
from classes.processors import ProcessorsAvailable
from fastapi.responses import StreamingResponse

REGISTRAR_CHECK_TITLE = 'Registrar Different from DNS Provider?'
LAME_DELEGATION_TITLE = 'Lame delegation?'
VULNERABLE_NS_TITLE = 'Vulnerable Nameservers'


domains_processed_lock = threading.Lock()
domains_processed = set({})
aggregated_data = {}
file_lock = threading.Lock()
aggregated_data_lock = threading.Lock()
ns_cache = NSCache()
aggregate_cache = AggregateDataCache()
data_event = asyncio.Event()
processing_task = ProcessorsAvailable()
processing = 0
def generate_filename(domain):
    return domain + ".json"

def initialize_file(filename):
    with open(filename, 'w'):
        pass
    return filename

def write_to_file(filename, data):
    """
    Write a new lint to the file in JSON format.
    """
    print('writing to file...')
    with file_lock: 
        with open (filename, 'a') as f:
            f.write(json.dumps(data) + "\n")


async def main(domain: str):
    global processing
    processing = 1
    filename = initialize_file(generate_filename(domain))
    executor = ThreadPoolExecutor(max_workers=10)
    parent_domain_dns_registrar_diff = registrar_check.check_if_different(
        domain, None, ns_cache)
    lame_delegation_answer, nameservers = lame_delegation_check.process_data(domain, ns_cache, aggregate_cache)
    aggregate_cache.set(domain, {
            'depth': 0,
            'registrar_dns_different': parent_domain_dns_registrar_diff,
            'lame_delegation': lame_delegation_answer,
            'flagged_name_servers' : nameservers
        } )
    # write_to_file(filename, { 'subdomain' : domain, **aggregate_cache.get(domain)})
    data_event.set()
    async for subdomain in subdomain_enumeration(domain):
        executor.submit(process_subdomain, subdomain, parent_domain_dns_registrar_diff,filename)
    print(f'execution completed for domain {domain}')
    processing = 0
    processing_task.completed_execution()
    data_event.set()


def process_subdomain(subdomain: str, parent_response, filename):
    """
    This runs in a separate thread for each subdomain.
    """
    print(f'PROCESSING subdomain {subdomain}')
    subdomain = subdomain.replace('www.','')
    depth = subdomain.count('.') - 1
    try:
        with domains_processed_lock:
            if subdomain in domains_processed:
                print(f'{subdomain} already processed')
                raise Exception("Subdomain already processed")
            domains_processed.add(subdomain) 
    except:
        return 
    registrar_dns_diff = registrar_check.process_data(
        subdomain, parent_response, ns_cache)

    # print(f'START LAME DELEGATION CHECK {subdomain}')
    lame_delegation, nameservers = lame_delegation_check.process_data(
        subdomain, ns_cache, aggregate_cache)
    # print(f'COMPLETED LAME DELEGATION? {subdomain}')


    print(f'writing to cache {subdomain}')
    aggregate_cache.set(subdomain, {
    'depth': depth,
    'registrar_dns_different': registrar_dns_diff,
    'lame_delegation': lame_delegation,
    'flagged_name_servers' : nameservers
    })
    data_event.set()
    # write_to_file(filename, { 'subdomain' : subdomain, **aggregate_cache.get(subdomain)})


async def stream_subdomain_data():
    global aggregate_cache
    global processing

    async def event_generator():
        while processing:
            # Wait until there's new data available
            await data_event.wait()
            subdomains, datas = aggregate_cache.pop_last_domains()
            for i in range(len(subdomains)):
                response = {'subdomain': subdomains[i], **datas[i]}
                yield f"data: {json.dumps(response)}\n\n"

            data_event.clear()

        yield 'data: {"status": "complete"}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("domain", type=str, help="The domain to enumerate")
#     args = parser.parse_args()
#     asyncio.run(main(args.domain))
