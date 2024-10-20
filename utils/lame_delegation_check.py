import dns.resolver
import dns.exception
import dns.flags
import dns.rdatatype
import dns.resolver
import dns.message
import dns.query
import dns.name
import time


def get_ns_records(domain,ns_cache,counter=10):
    """
    Retrieves the NS records for the given domain.
    """
    # print('Getting NS Records lame delegation check...')
    try:
        ns_cached = ns_cache.get_ns_record(domain)
        # print(f'Cached NS Received {ns_cached}')
        if ns_cached == dns.resolver.NoAnswer or ns_cached == dns.resolver.NXDOMAIN:
            parent_domain = domain[domain.find('.') + 1:]
            return get_ns_records(parent_domain, ns_cache)
        if ns_cached: return ns_cached, domain
        time.sleep(2)
        answers = dns.resolver.resolve(domain, 'NS')
        ns_records = [str(rdata.target).rstrip('.') for rdata in answers]
        # print(f"Nameservers for {domain}: {', '.join(ns_records)}")
        ns_cache.set_ns_record(domain, ns_records)
        if not ns_records:
            parent_domain = domain[domain.find('.') + 1:]
            # print(f"Attempting to get parent level NS {parent_domain}")
            return get_ns_records(parent_domain, ns_cache)
        return ns_records,domain
    except dns.resolver.NoAnswer:
        print(f"No answer received from NS query {domain}")
        parent_domain = domain[domain.find('.') + 1:]
        ns_cache.set_ns_record(domain, dns.resolver.NoAnswer)
        # print(f"Attempting to get parent level NS {parent_domain}")
        return get_ns_records(parent_domain, ns_cache)
    except dns.resolver.NXDOMAIN:
        print(f"Domain does not exist: {domain}")
        ns_cache.set_ns_record(domain, dns.resolver.NXDOMAIN)
        parent_domain = domain[domain.find('.') + 1:]
        # print(f"Attempting to get parent level NS {parent_domain}")
        return get_ns_records(parent_domain, ns_cache)
    except Exception as e:
        print(f"Error retrieving NS records for {domain}: {e}")
        if counter > 120:
            return [], ""
        time.sleep(counter)
        return get_ns_records(domain, ns_cache, counter=counter*3)



def resolve_ns_ips(ns_name):
    """
    Resolves the A records (IPv4 addresses) for a given nameserver.
    """
    try:
        time.sleep(3)
        answers = dns.resolver.resolve(ns_name, 'A')
        ips = [str(rdata) for rdata in answers]
        # print(f"Resolved IPs for {ns_name}: {', '.join(ips)}")
        return ips
    except dns.resolver.NoAnswer:
        print(f"No A records found for nameserver: {ns_name}")
    except dns.resolver.NXDOMAIN:
        print(f"Nameserver does not exist: {ns_name}")
    except Exception as e:
        print(f"Error resolving IP for nameserver {ns_name}: {e}")
    return []


def query_soa(ns_ip, domain,counter=5):
    """
    Sends a SOA query to the specified nameserver IP for the given domain.
    Returns the DNS response message or None if an error occurs.
    """
    # print(f'querying SOA for {ns_ip, domain}')
    try:
        time.sleep(2)
        query = dns.message.make_query(domain, dns.rdatatype.SOA)
        response = dns.query.udp(query, ns_ip, timeout=5)
        return response
    except dns.exception.Timeout:
        print(f"Query to {ns_ip} timed out. for domain {domain}")
        if counter > 120:
            print(f"ERROR : complete retries : {ns_ip} for domain {domain}")
            return None
        time.sleep(counter)
        print(f'retrying {ns_ip}... for domain {domain}')
        return query_soa(ns_ip, domain,counter=counter*3)
    except Exception as e:
        print(f"Error querying SOA from {ns_ip}: {e}")
    return None


def evaluate_response(response):
    """
    Evaluates the DNS response based on the specified conditions.
    Returns a list of issues found.
    """
    issues = []
    # print(f'evaluating response ....\n \n')

    if response is None:
        issues.append("No response received.")
        return issues

    # Check if AA (Authoritative Answer) bit is set
    aa_bit_set = bool(response.flags & dns.flags.AA)
    if not aa_bit_set:
        issues.append("AA bit not set (No Authoritative Answer).")

    # Check if the answer section is empty
    if len(response.answer) == 0:
        if aa_bit_set:
            issues.append("AA bit set but answer section is empty.")
        else:
            issues.append("Answer section is empty.")

    # Check if the answer contains an SOA record
    has_soa = False
    for rrset in response.answer:
        if rrset.rdtype == dns.rdatatype.SOA:
            has_soa = True
            break
    if aa_bit_set and not has_soa:
        issues.append("AA bit set but answer does not contain an SOA record.")
    return issues


def main(domain,ns_cache,aggregate_cache):
    """
    Main function to execute the SOA record checks across all nameservers.
    """

    # Step 1: Retrieve NS records
    ns_records,domain = get_ns_records(domain,ns_cache)
    if not ns_records:
        return None
    
    cache_data = aggregate_cache.get(domain)
    if cache_data:
        return {'cached' : True, 'lame_delegation' : cache_data['lame_delegation'], 'nameservers' : cache_data['flagged_name_servers']}


    # Step 2: For each NS, resolve its IPs
    ns_lame = {}
    for ns in ns_records:
        ns_ips = resolve_ns_ips(ns)
        
        if not ns_ips:
            print(f"Flagging nameserver as lame due to unresolved IPs: {ns}")
            ns_lame[ns] = True
            continue

        # Step 3: Query SOA record on each IP
        is_lame = False
        for ip in ns_ips:
            # print(
                # f"\nQuerying SOA record for {domain} on nameserver {ns} ({ip})...")
            response = query_soa(ip, domain)
            if not response:
                return None
            issues = evaluate_response(response)
            if issues:
                is_lame = True
            # print(f'{ns}, {issues}')

        if is_lame:
            ns_lame[ns] = True
            print(f'{ns} found to be lame with {issues}')
        else:
            ns_lame[ns] = False
    # print(f'Evaluated all Nameservers for {domain}')
    return ns_lame


def process_data(subdomain, ns_cache, aggregate_cache):
    print(f'Starting lame delegation check {subdomain}')
    lame_servers = main(subdomain, ns_cache,aggregate_cache)
    if 'cached' in lame_servers:
        return lame_servers['lame_delegation'], lame_servers['nameservers']
    if not lame_servers:
        return None, []
    final_result = False
    nameservers_flagged = []
    for ns, result in lame_servers.items():
        if result == True:
            nameservers_flagged.append(ns)
            final_result = True
    print(f'Completed lame delegation check {subdomain}')
    return final_result, nameservers_flagged


if __name__ == "__main__":
    zone = "url5347.tesla.com"
    lame_servers = main(zone)
    result, flagged = process_data(zone )
    print(result, flagged)
    # print(lame_servers)
