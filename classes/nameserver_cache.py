import threading


class DomainNSCache:
    def __init__(self):
        self.ns_records = {}
        self.lock = threading.Lock()

    def get_ns_record(self, subdomain):
        with self.lock:
            return self.ns_records.get(subdomain)

    def set_ns_record(self, subdomain, record):
        with self.lock:
            self.ns_records[subdomain] = record


class NSCache:
    def __init__(self):
        self.ns_records = {}
        self.lock = threading.Lock()

    def get_ns_record(self, nameserver, option=""):
        with self.lock:
            if option:
                record = self.ns_records.get(nameserver)
                if record and option in record:
                    return record[option]
            else:
                return None
            return self.ns_records.get(nameserver)

    def set_ns_record(self, nameserver, record):
        with self.lock:
            self.ns_records[nameserver] = record


class RegistrantCache:
    def __init__(self):
        self.providers = {}
        self.lock = threading.Lock()

    def get_provider(self, domain):
        with self.lock:
            return self.providers.get(domain)

    def set_provider(self, domain, provider):
        with self.lock:
            self.providers[domain] = provider
