from bbot.scanner import Scanner


async def subdomain_enumeration(domain, related_domains=[], active=True):
    domains = related_domains + [domain]
    subdomain_enum_modules = [
        "anubisdb", "asn", "azure_realm", "azure_tenant", "baddns_direct", "baddns_zone", "bevigil",
        "binaryedge", "builtwith", "c99", "censys", "certspotter", "chaos", "columbus", "crt",
        "digitorus", "dnsbrute", "dnsbrute_mutations", "dnscaa", "dnscommonsrv", "dnsdumpster",
        "fullhunt", "github_codesearch", "github_org", "hackertarget", "httpx", "hunterio",
        "internetdb", "ipneighbor", "leakix", "myssl", "oauth", "otx", "passivetotal", "postman",
        "postman_download", "rapiddns", "securitytrails", "securitytxt", "shodan_dns",
        "sitedossier", "sslcert", "subdomaincenter", "subdomainradar", "trickest",
        "urlscan", "virustotal", "wayback", "zoomeye"
    ]
    modules = subdomain_enum_modules
    passive_enum_modules = ['digitorus', 'github_codesearch', 'certspotter', 'leakix', 'postman', 'postman_download', 'rapiddns', 'github_org', 'bevigil', 'anubisdb', 'columbus', 'dnscaa', 'internetdb', 'subdomaincenter', 'censys', 'sitedossier', 'azure_tenant', 'trickest',
                            'securitytrails', 'wayback', 'virustotal', 'passivetotal', 'azure_realm', 'zoomeye', 'hackertarget', 'c99', 'shodan_dns', 'dnsdumpster', 'myssl', 'hunterio', 'urlscan', 'fullhunt', 'chaos', 'ipneighbor', 'otx', 'crt', 'asn', 'binaryedge', 'builtwith', 'subdomainradar']
    if not active:
        modules = passive_enum_modules
    # print(modules)
    scan = Scanner(*domains, modules=modules)
    async for event in scan.async_start():
        inScopeFound = False
        subFound = False
        for tag in event.tags:
            if tag == "in-scope":
                inScopeFound = True
            if tag == "subdomain":
                subFound = True
        if subFound and inScopeFound:
            print(
                f'found subdomain {event.data}, distance of {event.scope_distance}')
            yield event.data
