from bot.models.config import Config
from bot.models.bot import Bot
from bot.models.logger import Logger
from bot.models.config import Config
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import bs4
import base64
from rich.table import Table
import schedule
import email
from email.header import decode_header
import os
import time
import datetime
import json
from ruamel import yaml
from multiprocessing.pool import ThreadPool
from multiprocessing.process import current_process
from multiprocessing import cpu_count, Value, Manager
from .helpers import extract_item
from bot import settings
from bot.newegg.decorators.decorators import synchronized
import sys
import re
import socket
is_found = Value('i', 0)
success = False


class Newegg(Bot):

    class Item:
        def __init__(self, dict_item: dict):
            """return Item object from newegg dict_item"""
            self.init(*extract_item(dict_item).values())

        def init(self, is_combo, _id, name, price, currency, link, image, in_stock):
            self.is_combo = is_combo
            self.id = _id
            self.name = name
            self.price = price
            self.currency = currency
            self.link = link
            self.image = image
            self.in_stock = in_stock

        def in_range(self):
            return self.price in range(self.price_min, self.price_max)

        def is_in_stock(self) -> bool:
            return self.in_stock

        def __str__(self):
            return f"{self.name} - {self.currency}{self.price}"

        def __repr__(self):
            return f"{self.name} - {self.currency}{self.price}"

        @classmethod
        def is_item(cls, item: dict):
            return extract_item(item) is not None

    INSTANCE = 1
    BOT_PROTECTION_INTERVAL = 1
    SEARCH_INTERVAL = 3
    FETCH_MAIL_INTERVAL = 0

    def __init__(self, query=None, test=False, *args, **kwargs):
        self.is_test = test
        self.id = Newegg.INSTANCE
        # Newegg.INSTANCE += 1
        self.logger = Logger(logging_service=self.__class__.__name__,
                             instance=self.id, enable_notifications=True)

        self.__cfg__ = Config(path=self.__class__.__name__.lower())
        self.load_cfg(query)
        self.__items__ = Config(
            custom_path=f"{self.__class__.__name__}/data/items.yml")
        self.load_items()
        
        
        super(Newegg, self).__init__(self.logger)
        

        self.__init_mail__()
    def load_items(self):
        self.__items__.load()
        self.items = self.__items__.config or []

    def save_items(self):
        self.__items__.save(self.items)
        self.load_items()

    def load_cfg(self, query=None):
        self.__cfg__.load()

        self.config = self.__cfg__.config
        # User Details
        self.username = self.config['username']
        self.password = self.config['password']
        self.cvv = self.config['cvv']

        # Search Query
        newegg = self.config['newegg'][self.id-1]
        if(query):
            self.search_query = query
        elif(newegg.get('query', None)):
            self.search_query = newegg['query']
        self.price_min = newegg['price_min']
        self.price_max = newegg['price_max']
        self.category = newegg['category_id']
    def stop(self):
        self.driver.quit()
        schedule.clear()
        self.scheduler.stop()
        

    def start(self, timeout=sys.maxsize):
        Bot.PROTECTOR = self.bot_protector
        self.driver = self.__create_driver__()
        

        self.VPN()
        
        self.get('https://www.newegg.com', protect=False) if not settings.CAPTCHA else self.got_to_captcha()
                
                
       


        self.logger.info(
            f"Searchig for {self.search_query.upper()} between ${self.price_min} - ${self.price_max}")
        # self.__create_driver__()
         # MAIN FLOW
        start_time = time.time()
        
        results = []
        while True not in results:
            self.load_items()
            pool = ThreadPool(processes=max(
                min(len(self.items), cpu_count()-1), 5))
            results = []
            start_req_time = time.time()
            for i, item in enumerate(self.items):
                results.append(pool.apply_async(
                    func=self.add_to_cart, args=[self.items[i]]))
            results.append(pool.apply_async(func=self.__search__))
            pool.close()
            pool.join()
            results = [r.get() for r in results]
            if('Human' in results or time.time() >= start_time + timeout*60):
                self.stop()
                return False, round(time.time() - start_time)

            self.logger.debug(f"{len(results)} requests in  {time.time() - start_req_time} seconds")


        self.validate_cart()
        schedule.clear()
        self.logger.info(f"There is item available!!!", True)
        cart_url = f"https://secure.newegg.com/shop/cart"
        # self.get(cart_url)
        now = time.time()

        # self.driver.find_element_by_xpath("//button[@class='btn btn-primary btn-wide']").click()
        # time.sleep()
        # self.close_popup()
        # self.driver.find_element_by_xpath("//button[@class='btn btn-primary btn-wide']").click()
        while('Shopping Cart' in self.driver.title):
            self.logger.debug("clicking checkout btn")
            try:
                self.driver.execute_script(
                    "return document.getElementsByClassName('btn btn-secondary')[0].click()")
            except:
                try:
                    self.driver.execute_script(
                        "return document.getElementsByClassName('btn btn-primary btn-wide')[0].click()")
                except:
                    pass
            time.sleep(0.3)

        is_refreshed, is_logged_in = self.login(
            with_direct=False) or (False, False)
        if is_logged_in:
            self.logger.info(f"Logged In!")
            if(is_refreshed):
                self.js_click(_class='btn btn-primary btn-wide', timeout=5)
            self.type_cvv()
            table = self.fetch_table()
            self.logger.print(table)

            self.place_order() if not settings.DRY_RUN else None
            self.logger.info(f"took {time.time() - now}  seconds")
            order_num = self.get_order_num() if not settings.DRY_RUN and self.is_success(
            ) else f"FAILED_ORDER#{self.get_timestamp()[7:]}"

            self.screenshot(name=order_num)
            # time.sleep(1)
            global success
            success = True
        else:
            self.logger.error("There was an error with login, quit...")

        if(not settings.DEV):
            self.driver.quit()

        time.sleep(3)
        self.scheduler.stop()
        return (success, time.time()-now)

    def login(self, with_direct=True):
        LOGIN_URL = 'https://secure.newegg.com/NewMyAccount/AccountLogin.aspx?'
        attemps = 1
        email_step = False
        verification_step = False
        is_refreshed = False
        v_attempts = 0
        while True and attemps < 500:
            self.bot_protector()
            if with_direct and email_step:
                self.get(LOGIN_URL)
                is_refreshed = True

            # if attemps == 50:
            #     self.got_to_captcha()
            #     attemps = 0
            self.logger.debug(f"login attempt {attemps}")
            # Logging Into Account.
            # self.logger.info(f"Typing Email Address...")
            try:
                # wait_short = WebDriverWait(self.driver, 2.5, 0.1)
                # wait_short.until(ec.visibility_of_element_located((By.ID, "labeled-input-signEmail")))
                email_field = self.driver.find_element_by_id(
                    "labeled-input-signEmail")
                if email_field.get_attribute("value") != self.username:
                    email_step = False
                    email_field.clear()
                    email_field.send_keys(self.username)
                if(self.driver.find_element_by_xpath("//button[@id='signInSubmit']").is_enabled()):
                    email_field.send_keys(Keys.ENTER)
                    email_step = True
                    time.sleep(1)
                    # self.js_click(_id='signInSubmit',timeout=8)

                # self.js_set_val(self.username,'labeled-input-signEmail',timeout=8)
            except (NoSuchElementException, TimeoutException, Exception):
                pass
                # self.logger.error("EMAIL ADDRESS")

            # Verification Code

            try:
                form_verify_array = self.driver.find_element_by_xpath(
                    "//div[@class='form-v-code']").find_elements_by_xpath('//input')
                v_attempts += 1
                # wait_short = WebDriverWait(self.driver, 2.5, 0.1)
                # wait_short.until(ec.visibility_of_element_located((By.CLASS_NAME, "form-v-code")))
                self.logger.info(f"Fetching Verification Code...")
                verify_code = self.__get_mail_verification_code__()
                for i in range(len(verify_code)):
                    if i == len(verify_code):
                        break
                    form_verify_array[i].send_keys(verify_code[i])
                login = self.driver.find_element_by_xpath(
                    "//button[@id='signInSubmit']").click()
                return (is_refreshed, True)
            except:
                pass
            if(v_attempts >= 2):
                v_attempts = 0
                self.driver.refresh()

            # # Password
            # self.logger.info(f"Typing Password...")
            if(email_step):
                try:
                    # self.js_set_val(self.password,'labeled-input-password',timeout=3)
                    # self.js_click(_id='signInSubmit',timeout=3)
                    # wait_short = WebDriverWait(self.driver, 1, 0.1)
                    # wait_short.until(ec.visibility_of_element_located(
                    #     (By.ID, "labeled-input-password")))
                    password_field = self.driver.find_element_by_id(
                        "labeled-input-password")
                    password_field.send_keys(self.password)
                    # password_field.send_keys(Keys.ENTER)
                    self.driver.find_element_by_xpath(
                        "//button[@id='signInSubmit']").click()
                    return (is_refreshed, True)
                except (NoSuchElementException, TimeoutException):
                    # self.logger.error("Couldnt login to account with password.")
                    pass
            attemps += 1
            time.sleep(0.01)

    def js_click(self, _id=None, _class=None, timeout=3):
        if _id:
            js = f"document.getElementById('{_id}').click()"
        elif(_class):
            js = f"document.getElementsByClassName('{_class}')[0].click()"
        if not self.timeout_js(js, timeout):
            raise Exception
        return True

    def js_set_val(self, val, _id=None, _class=None, timeout=3):
        if _id:
            js = f"document.getElementById('{_id}').value = '{val}'"
        elif(_class):
            js = f"document.getElementsByClassName('{_class}')[0].value = '{val}'"
        if not self.timeout_js(js, timeout):
            raise Exception
        return True

    def timeout_js(self, js, timeout):
        _timeout = time.time() + timeout
        while time.time() < _timeout:
            try:
                self.driver.execute_script(js)
                return True
            except:
                pass
        return False

    def add_to_cart(self, item):
        global is_found
        if bool(is_found.value):
            return True
        # self.get(url)
        add_url = f"https://secure.newegg.com/Shopping/AddtoCart.aspx?Submit=ADD&ItemList={item}"
        try:
            response = self.get(add_url, xhr=True)
            html = response.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            self.logger.debug(soup.title.text)
            if(soup.title.text == 'Are you a human?' or soup.title.text == 'Forbidden: 403 Error'):
                self.logger.debug(soup.title.text)
                return 'Human'
            cart_items = self.get_cart_items(source=html)
            if cart_items:
                return True
        except:
            pass

        self.logger.debug(f"item {item} is not available yet :(")
        return False
        # time.sleep(0.1)

    def get_cart_items(self, source=None):
        cart_url = 'https://secure.newegg.com/shop/cart'
        if not source:
            res = self.get(cart_url, xhr=True)
        html = source if source else res.text
        soup = bs4.BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        js = json.loads(soup.html.find('script', text=re.compile(
            'window.__initialState__ = ')).string.replace("window.__initialState__ = ", ""))

        return js['CartInfo']['ActiveItemList']

    def validate_cart(self):
        self.driver.get('https://secure.newegg.com/shop/cart')
        cart_items = self.get_cart_items(self.driver.page_source)


        self.logger.debug(f"there {'is' if len(cart_items) == 1 else 'are'} {len(cart_items)} {'item' if len(cart_items) == 1 else 'items'} in the cart")
        
        min_item = min(cart_items, key=lambda x: x['ItemMathInfo']['FinalUnitPrice'])
        for item in cart_items:
            if item == min_item:
                self.set_qty(item, 1)
            else:
                self.logger.debug(f"removing {item['ItemDetailInfo']['LineDescription']}...")
                self.set_qty(item, -1)

    def set_qty(self, item, qty):
        """
        set quantity for an item in the cart,
        -1 for delete
        """
        fetch_data = {
            "headers": {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "sec-ch-ua": "\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"91\", \"Chromium\";v=\"91\"",
                "sec-ch-ua-mobile": "?0",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "x-requested-with": "XMLHttpRequest"
            },
            "referrer": "https://secure.newegg.com/shop/cart",
            "referrerPolicy": "unsafe-url",
            "body":  json.dumps({'Actions': [{'ActionType': 'UpdateItemQty', 'JsonContent': json.dumps({'ActionType': 'UpdateItemQty', 'Items': [{'ItemKey': item['ItemKey'], 'ItemNumber': item['ItemNumber'], 'Quantity': qty}]})}]}),
            "method": "POST",
            "mode": "cors",
            "credentials": "include"
        }
        fetch_str = 'fetch("https://secure.newegg.com/shop/api/InitCartApi", {})'.format(
            json.dumps(fetch_data))

        self.driver.execute_script(fetch_str)

    def type_cvv(self):
        while(True):
            self.bot_protector()
            try:
                wait = WebDriverWait(self.driver, 5, 0.1)
                wait.until(ec.visibility_of_element_located(
                    (By.XPATH, "//input[@class='form-text mask-cvv-4'][@type='text']")))
                self.logger.info(f"Typing CVV Number...")
                security_code = self.driver.find_element_by_xpath(
                    "//input[@class='form-text mask-cvv-4'][@type='text']")
                security_code.send_keys(
                    Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + str(self.cvv))
                return
            except (AttributeError, NoSuchElementException, TimeoutException, ElementNotInteractableException):
                self.logger.error("CVV")
            time.sleep(0.5)

    def fetch_table(self):
        wait = WebDriverWait(self.driver, 2, 0.1)
        try:
            wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//div[@class='summary-content']")))
            soup = self.extract_page()
            summary = soup.find('div', 'summary-content').find_all('li')
            item_container = soup.find('div', "item-container",)
            item_details = {
                "name": item_container.find("p", "item-title").text,
                "qty": item_container.find("div", "item-qty").text,
                "price": summary[0].span.text,
                "delivery": summary[1].span.text,
                "total": soup.find('li', 'summary-content-total').span.text
            }
            try:
                item_details["vat"] = summary[3].find_all('span')[1].text
            except:
                item_details["vat"] = "$0"
            row = item_details.values()
            cols = [key.capitalize() for key in item_details.keys()]
            return self.logger.table(columns=cols, rows=[row], title="Order Summary")
        except:
            self.logger.error("FETCHONG TABLE")
            return None

    def extract_page(self):
        html = self.driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        return soup

    def place_order(self):
        try:
            # wait.until(ec.visibility_of_element_located((By.XPATH, "//button[text()='Place Order']")))
            self.driver.find_element_by_xpath(
                "//button[text()='Place Order']").click()
            self.logger.info(f"Waiting For Order Confirmation...")
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
            self.logger.error("PLACEORDER")

    def is_success(self):
        try:
            wait = WebDriverWait(self.driver, 45)
            wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//span[@class='message-title']")))
            message = self.driver.find_element_by_xpath(
                "//span[@class='message-title']").text
            if(message == 'THANK YOU FOR YOUR ORDER!'):
                self.logger.info(f"{message}")
                return True
        except:
            return False

    def get_order_num(self):
        order_num = self.driver.find_element_by_xpath(
            "//label[text()='Order #: ']").text.replace(":", "").replace(" ", "").upper()
        return order_num

    @synchronized
    def bot_protector(self, source: bs4.BeautifulSoup = None):
        title = source.title.text if source else self.driver.title
        if title == 'Forbidden: 403 Error':
            # self.VPN()
            self.driver.get('www.newegg.com')
        if title != 'Are you a human?':
            return
        while(self.driver.title == 'Are you a human?'):
            wait = WebDriverWait(self.driver, 30, 0.1)
            self.logger.info("Bot detection is activated")
            try:
                wait.until(ec.visibility_of_element_located(
                    (By.ID, "imageCode")))
                html = self.driver.page_source
                soup = bs4.BeautifulSoup(html, 'html.parser')
                time.sleep(1.5)
                _captcha = self.driver.find_element_by_xpath(
                    "//img[@id='imageCode']").get_attribute('src')
                image_type, image_content = _captcha.split(',', 1)
                self.logger.info("Fetching Captcha...")
                start_time = time.time()
                solved_captcha = self.captcha(base64.b64decode(image_content))
                self.driver.find_element_by_xpath(
                    "//input[@id='userInput']").send_keys(solved_captcha)
                self.driver.find_element_by_xpath(
                    "//input[@id='verifyCode']").click()
                time.sleep(0.5)
                try:
                    alert = self.driver.switch_to_alert()
                    self.logger.info(
                        f"Wrong Captcha Trying Again - {solved_captcha}  - {round(time.time()-start_time)}s")
                    alert.accept()
                except:
                    self.logger.info(
                        f"Captcha Solved - {solved_captcha} - {round(time.time()-start_time)}s")
                    break
                time.sleep(1)
            except:
                self.driver.refresh()
                time.sleep(3)

    def __search__(self):
        self.load_cfg()

        try:
            show_in_stock_only = False
            url = f"https://www.newegg.com/p/pl?d={self.search_query.replace(' ', '+')}&N={self.category}{'%204131 'if show_in_stock_only else ''}&PageSize=96&Order=1"
            response = self.get(url, xhr=True)
            html = response.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            self.logger.debug(soup.title.text)
            if(soup.title.text == 'Are you a human?' or soup.title.text == 'Forbidden: 403 Error'):
                return "Human"
            self.logger.debug(f"Searching for {self.search_query.upper()}")

            scripts = soup.find_all('script')
            js_items = json.loads(soup.html.find('script', text=re.compile(
                'window.__initialState__ = ')).string.replace("window.__initialState__ = ", ""))['Products']

            items_obj = [self.Item(item) for item in js_items if self.Item.is_item(item)]
                
            # items = soup.find_all('div', 'item-cell')
            # items_obj = [self.Item(item_cell)
            #              for item_cell in items if self.Item.is_item(item_cell)]

            in_stock = [item for item in items_obj if item.in_stock]
            self.logger.debug(f"in stock items: \n{in_stock}")
            # print(items_obj)
            # temp_items = [extract_item(item) for item in items]
            # items_ids = [item['id'] for item in temp_items if item is not None and item['price'] in range(self.price_min, self.price_max)]
            relevant_items = [item for item in items_obj if round(item.price) in range(
                self.price_min, self.price_max) and item.id not in self.items and item.in_stock]
            if len(relevant_items):
                self.logger.info(f"Found {len(relevant_items)} items")
                self.logger.info(f"{relevant_items}")
                self.items = [item.id for item in relevant_items] + self.items
                self.save_items()
        except:
            pass

    def got_to_captcha(self):
        cur_url = self.driver.current_url
        url = 'https://www.newegg.com/areyouahuman3?itn=true&referer=https%3A%2F%2Fwww.newegg.com%2FComponents%2FStore&why=8'
        self.get(url)
        
        # self.VPN()
        # self.get(cur_url)

    def __get_mail_verification_code__(self):
        # print("FETCHING VERIFICATION CODE...")
        timeout = time.time() + 1*20
        while time.time() < timeout:
            # socket.setdefaulttimeout(10)
            # authenticate
            status, messages = self.imap.select("INBOX")
            # number of top emails to fetch
            N = 1
            # total number of emails
            messages = int(messages[0])

            for i in range(messages, messages-N, -1):
                # fetch the email message by ID
                res, msg = self.imap.fetch(str(i), "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        # parse a bytes email into a message object
                        msg = email.message_from_bytes(response[1])
                        # decode the email subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        print(subject)
                        if subject == 'Newegg Verification Code':
                            # if the email message is multipart
                            if msg.is_multipart():
                                # iterate over email parts
                                for part in msg.walk():
                                    # extract content type of email
                                    content_type = part.get_content_type()
                                    content_disposition = str(
                                        part.get("Content-Disposition"))
                                    try:
                                        # get the email body
                                        body = part.get_payload(
                                            decode=True).decode()
                                    except:
                                        pass
                                    if content_type == "text/plain" and "attachment" not in content_disposition:
                                        # print text/plain emails and skip attachments
                                        print(body)
                                    elif "attachment" in content_disposition:
                                        # download attachment
                                        filename = part.get_filename()
                                        if filename:
                                            folder_name = "".join(
                                                c if c.isalnum() else "_" for c in subject)
                                            if not os.path.isdir(folder_name):
                                                # make a folder for this email (named after the subject)
                                                os.mkdir(folder_name)
                                            filepath = os.path.join(
                                                folder_name, filename)
                                            # download attachment and save it
                                            open(filepath, "wb").write(
                                                part.get_payload(decode=True))
                            else:
                                # extract content type of email
                                content_type = msg.get_content_type()
                                # get the email body
                                body = msg.get_payload(decode=True).decode()
                                if content_type == "text/plain":
                                    # print only text email parts
                                    print(body)
                            if content_type == "text/html":
                                soup = bs4.BeautifulSoup(body, 'html.parser')

                                verification_code = soup.table.table.tbody.find_all('tr')[0].td.find_all(
                                    'table')[0].find_all('td')[2].find_all('table')[0].tbody.find_all('tr')[4].td.text
                                # print(f"found mail from NewEgg Verification Code: {verification_code}")
                                # Delete The Mail
                                self.imap.store(str(i), "+FLAGS", "\\Deleted")
                                self.imap.logout()
                                return verification_code
                                # open(filepath, "w").write(body)
                                # open in the default browser
                    else:
                        pass
                        # print('mail from NewEgg is not found, fetch new mails...')
                time.sleep(Newegg.FETCH_MAIL_INTERVAL)

    def get_timestamp(self):
        return str(datetime.datetime.timestamp(datetime.datetime.now())).replace('.', '')
    
    def __create_schedule__(self):
        pass
        # schedule.every(0.5).seconds.do(self.__search__).tag('search')
        # schedule.every(2).minutes.do(self.VPN)

        # schedule.every(1).hours.do(self.VPN).tag('change_ip')
        # schedule.every(1).hours.do(self.got_to_captcha).tag('captcha')
        # schedule.every(3).seconds.do(self.bot_protector).tag('protector')
        # schedule.every(1).minutes.do(self.__create_driver__).tag('driver')


    def VPN(self):
        schedule.clear()
        cur_ip, isp = self.get_ip()
        # cmd = Bot.CENNECT if connect else Bot.DISCONNECT if disconnect else Bot.CHANGE_IP
        os.system(f'"HMA! Pro VPN.exe" -disconnect')
        orginal_ip = None
        while(not orginal_ip or isp != 'BEZEQINT'):
            try:
                orginal_ip,isp = self.get_ip()
                print("1",orginal_ip)
            except:
                pass
            time.sleep(1)
        new_ip = orginal_ip
        os.system(f'"HMA! Pro VPN.exe" -connect')
        while(new_ip == orginal_ip):
            try:
                new_ip,isp = self.get_ip()
                print('2',new_ip)
            except:
                pass
            time.sleep(1)
        self.__init_mail__()
        time.sleep(10)
        self.__create_schedule__()
        
    def __str__(self):
        return f"NEWEGG[{self.id}]"
