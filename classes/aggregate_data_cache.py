import threading
from collections import deque
class AggregateDataCache:
    def __init__(self):
        self.aggregate_data = {}
        self.processed_domains = deque()
        self.lock = threading.Lock()

    def get(self, subdomain):
        with self.lock:
            return self.aggregate_data.get(subdomain)

    def set(self, subdomain, record):
        with self.lock:
            if subdomain in self.aggregate_data:
                return
            self.aggregate_data[subdomain] = record
            self.processed_domains.append(subdomain)
    
    def pop_last_domains(self):
        with self.lock:
            subdomains = []
            datas = []
            for i in range(len(self.processed_domains)):
                subdomain = self.processed_domains.popleft()
                subdomains.append(subdomain)
                datas.append(self.aggregate_data.get(subdomain))
            return subdomains,datas
