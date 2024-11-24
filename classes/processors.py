MAX_THREADS = 4
class ProcessorsAvailable:
    def __init__(self):
        self.processors = MAX_THREADS


    def add_tasks(self):
        self.processors -= 1

    def remaining_tasks(self):
        print(f'REMAINING PROCESSORS {self.processors}')
        return self.processors

    def completed_execution(self):
        self.processors += 1
        