from . import Newegg
import time
def main():
    success = False
    while not success:
        success, time = Newegg().start(timeout=60)
        # print(success, time)
    