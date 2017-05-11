from __future__ import absolute_import

from multiprocessing import cpu_count
import threading
import queue
import logging


logger = logging.getLogger(__name__)


class Queue(queue.Queue, object):
    def put(self, func, *args, **kwargs):
        return super(Queue, self).put((func, args, kwargs))


class ThreadQueue(object):
    def __init__(self, thread_multiplier=2):
        self.q = Queue()
        self.num_threads = (cpu_count() * thread_multiplier) or 1
        self.killswitch = threading.Event()

    def __enter__(self):
        logger.debug("Entering ThreadQueue context")
        for i in range(self.num_threads):
            t = threading.Thread(
                target=self.worker, args=("Thread-{}".format(i),))
            t.start()

        return self.q

    def __exit__(self, exc_type, exc_value, traceback):
        self.killswitch.set()
        logger.debug("Exiting ThreadQueue context")

    def worker(self, name):
        """
        Thread worker. Expects queue to be populated with three-ples of a
        function to run and related input args and kwargs.

        Worker function will be called with the queue as the first arg,
        along with the provided args and kwargs.
        """
        logger.debug("Starting thread {}".format(name))
        while not self.killswitch.is_set():
            try:
                func, args, kwargs = self.q.get(timeout=1)
                logger.debug(
                    "Processing %s(%s)", func.func_name,
                    ','.join([x for x in [
                        ','.join(args),
                        ','.join('{}={}'.format(k, v) for k, v in kwargs.items())
                    ] if x])
                )
            except queue.Empty:
                continue
            func(self.q, *args, **kwargs)
            self.q.task_done()
        logger.debug("Stopping thread {}".format(name))
