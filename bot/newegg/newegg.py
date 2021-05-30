from bot.models.config import Config
from bot.models.bot import Bot
from bot.models.logger import Logger
from bot.models.config import Config


class Newegg(Bot):
    instance = 1

    def __init__(self, *args, **kwargs):
        self.id = Newegg.instance
        Newegg.instance += 1
        self.logger = Logger(logging_service=self.__class__.__name__,
                             instance=self.id, enable_notifications=False)
        self.config = Config(self.__class__.__name__.lower()).config
        super(Newegg, self).__init__(self.logger)
        self.driver = self._create_driver_()
        
    def run(self):
        self.logger.info(f"{self.__class__.__name__} Bot is Running!")
        # self.driver.get('https://google.com')
        while True:
            pass

    def login(self):
        pass

    def __str__(self):
        return ''
