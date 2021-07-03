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
    if(not item['SponsoredMsg']):
        _item = {}
        _item['is_combo'] = item['IsCombo']
        _item['id'] = item['ItemCell']['Item'] if not _item['is_combo'] else item['ComboCell']['ComboID']
        _item['name'] = item['ItemCell']['Description']['Title'] if not _item['is_combo'] else item['ComboCell']['SolutionDescription']
        _item['price'] = item['ItemCell']['UnitCost'] if not _item['is_combo'] else item['ComboCell']['UnitCost']
        _item['shipping'] = item['ItemCell']['ShippingCharge'] if not _item['is_combo'] else item['ComboCell']['ShippingCharge']
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
