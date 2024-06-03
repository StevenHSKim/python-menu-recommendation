from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime
import json

def crawl(radius):
    driver = webdriver.Chrome()
    url = f"https://map.naver.com/p?c={radius},0,0,0,dh"
    options = webdriver.ChromeOptions()
    driver.get(url)

    time.sleep(3)

    restaurant_btn = driver.find_element(By.CSS_SELECTOR, ".item_bubble_keyword:first-child button")
    restaurant_btn.send_keys(Keys.ENTER)
    time.sleep(2)

    driver.switch_to.frame("searchIframe")
    time.sleep(1)

    option_btn = driver.find_element(By.CSS_SELECTOR, "._restaurant_filter_item:first-child > a")
    option_btn.send_keys(Keys.ENTER)
    time.sleep(1)

    most_btn = driver.find_element(By.CSS_SELECTOR, "#_popup_rank+div > span:first-child > a")
    most_btn.send_keys(Keys.ENTER)
    time.sleep(1)

    working_btn = driver.find_element(By.CSS_SELECTOR, "#_popup_property+div > span:first-child > a")
    working_btn.send_keys(Keys.ENTER)

    result_btn = driver.find_element(By.CSS_SELECTOR, ".qeVvz a:last-child")
    result_btn.send_keys(Keys.ENTER)
    time.sleep(1.5)

    for _ in range(10):
        element = driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container > ul > li")[-1]
        driver.execute_script("arguments[0].scrollIntoView(true);", element)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    driver.quit()

    restaurant_names = [restaurant_name.text for restaurant_name in soup.select('.place_bluelink')] 
    restaurant_menus = [restaurant_menu.text for restaurant_menu in soup.select('.KCMnt')] 

    restaurant_data = {}

    print("----[Crawling Progress]----")
    restuarants = soup.select("#_pcmap_list_scroll_container > ul > li")
    for i in tqdm(range(1,len(restuarants)+1), ncols=80, leave=False):
        RESTAURANT_CONTAINER = f"#_pcmap_list_scroll_container ul li:nth-child({i}) .MVx6e"
        restaurant_rate = soup.select(f"{RESTAURANT_CONTAINER} .orXYY")
        restaurant_program = soup.select(f"{RESTAURANT_CONTAINER} .V1dzc")
        restaurant_review = soup.select(f"{RESTAURANT_CONTAINER} > span:nth-last-child(1)")

        restaurant_data[restaurant_names[i-1]] = {}
        restaurant_data[restaurant_names[i-1]]["menu"] = restaurant_menus[i-1]

        if restaurant_rate == []:
            restaurant_data[restaurant_names[i-1]]["rate"] = None
        else:
            restaurant_data[restaurant_names[i-1]]["rate"] = float(restaurant_rate[0].text.lstrip("별점"))

        if restaurant_program == []:
            restaurant_data[restaurant_names[i-1]]["program"] = None
        else:
            restaurant_data[restaurant_names[i-1]]["program"] = restaurant_program[0].text.lstrip("TV")

        try:
            restaurant_data[restaurant_names[i-1]]["review"] = int(restaurant_review[0].text.lstrip("리뷰 ").rstrip('+'))
        except ValueError:
            try:
                restaurant_review = soup.select(f"{RESTAURANT_CONTAINER} > span:nth-last-child(2)")
                restaurant_data[restaurant_names[i-1]]["review"] = int(restaurant_review[0].text.lstrip("리뷰 ").rstrip('+'))
            except ValueError:
                restaurant_data[restaurant_names[i-1]]["review"] = None

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"crawled_data_{current_time}.json"

    json_data = json.dumps(restaurant_data, indent=2, ensure_ascii=False)
    with open(save_path, 'w', encoding="utf-8") as f:
        f.write(json_data)
    
    return save_path

def crawl_school_meal():
    now = datetime.now()
    if now.hour >= 13 and now.hour < 18:  # 13:30 ~ 18:30 사이
        meal_time = "dinner"
    else:
        meal_time = "lunch"

    school_restaurant = "truly-wise"
    url = f"https://www.mealtify.com/univ/cau/{school_restaurant}/meal/today/{meal_time}"
    
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(3)
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()

    school_restaurant_data = {}
    
    school_menus = [school_menu.text for school_menu in soup.select(".pt-4 tbody tr td:nth-child(1)")[:-1]]
    school_types = [school_type.text for school_type in soup.select(".pt-4 tbody tr td:nth-child(2)")[:-1]]
    school_kcals = [school_kcal.text for school_kcal in soup.select(".pt-4 tbody tr td:nth-child(3)")[:-1]]
    
    for i, menu in enumerate(school_menus):
        school_restaurant_data[menu] = {"type": school_types[i], "kcal": school_kcals[i]}

    json_data = json.dumps(school_restaurant_data, indent=2, ensure_ascii=False)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"school_meal_{current_time}.json"
    
    with open(save_path, 'w', encoding="utf-8") as f:
        f.write(json_data)
    
    return save_path
