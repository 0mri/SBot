from . import Newegg
import multiprocessing
import threading
import time
from multiprocessing.pool import ThreadPool
from concurrent.futures import ThreadPoolExecutor
def main():
    # executor = ThreadPoolExecutor(max_workers=10)
    # executor.submit(fn=Newegg().start)
    Newegg().start()