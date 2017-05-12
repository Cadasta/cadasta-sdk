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
        """
        Args:
            thread_multiplier (int, optional): Number of threads per cpu. Set
            to 0 for single-threaded operation. Thread-count maxes out at 8
            threads (to avoid overloading the Cadasta webserver).
        """

        self.q = Queue()
        self.num_threads = min([(cpu_count() * thread_multiplier) or 1, 8])
        self.killswitch = threading.Event()

    def __enter__(self):
        logger.debug("Entering ThreadQueue context")
        for i in range(self.num_threads):
            t = threading.Thread(
                target=self.worker, args=("Thread-{}".format(i),))
            t.start()

        return self.q

    def __exit__(self, exc_type, exc_value, traceback):
        self.q.join()
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
                signature_str = "{}({})".format(
                    func.__name__,
                    ', '.join([x for x in [
                        ', '.join([repr(arg) for arg in args]),
                        ', '.join('{}={}'.format(k, repr(v)) for k, v in kwargs.items())
                    ] if x]))
                logger.debug("Processing %s", signature_str)
            except queue.Empty:
                continue
            try:
                func(self.q, *args, **kwargs)
            except Exception:
                logger.exception("Failed to process %s", signature_str)
            finally:
                self.q.task_done()
        logger.debug("Stopping thread {}".format(name))
