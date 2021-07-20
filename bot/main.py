from . import Newegg
import time
def main():
    success = False
    while not success:
        negg = Newegg()
        success, time = negg.start(timeout=60)
        try:
            negg.stop()
        except:
            pass
        # print(success, time)
    