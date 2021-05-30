from captcha_solver import CaptchaSolver



class Bot:
    def __init__(self, logger: Logger, config: Config):
        self.logger = logger
        self.config = config

    def initialize(self):
        api_key = self.config['2captcha']['api_key']
        self._solver = CaptchaSolver('2captcha', api_key=api_key)
        
        
    def captcha(self, base64_img):
        _2captcha_api_key = se['2captcha']['api_key']
        solver = CaptchaSolver('2captcha', api_key=_2captcha_api_key)