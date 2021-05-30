from captcha_solver import CaptchaSolver
from selenium import webdriver
from bot.models.config import Config
from bot.models.logger import Logger

class Bot:
    def __init__(self, logger: Logger):
        self.log = logger
        self.config = Config('').config
        # self.initialize()
    def initialize(self):
        api_key = self.config['2captcha']['api_key']
        self._solver = CaptchaSolver('2captcha', api_key=api_key)
        pass
        
    def run(self):
        raise NotImplementedError()
    
    def captcha(self, base64_img):
        try:
            solved_captcha = self._solver.solve_captcha(base64_img)
            return solved_captcha
        except:
            pass
        
    def _create_driver_(self):
        self.log.info(f"Creating Driver For {self.__class__.__name__}", False)
        driver = webdriver.Chrome()
        return driver

    def driver(self):
        return self.driver
    
    def login(self):
        raise NotImplementedError()
        