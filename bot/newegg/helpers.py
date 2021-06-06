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


def extract_item(item: dict) -> dict:
    # is_sponsered = item.find('div', 'item-sponsored menu-box')
    # if is_sponsered:
    #     return None
    # try:
    #     price = item.find('div', 'item-action').ul.find('li', 'price-current')
    #     if '$' in price.text:
    #         currency = '$'
    #     else:
    #         currency = '₪'
    #     float_price = float(price.strong.text.replace(",", "")+price.sup.text)
    #     in_stock = check_in_stock(item)
    #     item_link = item.a['href']
    #     item_img = item.a.img['src']
    #     item_name = item.find('a', 'item-title').text
    #     return {
    #         "id": get_item_id_by_url(item_link),
    #         "name": item_name,
    #         "price": float_price,
    #         "currency": currency,
    #         "link": item_link,
    #         "img": item_img,
    #         "in_stock": in_stock
    #     }

    if(not item['SponsoredMsg']):
        _item = {}
        _item['is_combo'] = item['IsCombo']
        _item['id'] = item['ItemCell']['Item'] if not _item['is_combo'] else item['ComboCell']['ComboID']
        _item['name'] = item['ItemCell']['Description']['Title'] if not _item['is_combo'] else item['ComboCell']['SolutionDescription']
        _item['price'] = item['ItemCell']['UnitCost'] if not _item['is_combo'] else item['ComboCell']['UnitCost']
        _item['currency'] = '$'
        _item['link'] = f"https://www.newegg.com/p/{_item['id']}" if not _item[
            'is_combo'] else f"https://www.newegg.com/Product/ComboDealDetails?ItemList=Combo.{_item['id']}"
        _item['img'] = f"https://c1.neweggimages.com/NeweggImage/ProductImageCompressAll300/{item['ItemCell']['Image']['ItemCellImageName']}" if not _item[
            'is_combo'] else f"https://c1.neweggimages.com/NeweggImage/ProductImageCompressAll300/{item['ComboCell']['SolutionImage']}"
        _item['in_stock'] = item['ItemCell']['Instock'] if not _item['is_combo'] else item['ComboCell']['StockForCombo']
        return _item
    return None
    # except:
    #     return None
