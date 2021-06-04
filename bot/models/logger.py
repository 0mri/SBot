import logging

from .notification import NotificationHandler
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table
from random import shuffle
from . import Config
from bot import settings
class Logger:
    Logger = None
    SHUFFLE_COLORS = False
    COLORS = PURPLE, RED, BLUE, YELLOW, GREEN, MAGENTA  = ['purple','red','bright_blue', 'bright_yellow', 'bright_green', 'bright_magenta']
    def __init__(self, logging_service="",instance=None, enable_notifications=True, color='purple'):
        
        self.name = logging_service
        self.instance = instance
        if(Logger.SHUFFLE_COLORS):
            shuffle(Logger.COLORS)
            self.color =  Logger.COLORS.pop()
        else:
            shuffle(Logger.COLORS)
            self.color =  Logger.COLORS[0]
        # self.color =  'bright_magenta'
        # Logger setup
        self.Logger = logging.getLogger(f"{self.name.lower()}")
        self.Logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(f"./bot/logs/{self.name.lower()}.log")
        formatter = logging.Formatter(f"%(asctime)s - [{self.instance}] - %(levelname)s - %(message)s")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.Logger.addHandler(fh)
        self.console = Console()


        # notification handler
        self.NotificationHandler = NotificationHandler(enabled=enable_notifications, name=logging_service)

    def log(self, message, level="info", notification=True, attach=None):
        if level == "info":
            self.Logger.info(message)
            self.console.log(f"[bright_cyan][INFO][{self.color}]\t[{self.name.upper()}] [/{self.color}]{message}")
        elif level == "warning":
            self.Logger.warning(message)
            self.console.log(f"[bright_yellow][WARNING][{self.color}]\t[{self.name.upper()}] [/{self.color}]{message}",style="yellow")
        elif level == "error":
            self.Logger.error(message)
            self.console.log(f"[bright_red][ERROR][{self.color}]\t[{self.name.upper()}] [/{self.color}]{message}",style="red")
        elif level == "debug" and settings.DEV:
            self.Logger.debug(message)
            self.console.log(f"[bright_green][DEBUG][{self.color}]\t[{self.name.upper()}] [/{self.color}]{message}",style="green")

        if notification and self.NotificationHandler.enabled:
            self.NotificationHandler.send_notification(message=message,attachments=attach)
            
    def print(self, message):
        self.console.print(message)

    def info(self, message, notification=True, attach=None):
        self.log(message=message, level="info", notification=notification, attach=attach)

    def warning(self, message, notification=True):
        self.log(message, "warning", notification=notification)

    def error(self, message, notification=True):
        self.log(message, "error", notification)

    def debug(self, message, notification=False):
        self.log(message, "debug", notification)
        
    def table(self, columns:list, rows: list, title:str =None):
        table = Table(*columns,title=title,show_lines=True)
        for row in rows:
            table.add_row(*row)
                
        return table


