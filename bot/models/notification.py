import queue
import threading
from os import path
from bot.settings import APPRISE_CONFIG_PATH, URGENTBOT_CONFIG_PATH, USERNAME
import apprise


class NotificationHandler:
    def __init__(self, enabled=True, name=""):
        self.name = name
        if enabled and path.exists(APPRISE_CONFIG_PATH):

            self.apobj = [apprise.Apprise(), apprise.Apprise()]
            config = [apprise.AppriseConfig(), apprise.AppriseConfig()]
            config[0].add(APPRISE_CONFIG_PATH)
            config[1].add(URGENTBOT_CONFIG_PATH)
            self.apobj[0].add(config[0])
            self.apobj[1].add(config[1])

            self.queue = queue.Queue()
            self.start_worker()
            self.enabled = True
        else:
            self.enabled = False

    def start_worker(self):
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        while True:
            message, attachments, num = self.queue.get()
            print(num)
            if attachments:
               
                self.apobj[num].notify(
                    title=self.name, body=message, attach=attachments)
            else:
                self.apobj[num].notify(title=self.name, body=message)
            self.queue.task_done()

    def send_notification(self, message, attachments=None, urgent=False):
        if self.enabled:
            self.queue.put((f"{USERNAME}: " + message, attachments or [], int(urgent)))

