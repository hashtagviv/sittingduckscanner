class ProcessorsAvailable:
    def __init__(self):
        self.processors = 1


    def add_tasks(self):
        self.processors -= self.processors

    def remaining_tasks(self):
        print(f'REMAINING PROCESSORS {self.processors}')
        return self.processors

    def completed_execution(self):
        self.processors += 1
        