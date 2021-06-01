import urllib.parse as urlparse
from urllib.parse import parse_qs

def get_item_id_by_url(url):
    try:
        return parse_qs(urlparse.urlparse(url).query)['ItemList'][0]
    except:
        return parse_qs(urlparse.urlparse(url).query)['Item'][0]
        # return urlparse.urlparse(url).path.split('/')[-1]
    

def check_in_stock(soup_item):
    try:
        is_in_stock = soup_item.find('div', 'item-info').p.text
        if(is_in_stock != 'OUT OF STOCK'):
            return True
    except:
        return True
    return False

def extract_item(item):
        is_sponsered = item.find('div', 'item-sponsored menu-box')
        if is_sponsered:
            return None
        try:
            price = item.find('div', 'item-action').ul.find('li', 'price-current')
            if '$' in price.text:
                currency = '$'
            else:
                currency = '₪'
            float_price = float(price.strong.text.replace(",", ""))
            in_stock = check_in_stock(item)
            item_link = item.a['href']
            item_img = item.a.img['src']
            item_name = " ".join(item.find('a', 'item-title').text.split()[:6])
            return {
                "id": get_item_id_by_url(item_link),
                "name": item_name,
                "price": float_price,
                "currency": currency,
                "link": item_link,
                "img": item_img,
                "in_stock": in_stock
            }
        except:
            return None