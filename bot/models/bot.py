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
from bot import settings
import schedule
import time
import threading
class Bot:
    PROTECTOR = None
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
        self.notify = self._config['notify']
        self.headless = (not settings.DEV) or self._config['headless']
        if self._config.get('2captcha',None):
            api_key = self._config['2captcha']['api_key']
            self._solver = CaptchaSolver('2captcha', api_key=api_key)
        
        #Start Backgroud Tasks
        self.run_continuously()
         
    def run(self):
        raise NotImplementedError()
    
    def captcha(self, base64_img):
            try:
                solved_captcha = self._solver.solve_captcha(base64_img)
                return solved_captcha
            except:
                self.logger.error("Error sloving captcha")
    
    
    def login(self):
        raise NotImplementedError()
        
        
    def __create_driver__(self):
        print(self.webdriver)
        if(self.webdriver == settings.CHROME):
            options = webdriver.ChromeOptions()
            if(self.headless):
                options.add_argument('headless')
            options.add_argument("window-size=1920,1080")
            options.add_argument("--log-level=3")
            driver = Chrome(executable_path=settings.DRIVER_PATH,options=options)
            self.logger.info(f"creating chromedriver for {self.__class__.__name__} [{self.id}]", False)
            return driver
        elif(self.webdriver == settings.EDGE):
            options = EdgeOptions()
            if(self.headless):
                options.headless = True
            options.add_argument("window-size=1920,1080")
            options.add_argument("--log-level=3")
            self.logger.info(settings.DRIVER_PATH)
            driver = Edge(executable_path=settings.DRIVER_PATH, options=options)
            self.logger.info(f"creating chromedriver for {self.__class__.__name__} [{self.id}]", False)
            return driver
        
    def get(self,url, protect=True):
        self.logger.debug(f"getting {url}")
        self.driver.get(url)
        # self.driver.execute_script('localStorage.setItem("aatc_mask_show2",1)')
        Bot.PROTECTOR() if Bot.PROTECTOR is not None and protect else None
        
        #popupcloser
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
        if ans:
            self.logger.debug(f"Screenshot saved in - {path}")
        else:
            self.logger.debug(f"Error taking screenshot")
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
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)
            def stop(self):
                cease_continuous_run.set()


        self.scheduler  = ScheduleThread()
        self.scheduler.start()