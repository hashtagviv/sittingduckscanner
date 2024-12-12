# main.py
import asyncio
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor
from asyncio import Queue
from utils.iterate_subdomains import subdomain_enumeration
import utils.lame_delegation_check as lame_delegation_check
import utils.compare_registrar_provider as registrar_check
from utils.compare_registrar_provider import get_registrant
from classes.nameserver_cache import DomainNSCache, NSCache, RegistrantCache
from classes.aggregate_data_cache import AggregateDataCache
from classes.processors import ProcessorsAvailable
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
import os

REGISTRAR_CHECK_TITLE = 'Registrar Different from DNS Provider?'
LAME_DELEGATION_TITLE = 'Lame delegation?'
VULNERABLE_NS_TITLE = 'Vulnerable Nameservers'


domains_processed_lock = threading.Lock()
domains_processed = set()
# file_lock = threading.Lock()
domain_ns_cache, ns_cache, registrant_cache = DomainNSCache(), NSCache(), RegistrantCache()
aggregate_cache = AggregateDataCache()
data_event = asyncio.Event()
cancellation_event = asyncio.Event()
processing_task = ProcessorsAvailable()
processing = 0
use_cache = False


def generate_filename(domain):
    return domain + ".json"


def initialize_file(filename):
    with open(filename, 'w'):
        pass
    return filename


def write_to_file(filename, data, file_lock):
    """
    Write a new lint to the file in JSON format.
    """
    print('writing to file...')
    with file_lock:
        with open(filename, 'a') as f:
            f.write(json.dumps(data) + "\n")


def format_providers(nameservers, ns_cache):
    # Given a list of nameservers and ns_cache, return all the providers, or empty if not found
    orgs = []
    for nameserver in nameservers:
        org = ns_cache.get_ns_record(nameserver, option="dns_org")
        if org:
            orgs.append(org)
        else:
            ns_domain = '.'.join(nameserver.split('.')[-2:])
            dns_provider = get_registrant(ns_domain)
            ns_cache.set_ns_record(
                nameserver, {"dns_org": dns_provider})
            orgs.append(dns_provider)
    return orgs

def get_lastest_file(domain_name):
    files = [f for f in os.listdir(f'history/{domain_name}') if f.startswith(domain_name)]
    if not files:
        return None, None

    lastest_file = None
    lastest_file_time = None

    for file in files:
        timestamp_str = file[len(domain_name) + 1:file.rfind(".")]
        file_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
        if lastest_file_time is None or file_time > lastest_file_time:
            lastest_file = file
            lastest_file_time = file_time
    now = datetime.now()
    if_fresh = now - lastest_file_time <= timedelta(hours=24)
    lastest_file = f'history/{domain_name}/{lastest_file}'
    return lastest_file, if_fresh

def load_file(filename, aggregate_cache):
    with open(filename, 'r') as f:
            for line in f:
                # Parse each line as JSON
                record = json.loads(line.strip())
                
                subdomain = record.pop('subdomain')     
                aggregate_cache.set(subdomain, record)
    return aggregate_cache

async def main(domain="", time_limit=float('inf'), related_domains=[], active=True):
    global processing, domains_processed, domain_ns_cache, aggregate_cache, ns_cache, registrant_cache, cancellation_event, use_cache
    # cancellation_event = threading.Event()

    processing = 1
    filename = f'history/{domain}'
    if not os.path.exists(filename):
        os.makedirs(filename, exist_ok=True)
    lastest_file, if_fresh = get_lastest_file(domain)
    
    if if_fresh:
        print("The domain was processed recently. Use latest cache")
        use_cache = True
        data_event.set()
    else:
        use_cache = False
        data_event.set()
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f'{filename}/{domain}_{current_date}'
        filename = initialize_file(generate_filename(filename))
        file_lock = threading.Lock()
        executor = ThreadPoolExecutor(max_workers=10)
        start_time = time.time()
        parent_domain_dns_registrar_diff, registrar, connectivity = registrar_check.check_if_use_DNS_provider_differnt(
            domain, None, domain_ns_cache, ns_cache, registrant_cache)
        lame_delegation_answer, flagged_nameservers, all_nameservers, issues = lame_delegation_check.process_data(
            domain, domain_ns_cache, aggregate_cache)
        all_orgs = format_providers(all_nameservers, ns_cache)
        aggregate_cache.set(domain, {
            'depth': 0,
            'registrar_dns_different': parent_domain_dns_registrar_diff,
            'lame_delegation': lame_delegation_answer,
            'flagged_name_servers': flagged_nameservers,
            'all_nameservers': all_nameservers,
            'registrar': registrar,
            'all_orgs': all_orgs,
            'connectivity': connectivity,
            'issues': issues
        })
        
        write_to_file(filename, {'subdomain': domain,
                    **aggregate_cache.get(domain)}, file_lock)
        data_event.set()
        async for subdomain in subdomain_enumeration(domain, related_domains=related_domains, active=active):
            elapsed_time = time.time() - start_time
            if elapsed_time >= time_limit:
                cancellation_event.set()
                print(f"Stopping enumeration due to time limit.")
                break

            if cancellation_event.is_set():
                print("Cancellation requested. Stopping processing.")
                break
            executor.submit(process_subdomain, subdomain,
                            parent_domain_dns_registrar_diff, filename, cancellation_event, file_lock)

    print(f'execution completed for domain {domain}')
    processing = 0
    processing_task.completed_execution()
    data_event.set()
    cancellation_event.clear()
    # clear cache
    domains_processed = set()
    domain_ns_cache, ns_cache, registrant_cache = DomainNSCache(), NSCache(), RegistrantCache()
    aggregate_cache = AggregateDataCache()


def process_subdomain(subdomain: str, parent_response, filename, cancellation_event, file_lock):
    """
    This runs in a separate thread for each subdomain.
    """
    print(f'PROCESSING subdomain {subdomain}')
    if cancellation_event.is_set():
        print(f"Processing of {subdomain} cancelled.")
        return
    
    subdomain = subdomain.replace('www.', '')
    depth = subdomain.count('.') - 1
    try:
        with domains_processed_lock:
            if subdomain in domains_processed:
                print(f'{subdomain} already processed')
                raise Exception("Subdomain already processed")
            domains_processed.add(subdomain)
    except:
        return
    registrar_dns_diff, registrar, connectivity = registrar_check.process_data(
        subdomain, parent_response, domain_ns_cache, ns_cache, registrant_cache)

    # print(f'START LAME DELEGATION CHECK {subdomain}')
    lame_delegation, nameservers, all_nameservers, issues = lame_delegation_check.process_data(
        subdomain, domain_ns_cache, aggregate_cache)
    all_orgs = format_providers(all_nameservers, ns_cache)
    print(f'writing to cache {subdomain}')
    aggregate_cache.set(subdomain, {
        'depth': depth,
        'registrar_dns_different': registrar_dns_diff,
        'lame_delegation': lame_delegation,
        'flagged_name_servers': nameservers,
        'all_nameservers': all_nameservers,
        'registrar': registrar,
        'all_orgs': all_orgs,
        'connectivity': connectivity,
        'issues': issues
    })
    data_event.set()
    write_to_file(filename, {'subdomain': subdomain,
                  **aggregate_cache.get(subdomain)}, file_lock)


async def stream_subdomain_data(domain):
    global aggregate_cache
    global processing
    global use_cache
    filename = f'history/{domain}'
    if_fresh = False
    await data_event.wait()
    if os.path.exists(filename) and use_cache:
        # os.makedirs(filename, exist_ok=True)
        lastest_file, if_fresh = get_lastest_file(domain)
    
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

    async def event_generator1():    
        subdomains, datas = aggregate_cache1.pop_last_domains()
        for i in range(len(subdomains)):
            response = {'subdomain': subdomains[i], **datas[i]}
            yield f"data: {json.dumps(response)}\n\n"
        yield 'data: {"status": "complete"}\n\n'

    if if_fresh:
        aggregate_cache1 = AggregateDataCache()
        aggregate_cache1 = load_file(lastest_file, aggregate_cache1)
        use_cache = False
        return StreamingResponse(event_generator1(), media_type="text/event-stream")
    else:
        return StreamingResponse(event_generator(), media_type="text/event-stream")
