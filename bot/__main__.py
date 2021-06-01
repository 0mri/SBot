from .main import main
import argparse
from bot import settings
import sys
import platform

def pre_run():
    parser = argparse.ArgumentParser(prog="bot",description="SELENIUM BOT")

    parser.add_argument("-d","--dev",help="(optional) set developer mode",default=False,action='store_true')
    
    parser.add_argument("-c","--chrome", action='store_true', help="(optional) select chrome as webdriver",default=None)
    parser.add_argument("-e","--edge", action='store_true' ,help="(optional) select edge as webdriver",default=None)
    parser.add_argument("-f","--firefox", action='store_true' ,help="(optional) select firefox as webdriver",default=None)
    
    parser.add_argument("-dry","--dry-run", action='store_true' ,help="(optional) run the bot without buying anything",default=False)
    
    parser.add_argument("-cpu","--cpus", action='store_true' ,help="(optional) set num of proccessors",default=False)
    
    parser.add_argument("-p","--path",type=str ,help="(optional) custom path to webdriver",default=settings.DRIVER_PATH)
    
    args = parser.parse_args()
    if args.chrome:
        settings.WEBDRIVER = settings.CHROME
    elif args.edge:
        settings.WEBDRIVER = settings.EDGE
    elif args.firefox:
        settings.WEBDRIVER = settings.FIREFOX
    else:
        settings.WEBDRIVER = settings.CHROME
        
    settings.DEV = args.dev
    settings.DRY_RUN = args.dry_run
    
    settings.DRIVER_PATH = args.path
    settings.OS = platform.system()
    settings.DRIVER_PATH += "chromedriver" if settings.WEBDRIVER == settings.CHROME else 'msedgedriver'
    settings.DRIVER_PATH += ".exe" if settings.OS == settings.WINDOWS else ''
if __name__ == "__main__":
    try:
        pre_run()
        main()
    except (SystemExit):
        pass
