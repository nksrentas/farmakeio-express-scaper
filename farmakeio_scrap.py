# -*- coding: utf-8 -*-
from selenium import webdriver
from bs4 import BeautifulSoup
import csv
import io
import os
import urllib.request

SITE_URL = 'https://www.farmakeioexpress.gr/el'
SITE_URL_NO_LANG = 'https://www.farmakeioexpress.gr'
WAIT = 10


def init():
    # Create image folder
    current_path = os.getcwd()
    if not os.path.exists(current_path + '/images'):
        os.mkdir(current_path + '/images')

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    options.add_argument('--silent')
    d = webdriver.Chrome("/home/satner/Desktop/farmakeio scrap/chromedriver", chrome_options=options)
    d.set_window_size(1224, 937)

    return d


def get_menu_links():
    driver.implicitly_wait(WAIT)
    driver.get(SITE_URL)

    cookies_button = driver.find_element_by_xpath(
        '//*[contains(concat(" ",normalize-space(@class)," ")," gdpr-cm-accept ")]')
    cookies_button.click()

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


def store_product_image(product_name, image_slider):
    k = 0
    stripped_product_name = product_name.replace(' ', '-')
    # remove / from file name
    clean_product_name = stripped_product_name.replace('/', '-')
    for img_element in image_slider:
        image_file_type = (img_element.img['src'].split('/')[-1]).split('.')[-1]
        image_name = image_folder_path + "/" + clean_product_name + '-' + str(k) + '.' + image_file_type
        urllib.request.urlretrieve(img_element.img['src'], image_name)
        k += 1


def extract_product_data(product, lvl_one_title, lvl_two_title, lvl_three_title):
    product_link = product.select_one('.product-description.eq a')['href']
    driver.get(SITE_URL_NO_LANG + product_link)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    product_description_container = soup.select_one('.container-fluid.product-description .row')

    # brand title div
    brand_title = product_description_container.select_one('.col-md-12.brand-title').text

    # product title div
    product_title = product_description_container.find('h1').text

    product_price_container = product_description_container.find('div', {'class': 'product-price'})
    product_price_del_check = product_price_container.find('del')
    if product_price_del_check:
        product_price_del = product_price_del_check.text
    else:
        product_price_del = ''
    product_price_strong = product_price_container.find('strong').text

    # product status
    product_status_container = product_description_container.select_one('.col-md-12.product-status')
    all_p_tags = product_status_container.find_all('p')
    product_status_availability = all_p_tags[0].text
    product_status_barcode = all_p_tags[1].find('strong').text
    product_status_code = all_p_tags[2].find('strong').text

    # product description
    product_description_text = product_description_container.select_one('.col-md-12.description-text').text

    # store product image
    swiper_slider = soup.select('.swiper-slide')
    store_product_image(product_title, swiper_slider)

    tab_content = soup.select('.tab-content')
    tab_content_dict = {}
    for tab_number in tab_content:
        tab_content_dict[tab_number['id']] = tab_number.get_text('\t')

    # tab-1: description
    # tab-2: instructions
    # tab-3: components
    tab_row = ['', '', '']
    if tab_content_dict:
        if 'tab-1' in tab_content_dict:
            tab_row[0] = tab_content_dict['tab-1']

        if 'tab-2' in tab_content_dict:
            tab_row[1] = tab_content_dict['tab-2']

        if 'tab-3' in tab_content_dict:
            tab_row[2] = tab_content_dict['tab-3']

    # write product details to csv file
    row = [lvl_one_title, lvl_two_title, lvl_three_title, brand_title, product_title, product_price_del, product_price_strong, product_status_availability,
         product_status_barcode, product_status_code, product_description_text]
    csv_file.writerow(row + tab_row)


def expand_product_category(product_category_url, lvl_one_title='', lvl_two_title='', lvl_three_title=''):
    driver.get(SITE_URL_NO_LANG + product_category_url)
    while True:
        try:
            load_more_button = driver.find_element_by_xpath("	//*[contains(concat(\" \",normalize-space(@class),\" \"),\" gy-load-more \")][contains(concat(\" \",normalize-space(@class),\" \"),\" btn-standard \")][contains(concat(\" \",normalize-space(@class),\" \"),\" green \")]")
            driver.execute_script('arguments[0].click()', load_more_button)
        except Exception as e:
            # print(e)
            break

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    item_container = soup.find_all('div', {'class': 'col-lg-6 col-xl-4 mb-5'})
    loaded_item_container = soup.find_all('div', {'class': 'col-lg-4 mb-5'})

    print('[-] Initiating data collection from: {} / {} / {}   ({} total products)'.format(lvl_one_title, lvl_two_title, lvl_three_title, len(item_container) + len(loaded_item_container)))
    for product in item_container:
        extract_product_data(product, lvl_one_title, lvl_two_title, lvl_three_title)
    for product in loaded_item_container:
        extract_product_data(product, lvl_one_title, lvl_two_title, lvl_three_title)
    print('[+] Data collection is over from: {} / {} / {} '.format(lvl_one_title, lvl_two_title, lvl_three_title))


def get_total_links():
    counter = 0
    for k, v in menu_links.items():
        if not isinstance(v, dict):
            counter += 1
            continue
        for kk, vv in v.items():
            if not isinstance(vv, dict):
                counter += 1
                continue
            counter += len(vv.keys())
    return counter


if __name__ == '__main__':
    driver = init()

    menu_links = {}
    image_folder_path = os.getcwd() + '/images'
    get_menu_links()

    remaining_links = get_total_links()

    with io.open('data.csv', mode='w') as csv_file:
        csv_file = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(['lvl_one_title', 'lvl_two_title', 'lvl_three_title', 'brand_title', 'product_title', 'product_price_del', 'product_price_strong', 'product_status_availability',
         'product_status_barcode', 'product_status_code', 'product_description_text', 'description', 'instructions', 'components'])
        for k, v in menu_links.items():
            if not isinstance(v, dict):
                expand_product_category(v, k)
                remaining_links -= 1
                print('[*] Remaining categories: {}'.format(remaining_links))
                continue
            for kk, vv in v.items():
                if not isinstance(vv, dict):
                    expand_product_category(vv, k, kk)
                    remaining_links -= 1
                    print('[*] Remaining categories: {}'.format(remaining_links))
                    continue
                for kkk, vvv in vv.items():
                    expand_product_category(vvv, k, kk, kkk)
                    remaining_links -= 1
                    print('[*] Remaining categories: {}'.format(remaining_links))
