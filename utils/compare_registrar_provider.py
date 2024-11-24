import dns.resolver
import time
import subprocess
import re
from thefuzz import fuzz


def whois_query(domain):
    result = subprocess.run(['whois', domain], capture_output=True, text=True)
    return result.stdout


def get_registrar(domain):
    # print('fetching registrar for {}'.format(domain))
    w = whois_query(domain)
    registrar_pattern = re.compile(
        r'(?i)(registrar):\s*(.*)')
    match = registrar_pattern.search(w)
    if match:
        return match.group(2).strip()
    else:
        registrar_pattern = re.compile(
            r'(?i)(organisation):\s*(.*)')
        match = registrar_pattern.search(w)
        if match:
            return match.group(2).strip()
        return "Unknown"


def get_registrant(domain):
    print(f"checking registrant for {domain}")
    w = whois_query(domain)
    registrant_pattern = re.compile(r'(?i)Registrant Organization:\s*(.*)')
    match = registrant_pattern.search(w)
    if match:
        return match.group(1).strip()
    else:
        return "Unknown"


def get_authoritative_nameservers(domain, domain_ns_cache, registrant_cache):
    try:
        domain_ns_cached = domain_ns_cache.get_ns_record(domain)
        # print(f'Cached NS Received {domain_ns_cached}')
        if domain_ns_cached == dns.resolver.NXDOMAIN or domain_ns_cached == dns.resolver.NoAnswer:
            return None
        if domain_ns_cached:
            return domain_ns_cached
        answer = dns.resolver.resolve(domain, 'NS')
        nameservers = [str(rr.target).strip('.') for rr in answer]
        domain_ns_cache.set_ns_record(domain, nameservers)
        nameserver_orgs = {}
        if not nameservers:
            return None
        for nameserver in nameservers:
            ns_domain = '.'.join(nameserver.split('.')[-2:])
            dns_provider = registrant_cache.get_provider(ns_domain)
            if not dns_provider:
                time.sleep(5)
                dns_provider = get_registrant(ns_domain)
                registrant_cache.set_provider(ns_domain, dns_provider)
            nameserver_orgs[nameserver] = dns_provider
        return nameserver_orgs
    except dns.resolver.NoAnswer:
        print(f"No answer received from NS query {domain} for registrar check")
        domain_ns_cache.set_ns_record(domain, dns.resolver.NoAnswer)
        return None
    except dns.resolver.NXDOMAIN:
        print(
            f'Domain does not exist for NS query {domain} for registrar check')
        domain_ns_cache.set_ns_record(domain, dns.resolver.NXDOMAIN)
        return None
    except Exception as e:
        print(f"Error retrieving NS records for {domain}: {e}")
        return None


def extract_domain_part(nameserver):
    return '.'.join(nameserver.split('.')[1:])


def check_if_use_DNS_provider_differnt(domain, parent_response, domain_ns_cache, ns_cache, registrant_cache):
    nameservers = []
    final_result = False
    connectivity = True
    time.sleep(5)
    registrar = get_registrar(domain)
    nameservers_orgs = get_authoritative_nameservers(
        domain, domain_ns_cache, registrant_cache)
    print(f'nameserver_orgs {nameservers_orgs}')
    if not nameservers_orgs:
        # print(
        #     f'No nameservers found for {domain}, returning None for registrar Check')
        connectivity = False
        return parent_response, registrar, connectivity
    for nameserver in nameservers_orgs:
        print(f'DEBUGGING NAMESERVER IS {nameserver}')
        if fuzz.partial_ratio(registrar, nameservers_orgs[nameserver]) > 80:
            print('Nameserver {} matches. Registrar = {} and NS ORG = {}'.format(
                nameserver, registrar, nameservers_orgs[nameserver]))
        elif fuzz.partial_ratio(registrar, domain) > 80:
            print('Nameserver {} is owned by Domain = {}'.format(
                nameserver, domain))
        else:
            print('Nameserver {} does not match. Registrar = {} and NS ORG = {}'.format(
                nameserver, registrar, nameservers_orgs[nameserver]))
            final_result = True
        ns_cache.set_ns_record(
            nameserver, {"dns_org": nameservers_orgs[nameserver]})
    return final_result, registrar, connectivity

def process_data(subdomain, parent_response, domain_ns_cache, ns_cache, registrant_cache):
    # print(f"Received new domain for registrar check: {subdomain}")
    final_result = check_if_use_DNS_provider_differnt(
        subdomain, parent_response, domain_ns_cache, ns_cache, registrant_cache)
    print(f'Completed Registrar check {subdomain}')
    return final_result
