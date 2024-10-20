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
        return "Unknown"


def get_authoritative_nameservers(domain, ns_cache):
    try:
        ns_cached = ns_cache.get_ns_record(domain)
        # print(f'Cached NS Received {ns_cached}')
        if ns_cached == dns.resolver.NXDOMAIN or ns_cached == dns.resolver.NoAnswer:
            return None
        if ns_cached: return ns_cached
        answer = dns.resolver.resolve(domain, 'NS')
        nameservers = [str(rr.target).strip('.') for rr in answer]
        ns_cache.set_ns_record(domain, nameservers)
        nameserver_orgs = {}
        for nameserver in nameservers:
            # print('Checking nameserver {}'.format(nameserver))
            whois_output = whois_query(nameserver)
            org_pattern = re.compile(
                r'(?i)(organisation):\s*(.*)')
            match = org_pattern.search(whois_output)

            if match:
                # Extract and clean the organization name
                nameserver_orgs[nameserver] = match.group(2).strip()
            else:
                # print("Organization not found")
                nameserver_orgs[nameserver] = "Unknown"
        return nameserver_orgs
    except dns.resolver.NoAnswer:
        print(f"No answer received from NS query {domain} for registrar check")
        ns_cache.set_ns_record(domain, dns.resolver.NoAnswer)
        return None
    except dns.resolver.NXDOMAIN:
        print(f'Domain does not exist for NS query {domain} for registrar check')
        ns_cache.set_ns_record(domain, dns.resolver.NXDOMAIN)
        return None
    except Exception as e:
        print(f"Error retrieving NS records for {domain}: {e}")
        return None


def extract_domain_part(nameserver):
    return '.'.join(nameserver.split('.')[1:])


def check_if_different(domain, parent_response, ns_cache):
    registrar = get_registrar(domain)
    nameservers_orgs = get_authoritative_nameservers(domain, ns_cache)
    if not nameservers_orgs:
        # print(
        #     f'No nameservers found for {domain}, returning None for registrar Check')
        return parent_response
    for nameserver in nameservers_orgs:
        print(f'DEBUGGING NAMESERVER IS {nameserver}')
        if nameservers_orgs[nameserver] == 'Unknown':
            # print('Nameserver {}, org is not known')
            return None
        else:
            if fuzz.partial_ratio(registrar, nameservers_orgs[nameserver]) > 80:
                print('Nameserver {} matches. Registrar = {} and NS ORG = {}'.format(
                    nameserver, registrar, nameservers_orgs[nameserver]))
                return False
            else:
                print('Nameserver {} does not match. Registrar = {} and NS ORG = {}'.format(
                nameserver, registrar, nameservers_orgs[nameserver]))
                return True


def process_data(subdomain, parent_response, ns_cache):
    # print(f"Received new domain for registrar check: {subdomain}")
    final_result = check_if_different(subdomain, parent_response, ns_cache)
    print(f'Completed Registrar check {subdomain}')
    return final_result


# if __name__ == "__main__":
#     domain = "www.evilcorp.com"
#     check_if_different(domain)
