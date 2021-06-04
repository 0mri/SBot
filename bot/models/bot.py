from captcha_solver import CaptchaSolver
from bot.models.config import Config
from bot.models.logger import Logger
from msedge.selenium_tools import Edge, EdgeOptions
import bs4
from selenium import webdriver
from seleniumrequests import Chrome 
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from fake_useragent import UserAgent
from bot import settings
import schedule
import time
import threading
import os,sys
class Bot:
    PROTECTOR = None
    
    NUM_OF_CAPTCHA = 0
    LAST_TIME_CAPTCHA = None
    VPN_COMMANDS = CENNECT, CHANGE_IP, DISCONNECT = ('connect', 'changeip', 'disconect')
    def __init__(self, logger: Logger):
        self.___cfg___ = Config(path='')
        self.___cfg___.load()
        self._config = self.___cfg___.config
        self.load_cfg()
        self.logger = logger
        self.initialize()
        # self.schedule = schedule
    def initialize(self):
        if settings.WEBDRIVER:
            self.webdriver = settings.WEBDRIVER
        self.headless = not settings.DEV
        if self._config.get('2captcha',None):
            api_key = self._config['2captcha']['api_key']
            self._solver = CaptchaSolver('2captcha', api_key=api_key)
            
        schedule.every(10).minutes.do(self.VPN,(Bot.CHANGE_IP)).tag('change_ip')
        
        #Start Backgroud Tasks
        self.run_continuously()
         
    def run(self):
        raise NotImplementedError()
    
    def captcha(self, base64_img):
        Bot.NUM_OF_CAPTCHA += 1
        print("captcha num", Bot.NUM_OF_CAPTCHA)
        Bot.LAST_TIME_CAPTCHA = time.time()
        try:
            solved_captcha = self._solver.solve_captcha(base64_img)
            return solved_captcha
        except:
            self.logger.error("Error sloving captcha")
        if(Bot.NUM_OF_CAPTCHA >=5 or time.time()-Bot.LAST_TIME_CAPTCHA < 20):
            self.VPN(Bot.CHANGE_IP)
            time.sleep(5)
            Bot.NUM_OF_CAPTCHA = 0
    
    
    def login(self):
        raise NotImplementedError()
        
    def __create_driver__(self):
        if(self.webdriver == settings.CHROME):
            options = webdriver.ChromeOptions()
            if(self.headless or settings.HEADLESS):
                options.add_argument('headless')
            options.add_argument("window-size=1920,1080")
            options.add_argument("--log-level=3")
            
            caps = DesiredCapabilities().CHROME
            # caps["pageLoadStrategy"] = "normal"  #  complete
            caps["pageLoadStrategy"] = "eager"  #  interactive
            
            prefs = {'profile.default_content_setting_values': { 'javascript': 0, 'stylesheet': 2, 
                                                                'images': 2,
                            'plugins': 2, 'popups': 2, 'geolocation': 2, 
                            'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2, 
                            'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 
                            'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 
                            'ppapi_broker': 2, 'automatic_downloads': 2, 'midi_sysex': 2, 
                            'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2, 
                            'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 
                            'durable_storage': 2}}
            options.add_experimental_option('prefs', prefs)
            options.add_argument(f'user-agent={UserAgent().random}')
            options.add_argument("start-maximized")
            options.add_argument("disable-infobars")
            options.add_argument("disable-gpu")
            options.add_argument("disable-extensions")
            
            driver = Chrome(desired_capabilities=caps,executable_path=settings.DRIVER_PATH,options=options)
            self.logger.debug(f"creating chromedriver for {self.__class__.__name__}", False)
            return driver
        elif(self.webdriver == settings.EDGE):
            options = EdgeOptions()
            if(self.headless or settings.HEADLESS):
                options.headless = True
            options.add_argument("window-size=1920,1080")
            options.add_argument("--log-level=3")
            driver = Edge(executable_path=settings.DRIVER_PATH, options=options)
            self.logger.debug(f"creating msedgedriver for {self.__class__.__name__}", False)
            return driver
        
    def get(self,url, protect=True, xhr=False):
        if xhr:
            response = self.driver.request('GET', url, timeout=2)
            self.logger.debug(f"xhr request: {url}")
            Bot.PROTECTOR(source=bs4.BeautifulSoup(response.text,'html.parser')) if Bot.PROTECTOR is not None and protect else None
            return response
        else:
            self.logger.debug(f"getting {url}")
            self.driver.get(url)
            Bot.PROTECTOR() if Bot.PROTECTOR is not None and protect else None
        # self.driver.execute_script('localStorage.setItem("aatc_mask_show2",1)')
        
        #popupcloser
        self.close_popup()
    def close_popup(self):
        try:
            self.driver.find_element_by_xpath(f"//div[@class='centerPopup-body']")
            self.driver.find_element_by_xpath(f"//a[@class='fas fa-times centerPopup-close']").click()
            self.logger.debug("Popup Closed!")
        except:
            pass
        
    def click(self,tag='button', _class = None, text = None):
        if(_class):
            self.logger.debug(f"//{tag}[@class='{_class}']")
            self.driver.find_element_by_xpath(f"//{tag}[@class='{_class}']").click()
        self.driver.find_element_by_xpath(f"//{tag}[text()='{text}']").click()
        
        
    def wait(self, _id):
        tmp = WebDriverWait(self.driver, 3.5, 0.1)
        tmp.until(ec.visibility_of_element_located((By.ID, _id)))
        
    def wait_short(self, _id):
        self.wait_short.until(ec.visibility_of_element_located((By.ID, _id)))
        
    def wait_long(self, _id):
        self.wait_long.until(ec.visibility_of_element_located((By.ID, _id)))
        
    def xpath(self, *args, **kwargs):
        if(len(args)==3):
            tag, attr, val = args
            self.log.debug(f"finding element <{tag} {attr}='{val}'>")
            try:
                return self.driver.find_element_by_xpath(f"//{tag}[@{attr}='{val}']")
            except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as err:
                self.log.error(f"cannot find element <{tag} {attr}='{val}'>")
                raise err
        elif(len(args)==2):
            tag, text = args
            self.log.debug(f"finding element <{tag}>{text}</{tag}>")
            try:
                return self.driver.find_element_by_xpath(f"//{tag}[text()='{text}']")
            except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as err:
                self.log.error(f"cannot find element <{tag}>{text}</{tag}>")
                raise err
        
    def screenshot(self, name):
        # self.driver.maximize_window()
        path = f"bot/{self.__class__.__name__.lower()}/screenshot/{name}.png"
        ans = self.driver.save_screenshot(path)
        self.logger.info("",attach=f"{path}")
        if ans:
            self.logger.debug(f"Screenshot saved in - {path}")
        else:
            self.logger.error(f"Error taking screenshot")
            self.logger.debug(path)
            
        

    def run_continuously(self,interval=1):
        """Continuously run, while executing pending jobs at each
        elapsed time interval.
        @return cease_continuous_run: threading. Event which can
        be set to cease continuous run. Please note that it is
        *intended behavior that run_continuously() does not run
        missed jobs*. For example, if you've registered a job that
        should run every minute and you set a continuous run
        interval of one hour then your job won't be run 60 times
        at each interval but only once.
        """
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            def __init__(self, *args,**kwargs):
                        super().__init__(*args,**kwargs)
            @classmethod
            def run(cls):
                try:
                    while not cease_continuous_run.is_set():
                        schedule.run_pending()
                        time.sleep(interval)
                except:
                    cease_continuous_run.set()
            @classmethod        
            def stop(cls):
                cease_continuous_run.set()


        self.scheduler  = ScheduleThread()
        self.scheduler.start()
        
        
    def VPN(self,connect=None,disconnect=None,change_ip=CHANGE_IP):
        self.logger.info("Changing IP address")
        cmd = connect or disconnect or change_ip
        os.system(f'"HMA! Pro VPN.exe" -'+cmd)