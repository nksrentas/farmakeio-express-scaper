from selenium import webdriver
from bs4 import BeautifulSoup

SITE_URL = 'https://www.farmakeioexpress.gr/el'
WAIT = 10


def init():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    options.add_argument('--silent')

    return webdriver.Chrome("/home/satner/Desktop/soup/web-srap/chromedriver", chrome_options=options)


def get_menu_links():
    driver.implicitly_wait(WAIT)
    driver.get(SITE_URL)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')
    menu_container = soup.find('div', {'class': 'row menu-items-block'})
    menu_item_container = menu_container.find_all('div', {'class': 'col-md-3 col-sm-12 menu-item accordion'})

    for menu_item in menu_item_container:
        menu_item_name = menu_item.select_one('h2 a')['title']
        menu_item_href = menu_item.select_one('h2 a')['href']
        second_lvl_menu = menu_item.select('.second-lvl-menu > .item-wrap')
        if not second_lvl_menu:
            menu_links[menu_item_name] = menu_item_href
            continue
        menu_links[menu_item_name] = {}
        for second_lvl_menu_item in second_lvl_menu:
            second_lvl_menu_name = second_lvl_menu_item.select_one('a')['title']
            second_lvl_menu_href = second_lvl_menu_item.select_one('a')['href']
            third_lvl_menu = second_lvl_menu_item.select('.third-lvl-menu .item-wrap')
            if not third_lvl_menu:
                menu_links[menu_item_name][second_lvl_menu_name] = second_lvl_menu_href
                continue
            menu_links[menu_item_name][second_lvl_menu_name] = {}
            for third_lvl_menu_item in third_lvl_menu:
                link_name = third_lvl_menu_item.select_one('a')['title']
                link_href = third_lvl_menu_item.select_one('a')['href']
                menu_links[menu_item_name][second_lvl_menu_name][link_name] = link_href


if __name__ == '__main__':
    driver = init()
    menu_links = {}
    get_menu_links()

    for k,v in menu_links.iteritems():
        print k
        if not isinstance(v, dict):
            print '++', v
            continue
        for kk,vv in v.iteritems():
            print '==>', kk
            if not isinstance(vv, dict):
                print '++++', vv
                continue
            for kkk,vvv in vv.iteritems():
                print '====>', kkk, vvv
        print '\n'
