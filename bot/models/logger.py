import logging

from .notification import NotificationHandler
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table
from random import shuffle
class Logger:
    Logger = None
    NotificationHandler = None
    COLORS = PURPLE, YELLOW, GREEN, WHITE, RED = ['purple', 'yello', 'green', 'white', 'red']
    def __init__(self, logging_service="",instance=None, enable_notifications=True, color='purple'):
        
        self.name = logging_service
        self.instance = instance
        shuffle(Logger.COLORS)
        self.color =  Logger.COLORS.pop()
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
            self.console.log(f"[{self.color}] [{self.instance}][{self.name.upper()}] [/{self.color}]{message}")
        elif level == "warning":
            self.Logger.warning(message)
            self.console.log(f"[{self.color}] [{self.name.upper()}] [/{self.color}]{message}",style="yellow")
        elif level == "error":
            self.Logger.error(message)
            self.console.log(f"[{self.color}] [{self.name.upper()}] [/{self.color}]{message}",style="red")
        elif level == "debug":
            self.Logger.debug(message)
            self.console.log(f"[{self.color}] [{self.name.upper()}] [/{self.color}]{message}",style="green")

        if notification and self.NotificationHandler.enabled:
            self.NotificationHandler.send_notification(message=message,attachments=attach)
            
    def print(self, message):
        self.console.print(message)
        
    def notify(self, attach):
        self.NotificationHandler.send_notification(message=None, attachments=attach)

    def info(self, message, notification=True, attach=None):
        self.log(message=message, level="info", notification=notification, attach=attach)

    def warning(self, message, notification=True):
        self.log(message, "warning", notification=notification)

    def error(self, message, notification=True):
        self.log(message, "error", notification)

    def debug(self, message, notification=True):
        self.log(message, "debug", notification)
        
    def table(self, columns, rows, title=None):
        table = Table(*columns,title=title,show_lines=True)
        for row in rows:
            table.add_row(*row)
                
        return table
    def console(self):
        return self.console


