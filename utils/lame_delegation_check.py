import dns.resolver
import dns.exception
import dns.flags
import dns.rdatatype
import dns.resolver
import dns.message
import dns.query
import dns.name
import time


def get_ns_records(domain):
    """
    Retrieves the NS records for the given domain.
    """
    try:
        time.sleep(2)
        answers = dns.resolver.resolve(domain, 'NS')
        ns_records = [str(rdata.target).rstrip('.') for rdata in answers]
        print(f"Nameservers for {domain}: {', '.join(ns_records)}")
        if not ns_records:
            parent_domain = domain[domain.find('.') + 1:]
            print(f"Attempting to get parent level NS {parent_domain}")
            return get_ns_records(parent_domain)
        return ns_records
    except dns.resolver.NoAnswer:
        print(f"No NS records found for domain: {domain}")
        return []
    except dns.resolver.NXDOMAIN:
        print(f"Domain does not exist: {domain}")
        parent_domain = domain[domain.find('.') + 1:]
        print(f"Attempting to get parent level NS {parent_domain}")
        return get_ns_records(parent_domain)
    except Exception as e:
        print(f"Error retrieving NS records for {domain}: {e}")
        return []

    return []


def resolve_ns_ips(ns_name):
    """
    Resolves the A records (IPv4 addresses) for a given nameserver.
    """
    try:
        time.sleep(1)
        answers = dns.resolver.resolve(ns_name, 'A')
        ips = [str(rdata) for rdata in answers]
        print(f"Resolved IPs for {ns_name}: {', '.join(ips)}")
        return ips
    except dns.resolver.NoAnswer:
        print(f"No A records found for nameserver: {ns_name}")
    except dns.resolver.NXDOMAIN:
        print(f"Nameserver does not exist: {ns_name}")
    except Exception as e:
        print(f"Error resolving IP for nameserver {ns_name}: {e}")
    return []


def query_soa(ns_ip, domain):
    """
    Sends a SOA query to the specified nameserver IP for the given domain.
    Returns the DNS response message or None if an error occurs.
    """
    try:
        time.sleep(1)
        query = dns.message.make_query(domain, dns.rdatatype.SOA)
        response = dns.query.udp(query, ns_ip, timeout=5)
        return response
    except dns.exception.Timeout:
        print(f"Query to {ns_ip} timed out.")
    except Exception as e:
        print(f"Error querying SOA from {ns_ip}: {e}")
    return None


def evaluate_response(response):
    """
    Evaluates the DNS response based on the specified conditions.
    Returns a list of issues found.
    """
    issues = []
    print(f'evaluating response ....\n \n')

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


def main(domain):
    """
    Main function to execute the SOA record checks across all nameservers.
    """

    # Step 1: Retrieve NS records
    ns_records = get_ns_records(domain)
    if not ns_records:
        print(f'NS RECORDS FOUND FOR LAME DELEGATION CHECK{ns_records}')
        return

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
            print(
                f"\nQuerying SOA record for {domain} on nameserver {ns} ({ip})...")
            response = query_soa(ip, domain)
            issues = evaluate_response(response)

            if issues:
                print(f"Issues found with nameserver {ns} ({ip}):")
                for issue in issues:
                    print(f" - {issue}")
                is_lame = True
                break
            else:
                print(f"Nameserver {ns} ({ip}) responded correctly.")

        if is_lame:
            ns_lame[ns] = True
        else:
            ns_lame[ns] = False
    print('Evaluated all Nameservers')
    return ns_lame


def process_data(subdomain):
    lame_servers = main(subdomain)
    if not lame_servers:
        return None
    result = False
    for ns, result in lame_servers.items():
        print(f'{ns}, {result}')
        if result == True:
            return True
    return False


if __name__ == "__main__":
    zone = "aws.com"
    lame_servers = main(zone)
    print(lame_servers)
