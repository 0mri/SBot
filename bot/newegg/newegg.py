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
import imaplib
import email
from email.header import decode_header
import os
import time
import datetime
import json
from ruamel import yaml
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count
from .helpers import extract_item
from bot import settings
import sys
class Newegg(Bot):
    class Item:
        def __init__(self, *args, **kwargs):
            pass
        
    INSTANCE = 1
    BOT_PROTECTION_INTERVAL = 1
    SEARCH_INTERVAL = 3
    FETCH_MAIL_INTERVAL = 0.1
    
    def __init__(self, query=None, *args, **kwargs):
        self.id = Newegg.INSTANCE
        Newegg.INSTANCE += 1
        self.logger = Logger(logging_service=self.__class__.__name__,instance=self.id, enable_notifications=False)

        self.__cfg__ = Config(path=self.__class__.__name__.lower())
        self.load_cfg(query)
        
        self.__items__ = Config(custom_path=f"{self.__class__.__name__}/data/items.yml")
        self.load_items()
        super(Newegg, self).__init__(self.logger)
        
        self.is_found = False
        # self.logger.debug(f"search_query: {self.search_query.upper()}")
        # self.logger.debug(f"min price: {self.price_min}")
        # self.logger.debug(f"max price: {self.price_max}")
        # self.logger.debug(f"Category ID: {self.category_id}")
    def load_items(self):
        self.__items__.load()
        self.items = self.__items__.config or []
    def save_items(self):
        self.__items__.save(self.items)
        self.load_items()
    def load_cfg(self, query=None):
        self.__cfg__.load()
        
        self.config = self.__cfg__.config
        #User Details
        self.username = self.config['username']
        self.password = self.config['password']
        self.cvv = self.config['cvv']
        
        self.gmail = self.config['gmail']
        #Search Query
        newegg = self.config['newegg'][self.id-1]
        if(query):
            self.search_query = query
        elif(newegg.get('query', None)):
            self.search_query = newegg['query']
        self.price_min = newegg['price_min']
        self.price_max = newegg['price_max']
        self.category = newegg['category_id']

    def start(self):
        self.driver = self.__create_driver__()
        Bot.PROTECTOR = self.bot_protector
        if not self.driver:
            self.logger.error("Driver is not running")
            sys.exit()
        self.logger.info(f"{self.__class__.__name__} Bot is Running!")
        # schedule.every(Newegg.BOT_PROTECTION_INTERVAL).seconds.do(self.bot_protector)
        
        # self.got_to_captcha()
        # self.login()
        
        #MAIN FLOW
        self.get('https://www.newegg.com')
        
        
        self.logger.info(f"Searchig for {self.search_query.upper()} between ${self.price_min} - ${self.price_max}")
        schedule.every(0.1).seconds.do(self._search_).tag('search')
        

        results = []
        while(True not in results):
            self.load_items()
            pool = ThreadPool(processes=max(min(cpu_count()-1,len(self.items)),1))
            results = []
            for i, item in enumerate(self.items):
                results.append(pool.apply_async(func=self.add_to_cart, args=[self.items[i]]))


            pool.close()
            pool.join()
            results = [r.get() for r in results]
            if('Human' in results):
                self.got_to_captcha()
            
        self.logger.info(f"There is item available!!!")
        schedule.clear(tag='search')
        cart_url = f"https://secure.newegg.com/shop/cart"
        self.get(cart_url)
        
        
        self.driver.execute_script("document.getElementsByClassName('btn btn-primary btn-wide')[0].click()")
        
        # checkout_btn = self.driver.find_element_by_xpath("//button[@class='btn btn-primary btn-wide']")
        # if(checkout_btn.is_enabled()):
        #     self.driver.find_element_by_xpath("//button[@class='btn btn-primary btn-wide']").click()
        # else:
        #     self.driver.find_element_by_xpath("//button[@class='btn btn-secondary']").click()
        #     while(not checkout_btn.is_enabled()):
        #         continue
        #     checkout_btn.click()

        
        

        self.login(with_direct=False)
        self.type_cvv()
        table = self.fetch_table()
        self.logger.print(table)

        self.place_order() if not settings.DRY_RUN else None
        
        order_num = self.get_order_num() if not settings.DRY_RUN and self.is_success() else f"FAILED_ORDER#{self.get_timestamp()[7:]}"
        
        self.screenshot(name=order_num)
        self.driver.quit()
        self.scheduler.stop()
    def login(self, with_direct=True):
        LOGIN_URL = 'https://secure.newegg.com/NewMyAccount/AccountLogin.aspx?'
        attemps = 1
        while True:
            if with_direct or attemps>=3:
                self.get(LOGIN_URL)
            # Logging Into Account.
            try:
                wait = WebDriverWait(self.driver, 3.5, 0.1)
                # wait.until('labeled-input-signEmail')
                wait.until(ec.visibility_of_element_located((By.ID, "labeled-input-signEmail")))
                self.logger.info(f"Typing Email Address...")
                
                email_field = self.driver.find_element_by_id("labeled-input-signEmail")
                email_field.clear()
                # time.sleep(0.5)
                email_field.send_keys(self.username)
                email_field.send_keys(Keys.ENTER)
            except (NoSuchElementException, TimeoutException):
                self.logger.error("EMAIL ADDRESS")
            attemps +=1


            # Verification Code
            try:
                wait.until(ec.visibility_of_element_located((By.CLASS_NAME, "form-v-code")))
                self.logger.info(f"Fetching Verification Code...")
                form_verify_array = self.driver.find_element_by_xpath( "//div[@class='form-v-code']").find_elements_by_xpath('//input')
                verify_code = self.__get_mail_verification_code__()
                for i in range(len(verify_code)):
                    if i == len(verify_code):
                        break
                    form_verify_array[i].send_keys(verify_code[i])
                login = self.driver.find_element_by_xpath("//button[@id='signInSubmit']").click()
                self.logger.info(f"Logged In!")
                return True
            except:
                pass

            # # Password
            try:
                wait.until(ec.visibility_of_element_located((By.ID, "labeled-input-password")))
                self.logger.info(f"Typing Password...")
                password_field = self.driver.find_element_by_id("labeled-input-password")
                time.sleep(0.5)
                password_field.send_keys(self.password)
                password_field.send_keys(Keys.ENTER)
                return True
            except (NoSuchElementException, TimeoutException):
                self.logger.error("Couldnt login to account with password.")
                pass            
            
    def add_to_cart(self, item):
        if(self.is_found):
            return True
        # self.get(url)
        add_url = f"https://secure.newegg.com/Shopping/AddtoCart.aspx?Submit=ADD&ItemList={item}"
        response = self.driver.request(method="GET", url=add_url)
        html = response.text
        soup = bs4.BeautifulSoup(html, 'html.parser')
        
        
        if(soup.title.text == 'Are you a human?'):
            self.logger.debug(soup.title.text)
            return 'Human'
            
        scripts = soup.find_all('script')
        try:
            js = [json.loads(sc.string.replace("window.__initialState__ = ","")) for sc in scripts if 'window.__initialState__' in str(sc)][0]
            ItemNumber = js['CartInfo']['ActiveItemList'][0]['ItemNumber']
            ItemKey = js['CartInfo']['ActiveItemList'][0]['ItemKey']
            ItemGroup = js['CartInfo']['ActiveItemList'][0]['ItemGroup']
            Quantity = js['CartInfo']['ActiveItemList'][0]['Quantity']
            self.is_found = True
            return True
        except:
            # self.logger.debug(f"item {item} is not available yet :(")
            return False
            # time.sleep(0.1)
        
        
        # url = 'https://secure.newegg.com/shop/api/CheckoutApi'
        # data = {'ItemList': [{'ItemNumber': ItemNumber, 'ItemKey': ItemKey, 'Quantity': Quantity, 'ItemGroup': ItemGroup}], 'Actions': []}
        # self.logger.debug(data)
        # response = self.driver.request('POST',url, data=data)
        # print(dir(response.request))
        # print(response.json())
    def check_in_cart(self):
        """
        
        return True if there is any item in the cart
        
        """
        
        try:
            available = self.driver.find_element_by_xpath("//*[@class='btn btn-primary btn-wide']").is_enabled()
            if available:
                return True
            if not available:
                pass
                # self.logger.info("Item is not in cart")
        except (TimeoutException, NoSuchElementException) as err:
            pass
            # self.logger.error("Item is not in cart")
    def type_cvv(self):
        try:
            wait = WebDriverWait(self.driver, 5, 0.1)
            wait.until(ec.visibility_of_element_located((By.XPATH, "//input[@class='form-text mask-cvv-4'][@type='text']")))
            self.logger.info(f"Typing CVV Number...")
            security_code = self.driver.find_element_by_xpath("//input[@class='form-text mask-cvv-4'][@type='text']")
            security_code.send_keys(Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + str(self.cvv))
        except (AttributeError, NoSuchElementException, TimeoutException, ElementNotInteractableException):
            self.logger.error("CVV")
            
    def fetch_table(self):
        wait = WebDriverWait(self.driver, 2, 0.1)
        try:
            wait.until(ec.visibility_of_element_located((By.XPATH, "//div[@class='summary-content']")))
            soup = self.extract_page()
            summary = soup.find('div','summary-content').find_all('li')
            item_container = soup.find('div',"item-container",)
            item_details = {
                "name": item_container.find("p","item-title").text,
                "qty": item_container.find("div","item-qty").text,
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
            return self.logger.table(columns=cols,rows=[row],title="Order Summary")
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
            self.driver.find_element_by_xpath("//button[text()='Place Order']").click()
            self.logger.info(f"Waiting For Order Confirmation...")
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
            self.logger.error("PLACEORDER")
    
    def is_success(self):
        try:
            wait = WebDriverWait(self.driver, 45)
            wait.until(ec.visibility_of_element_located((By.XPATH, "//span[@class='message-title']")))
            message = self.driver.find_element_by_xpath("//span[@class='message-title']").text
            if(message == 'THANK YOU FOR YOUR ORDER!'):
                self.logger.info(f"{message}")
                return True
        except:
            return False

    def get_order_num(self):
        order_num = self.driver.find_element_by_xpath("//label[text()='Order #: ']").text.replace(":", "").replace(" ", "").upper()
        return order_num
    
    def bot_protector(self):
        if self.driver.title != 'Are you a human?':
            return
        while(self.driver.title == 'Are you a human?'):
            wait = WebDriverWait(self.driver, 30, 0.1)
            self.logger.info("Bot detection is activated")
            try:
                wait.until(ec.visibility_of_element_located((By.ID, "imageCode")))
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
                self.driver.find_element_by_xpath("//input[@id='verifyCode']").click()
                time.sleep(0.5)
                try:
                    alert = self.driver.switch_to_alert()
                    self.logger.info(f"Wrong Captcha Trying Again - {solved_captcha}  - {round(time.time()-start_time)}")
                    alert.accept()
                except:
                    self.logger.info(f"Captcha Solved - {solved_captcha}")
                    break
                time.sleep(1)
            except:
                self.driver.refresh()
                time.sleep(3)
    
    def _search_(self):
        self.load_cfg()
        # url = 'https://www.newegg.com/global/il-en/p/pl?d=rtx+3060&N=101613480'

        # parsed = urlparse.urlparse(search_url)

        # search_query = parse_qs(parsed.query)['d'][0]
        # category = parse_qs(parsed.query)['N'][0]

        url = f"https://www.newegg.com/p/pl?d={self.search_query.replace(' ', '+')}&N={self.category}%204131&PageSize=96&Order=1"
        
        # found_item = {}
        response = self.driver.request("GET", url)
        html = response.text
        soup = bs4.BeautifulSoup(html, 'html.parser')
        # self.logger.debug(soup.title.text)
        
        items = soup.find_all('div', class_='item-cell')
        temp_items = [extract_item(item) for item in items]
        items_ids = [item['id'] for item in temp_items if item is not None and item['price'] in range(self.price_min, self.price_max)]
        if len(items_ids): 
            tmp = [ _id for _id in items_ids if _id not in self.items]
            self.logger.info(f"found {len(tmp)} items")
            self.logger.info(f"ID: {tmp}")
            self.items = tmp + self.items
            self.save_items()
            self.logger.debug(self.items)
            

        # self.logger.info(message=f"New Item is In Stock!\n{found_item['name']}\n{found_item['currency']}{found_item['price']}\n{found_item['link']}", notification=True, attach=found_item['img'])
        # if(notify):
        #     body = f"{found_item['name']} \n₪{found_item['price']}"
        #     send_notification("Item is in stock!", body, found_item['img'])
    
    def got_to_captcha(self):
        url = 'https://www.newegg.com/areyouahuman3?itn=true&referer=https%3A%2F%2Fwww.newegg.com%2FComponents%2FStore&why=8'
        self.get(url)
    
    def __get_mail_verification_code__(self):
        # print("FETCHING VERIFICATION CODE...")
        timeout = time.time() + 1*5
        while time.time() < timeout:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            # authenticate
            imap.login(*self.gmail.values())
            
            status, messages = imap.select("INBOX")
            # number of top emails to fetch
            N = 1
            # total number of emails
            messages = int(messages[0])
            
            for i in range(messages, messages-N, -1):
                # fetch the email message by ID
                res, msg = imap.fetch(str(i), "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        # parse a bytes email into a message object
                        msg = email.message_from_bytes(response[1])
                        # decode the email subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        # if isinstance(subject, bytes):
                        #     # if it's a bytes, decode to str
                        #     subject = subject.decode(encoding)
                        # # decode email sender
                        # From, encoding = decode_header(msg.get("From"))[0]
                        # if isinstance(From, bytes):
                        #     From = From.decode(encoding)
                        # # print("Subject:", subject)
                        # # print("From:", From)
                        if subject == 'Newegg Verification Code':
                            # if the email message is multipart
                            if msg.is_multipart():
                                # iterate over email parts
                                for part in msg.walk():
                                    # extract content type of email
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))
                                    try:
                                        # get the email body
                                        body = part.get_payload(decode=True).decode()
                                    except:
                                        pass
                                    if content_type == "text/plain" and "attachment" not in content_disposition:
                                        # print text/plain emails and skip attachments
                                        print(body)
                                    elif "attachment" in content_disposition:
                                        # download attachment
                                        filename = part.get_filename()
                                        if filename:
                                            folder_name = "".join(c if c.isalnum() else "_" for c in subject)
                                            if not os.path.isdir(folder_name):
                                                # make a folder for this email (named after the subject)
                                                os.mkdir(folder_name)
                                            filepath = os.path.join(folder_name, filename)
                                            # download attachment and save it
                                            open(filepath, "wb").write(part.get_payload(decode=True))
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
                                
                                verification_code = soup.table.table.tbody.find_all('tr')[0].td.find_all('table')[0].find_all('td')[2].find_all('table')[0].tbody.find_all('tr')[4].td.text
                                # print(f"found mail from NewEgg Verification Code: {verification_code}")
                                # Delete The Mail
                                imap.store(str(i), "+FLAGS", "\\Deleted")
                                return verification_code
                                # open(filepath, "w").write(body)
                                # open in the default browser
                    else:
                        pass
                        # print('mail from NewEgg is not found, fetch new mails...')
                time.sleep(Newegg.FETCH_MAIL_INTERVAL)
    def get_timestamp(self):
        return str(datetime.datetime.timestamp(datetime.datetime.now())).replace('.','')
    def __str__(self):
        return f"NEWEGG[{self.id}]"
