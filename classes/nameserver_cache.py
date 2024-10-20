import threading
class NSCache:
    def __init__(self):
        self.ns_records = {}
        self.lock = threading.Lock()

    def get_ns_record(self, subdomain):
        with self.lock:
            return self.ns_records.get(subdomain)

    def set_ns_record(self, subdomain, record):
        with self.lock:
            self.ns_records[subdomain] = record