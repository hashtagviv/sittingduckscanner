import dns.resolver
import whois


domain = 'google.com'
answer = dns.resolver.resolve(domain, 'NS')
nameservers = [str(rr.target).strip('.') for rr in answer]
nameserver_orgs = []

for nameserver in nameservers:
    print(nameserver)
    nameserver_orgs.append(whois.whois(nameserver).org)
