from . import Newegg
from threading import Thread
def main():
    n_t = Thread(target=Newegg().run).start()