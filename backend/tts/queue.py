from queue import Queue


class SynthesisQueue:

    def __init__(self):

        self.queue = Queue()

    def add(self, task):

        self.queue.put(task)

    def next(self):

        if self.queue.empty():

            return None

        return self.queue.get()