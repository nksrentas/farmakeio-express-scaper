# -*- coding: utf-8 -*-
import csv
import io
import os
import urllib.request
import threading
from queue import Queue

from selenium import webdriver
from bs4 import BeautifulSoup
from tqdm import tqdm

SITE_URL = 'https://www.farmakeioexpress.gr/el'
SITE_URL_NO_LANG = 'https://www.farmakeioexpress.gr'
NUMBER_OF_THREADS = os.cpu_count()
WAIT = 10


def init():
    # Create image folder
    current_path = os.getcwd()
    folder = current_path + '/images'
    if not os.path.exists(folder):
        os.mkdir(folder)
    else:  # Delete inner files
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    options.add_argument('--silent')

    for _ in range(NUMBER_OF_THREADS):
        d = webdriver.Chrome('/home/satner/Desktop/farmakeio scrap/chromedriver', chrome_options=options)
        d.set_window_size(1224, 937)
        drivers.append(d)


def get_menu_links():
    drivers[0].implicitly_wait(WAIT)
    drivers[0].get(SITE_URL)

    cookies_button = drivers[0].find_element_by_xpath(
        '//*[contains(concat(" ",normalize-space(@class)," ")," gdpr-cm-accept ")]')
    cookies_button.click()

    page_source = drivers[0].page_source
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
        image_name = image_folder_path + '/' + clean_product_name + '-' + str(k) + '.' + image_file_type
        urllib.request.urlretrieve(img_element.img['src'], image_name)
        k += 1


def extract_product_data(product, lvl_one_title, lvl_two_title, lvl_three_title, driver):
    product_link = product.select_one('.product-description.eq a')['href']
    driver.get(SITE_URL_NO_LANG + product_link)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    product_description_container = soup.select_one('.container-fluid.product-description .row')

    # brand title div
    brand_title = ''
    if product_description_container.select_one('.col-md-12.brand-title'):
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
    row = [lvl_one_title, lvl_two_title, lvl_three_title, brand_title, product_title, product_price_del,
           product_price_strong, product_status_availability,
           product_status_barcode, product_status_code, product_description_text]

    with lock:
        csv_file.writerow(row + tab_row)


def expand_product_category(args, driver):
    global remaining_links

    if len(args) == 2:
        product_category_url = args[0]
        lvl_one_title = args[1]
        lvl_two_title = ''
        lvl_three_title = ''
    elif len(args) == 3:
        product_category_url = args[0]
        lvl_one_title = args[1]
        lvl_two_title = args[2]
        lvl_three_title = ''
    elif len(args) == 4:
        product_category_url = args[0]
        lvl_one_title = args[1]
        lvl_two_title = args[2]
        lvl_three_title = args[3]

    driver.get(SITE_URL_NO_LANG + product_category_url)
    while True:
        try:
            load_more_button = driver.find_element_by_xpath(
                "	//*[contains(concat(\" \",normalize-space(@class),\" \"),\" gy-load-more \")][contains(concat(\" \",normalize-space(@class),\" \"),\" btn-standard \")][contains(concat(\" \",normalize-space(@class),\" \"),\" green \")]")
            driver.execute_script('arguments[0].click()', load_more_button)
        except Exception as e:
            break

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    item_container = soup.find_all('div', {'class': 'col-lg-6 col-xl-4 mb-5'})
    loaded_item_container = soup.find_all('div', {'class': 'col-lg-4 mb-5'})

    total_category_products = len(item_container) + len(loaded_item_container)
    with tqdm(total=total_category_products) as progress_bar:
        with lock:
            start_msg = '[-] Initiating data collection from: {} / {} / {}   ({} total products)'.format(lvl_one_title,
                                                                                                   lvl_two_title,
                                                                                                   lvl_three_title,
                                                                                                   total_category_products)
            progress_bar.write(start_msg)

        for product in item_container:
            extract_product_data(product, lvl_one_title, lvl_two_title, lvl_three_title, driver)
            progress_bar.update()
        for product in loaded_item_container:
            extract_product_data(product, lvl_one_title, lvl_two_title, lvl_three_title, driver)
            progress_bar.update()
        progress_bar.close()

    with lock:
        remaining_links -= 1
        end_msg = '[+] Data collection is over from: {} / {} / {} '.format(lvl_one_title, lvl_two_title, lvl_three_title)
        remaining_msg = '[*] Remaining categories: {}'.format(remaining_links)
        progress_bar.write(end_msg)
        progress_bar.write(remaining_msg)


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


def worker(driver):
    while True:
        item = q.get()
        expand_product_category(item, driver)
        q.task_done()


if __name__ == '__main__':
    drivers = []
    init()

    menu_links = {}
    image_folder_path = os.getcwd() + '/images'
    get_menu_links()

    remaining_links = get_total_links()
    print('[*] Total categories: {}'.format(remaining_links))

    with io.open('data.csv', mode='w') as csv_file:
        q = Queue()
        lock = threading.Lock()
        csv_file = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_file.writerow(
            ['lvl_one_title', 'lvl_two_title', 'lvl_three_title', 'brand_title', 'product_title', 'product_price_del',
             'product_price_strong', 'product_status_availability',
             'product_status_barcode', 'product_status_code', 'product_description_text', 'description', 'instructions',
             'components'])
        for k, v in menu_links.items():
            if not isinstance(v, dict):
                q.put((v, k))
                continue
            for kk, vv in v.items():
                if not isinstance(vv, dict):
                    q.put((vv, k, kk))
                    continue
                for kkk, vvv in vv.items():
                    q.put((vvv, k, kk, kkk))

        for i in range(NUMBER_OF_THREADS):
            t = threading.Thread(target=worker, args=(drivers[i],))
            t.daemon = True
            t.start()

        q.join()

    print('[*] Data collection is over')
