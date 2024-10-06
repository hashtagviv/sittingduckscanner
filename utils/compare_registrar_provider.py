import dns.resolver

import time
import subprocess
import re
from asyncio import Queue


def whois_query(domain):
    result = subprocess.run(['whois', domain], capture_output=True, text=True)
    return result.stdout


def get_registrar(domain):
    print('fetching registrar for {}'.format(domain))
    w = whois_query(domain)
    registrar_pattern = re.compile(
        r'(?i)(registrar):\s*(.*)')
    match = registrar_pattern.search(w)
    if match:
        return match.group(2).strip()
    else:
        return "Unknown"


def get_authoritative_nameservers(domain):
    try:
        answer = dns.resolver.resolve(domain, 'NS')
        nameservers = [str(rr.target).strip('.') for rr in answer]
        nameserver_orgs = {}
        for nameserver in nameservers:
            print('Checking nameserver {}'.format(nameserver))
            whois_output = whois_query(nameserver)
            org_pattern = re.compile(
                r'(?i)(organisation):\s*(.*)')
            match = org_pattern.search(whois_output)

            if match:
                # Extract and clean the organization name
                nameserver_orgs[nameserver] = match.group(2).strip()
            else:
                print("Organization not found")
                nameserver_orgs[nameserver] = "Unknown"
        return nameserver_orgs
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return None


def extract_domain_part(nameserver):
    return '.'.join(nameserver.split('.')[1:])


def check_if_different(domain, parent_response):
    registrar = get_registrar(domain)
    nameservers_orgs = get_authoritative_nameservers(domain)
    if not nameservers_orgs:
        print(
            f'No nameservers found for {domain}, returning None for registrar Check')
        return parent_response
    for nameserver in nameservers_orgs:
        if nameservers_orgs[nameserver] == 'Unknown':
            print('Nameserver {}, org is not known')
        else:

            registrar_words = registrar.split(' ')
            words_in_ns_org = nameservers_orgs[nameserver].split(' ')
            if registrar_words[0] in words_in_ns_org and words_in_ns_org[0] in registrar_words:
                print('Nameserver {} matches. Registrar = {} and NS ORG = {}'.format(
                    nameserver, registrar, nameservers_orgs[nameserver]))
                return False
            else:
                print('Nameserver {} does not match. Registrar = {} and NS ORG = {}'.format(
                    nameserver, registrar, nameservers_orgs[nameserver]))
                return True


def process_data(subdomain, parent_response):
    while True:
        print(f"Received new domain: {subdomain}")
        final_result = check_if_different(subdomain, parent_response)
        return final_result


# if __name__ == "__main__":
#     domain = "www.evilcorp.com"
#     check_if_different(domain)
