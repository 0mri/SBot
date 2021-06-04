from .main import main
import argparse
from bot import settings
import sys
import platform
import threading
import os
def pre_run():
    
    os.system("taskkill /im chromedriver.exe /f")
    os.system("taskkill /im chrome.exe /f")
    
    
    parser = argparse.ArgumentParser(prog="bot",description="SELENIUM BOT")

    parser.add_argument("-d","--dev",help="(optional) set developer mode",default=False,action='store_true')
    
    parser.add_argument("-c","--chrome", action='store_true', help="(optional) select chrome as webdriver",default=None)
    parser.add_argument("-e","--edge", action='store_true' ,help="(optional) select edge as webdriver",default=None)
    parser.add_argument("-f","--firefox", action='store_true' ,help="(optional) select firefox as webdriver",default=None)
    
    parser.add_argument("-dry","--dry-run", action='store_true' ,help="(optional) run the bot without buying anything",default=False)
    
    parser.add_argument("-ps","--processes", type=int ,help="(optional) set num of processes",default=None)
    
    parser.add_argument("-p","--path",type=str ,help="(optional) custom path to webdriver",default=settings.DRIVER_PATH)
    
    parser.add_argument("--captcha",action='store_true' ,help="(optional) go to captcha first",default=False)
    
    parser.add_argument("--headless",action='store_true' ,help="(optional) force headless browser",default=False)
    
    args = parser.parse_args()
    if args.chrome:
        settings.WEBDRIVER = settings.CHROME
    elif args.edge:
        settings.WEBDRIVER = settings.EDGE
    elif args.firefox:
        settings.WEBDRIVER = settings.FIREFOX
    else:
        settings.WEBDRIVER = settings.CHROME
    
    #run in developer mode
    settings.DEV = args.dev
    #run without buying
    settings.DRY_RUN = args.dry_run
    #set path
    settings.DRIVER_PATH = args.path
    settings.OS = platform.system()
    settings.DRIVER_PATH += "chromedriver" if settings.WEBDRIVER == settings.CHROME else 'msedgedriver'
    settings.DRIVER_PATH += ".exe" if settings.OS == settings.WINDOWS else ''
    #num of processes
    settings.PROCESSES_NUM = args.processes
    settings.HEADLESS = args.headless
    settings.CAPTCHA = args.captcha
if __name__ == "__main__":
    pre_run()
    main()