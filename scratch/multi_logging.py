import logging
import sys
from logging import handlers
import datetime
import multiprocessing as mp
import time


def child_process(q: mp.Queue):
    logger = logging.getLogger('child')
    q_handler = handlers.QueueHandler(q)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(q_handler)

    while True:
        logger.debug(f"Child Process: {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(1)


def main():
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(stream_handler)

    q = mp.Queue()
    l = handlers.QueueListener(q,stream_handler)

    p = mp.Process(target=child_process, args=(q,))
    p.start()

    l.start()
    while True:
        logger.debug(f"Main Process: {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(5)


if __name__ == "__main__":
    main()