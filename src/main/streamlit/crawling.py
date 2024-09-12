from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import requests
import json


def crawl(radius):
    """
    지정한 반경 내의 음식점 정보를 크롤링하여 JSON 파일로 저장하는 함수

    Parameters:
        radius (int): 크롤링할 반경

    Returns:
        str: 저장된 JSON 파일 경로
    """

    # 원격 크롬 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') 
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--log-level=3')
    options.add_argument('--incognito')
    options.add_argument('--disable-images')
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.200'
    options.add_argument(f'user-agent={user_agent}')
    
    # 크롬 웹 드라이버 실행
    driver = webdriver.Chrome(options=options)
    
    # 네이버 지도 URL 설정 (반경 반영)
    url = f"https://map.naver.com/p?c={radius},0,0,0,dh"
    driver.get(url)
    driver.maximize_window()
    
    # 검색창에 음식점 검색
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.input_search"))
    )
    search_box.send_keys("음식점")
    search_box.send_keys(Keys.RETURN)
    
    time.sleep(1)

    # 검색 결과 iframe으로 전환
    driver.switch_to.frame("searchIframe")
    # 옵션 버튼이 등장할 때까지 대기
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "._restaurant_filter_item:first-child > a"))
    )

    # 옵션 버튼 클릭
    option_btn = driver.find_element(By.CSS_SELECTOR, "._restaurant_filter_item:first-child > a")
    option_btn.send_keys(Keys.ENTER)

    # '인기 많은 순' 버튼 클릭
    most_btn = driver.find_element(By.CSS_SELECTOR, "#_popup_rank+div > span:first-child > a")
    most_btn.send_keys(Keys.ENTER)

    # '영업 중' 버튼 클릭
    working_btn = driver.find_element(By.CSS_SELECTOR, "#_popup_property+div > span:first-child > a")
    working_btn.send_keys(Keys.ENTER)

    # 검색 결과 버튼 클릭
    result_btn = driver.find_element(By.CSS_SELECTOR, ".qeVvz a:last-child")
    result_btn.send_keys(Keys.ENTER)
    time.sleep(1)

    # 스크롤 전에 마지막 요소 수 저장
    previous_height = len(driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container > ul > li"))

    # 기다리는 시간 설정
    wait = WebDriverWait(driver, 10)
    while True:
        try:
            # 리스트의 마지막 요소 찾기
            element = driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container > ul > li")[-1]
            
            # 해당 요소가 보일 때까지 스크롤
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            
            # 페이지가 스크롤된 후 새로운 요소가 추가되었는지 확인
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#_pcmap_list_scroll_container > ul > li:nth-child({})".format(previous_height + 1))))
            
            # 새로운 요소의 수를 계산
            new_height = len(driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container > ul > li"))
            
            # 새로운 요소가 더 이상 추가되지 않으면 종료
            if new_height == previous_height:
                break
            
            # 스크롤 전 요소 수를 업데이트
            previous_height = new_height
            
        except Exception as e:
            print(f"스크롤 중 오류 발생: {e}")
            break
    
    # 페이지의 HTML 가져오기
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 음식점 이름, 메뉴, 평점, 프로그램 출연 정보, 리뷰 수 등 크롤링
    restaurant_names = [restaurant_name.text for restaurant_name in soup.select(".place_bluelink")]
    restaurant_menus = [restaurant_menu.text for restaurant_menu in soup.select(".KCMnt")]
    
    # 음식점 데이터를 저장할 딕셔너리 초기화
    restaurant_data = {}
    
    # CSS 셀렉터를 한 번에 사용하여 필요한 데이터를 추출
    restaurant_containers = soup.select("#_pcmap_list_scroll_container ul li .MVx6e")

    for i, name in enumerate(restaurant_names):
        container = restaurant_containers[i]

        # 음식점 정보를 추출
        rate_element = container.select_one(".orXYY")
        program_element = container.select_one(".V1dzc")
        
        # 리뷰 요소를 정확히 선택하기 위해 '리뷰' 텍스트가 포함된 span을 검색
        review_element = None
        for span in container.select("span"):
            if "리뷰" in span.text:
                review_element = span
                break

        restaurant_data[name] = {}
        restaurant_data[name]["menu"] = restaurant_menus[i]

        # 평점 정보가 없는 경우 None으로 설정
        if rate_element is None:
            restaurant_data[name]["rate"] = None
        else:
            try:
                restaurant_data[name]["rate"] = float(rate_element.text.lstrip("별점"))
            except ValueError:
                restaurant_data[name]["rate"] = None

        # 프로그램 정보가 없는 경우 None으로 설정
        if program_element is None:
            restaurant_data[name]["program"] = None
        else:
            restaurant_data[name]["program"] = program_element.text.lstrip("TV")

        # 리뷰 정보가 없는 경우 None으로 설정, 오류 발생 시 재시도
        try:
            if review_element:
                review_text = review_element.text.lstrip("리뷰 ").rstrip("+")
                restaurant_data[name]["review"] = int(review_text) if review_text.isdigit() else None
            else:
                restaurant_data[name]["review"] = None
        except ValueError:
            restaurant_data[name]["review"] = None

    driver.quit()

    # 현재 시간에 따라 파일 이름 설정
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"crawled_data_{current_time}.json"

    # JSON 파일로 저장
    json_data = json.dumps(restaurant_data, indent=2, ensure_ascii=False)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(json_data)
    
    return save_path


def crawl_school_meal():
    
    # JSON에 저장할 dictionary
    school_restaurant_data = {}

    options = webdriver.ChromeOptions()
    options.add_argument('--headless') 
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--log-level=3')
    options.add_argument('--incognito')
    options.add_argument('--disable-images')
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.200'
    options.add_argument(f'user-agent={user_agent}')
    
    # 크롬 웹 드라이버 실행
    driver = webdriver.Chrome(options=options)
    driver.get('https://chat.cau.ac.kr/v2/index.html')

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#root > div > div > div.chat_container > div > div > div:nth-child(1) > div > div > div.card > div:nth-child(3) > div > div > ul:nth-child(1) > li:nth-child(2) > a"))
    )

    school_meal_tab = driver.find_element(By.CSS_SELECTOR, "#root > div > div > div.chat_container > div > div > div:nth-child(1) > div > div > div.card > div:nth-child(3) > div > div > ul:nth-child(1) > li:nth-child(2) > a")
    school_meal_tab.click()

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#root > div > div > div.chat_container > div > div > div:nth-child(3) > div:nth-child(3) > div > div > div > div:nth-child(1) > div"))
    )

    time_now = datetime.now()

    if time_now.hour <= 10:
        time_num = 1
    elif time_now.hour > 10 or time_now.hour <= 15:
        time_num = 2
        n = 4
    else:
        time_num = 3
        n = 3
    
    meal_time = driver.find_element(By.CSS_SELECTOR, f"#root > div > div > div.chat_container > div > div > div:nth-child(3) > div:nth-child(3) > div > div > div > div:nth-child(1) > div > div > a:nth-child({time_num})")
    meal_time.click()

    if time_num==1:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#root > div > div > div.chat_container > div > div > div:nth-child(5) > div.bubble_box > div > span"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        meal_data = soup.select_one("#root > div > div > div.chat_container > div > div > div:nth-child(5) > div.bubble_box > div > span").text

        # '-' 뒤에 있는 부분을 찾음
        fixed_part = "-"
        menu_start_index = meal_data.find(fixed_part) + len(fixed_part)

        # 메뉴 부분 슬라이싱
        menu_part = meal_data[menu_start_index:].strip()

        menu_list = list(menu_part.split(','))
        
        school_restaurant_data = {
            "생활관식당(블루미르308관)": {
                "menu": {menu_item: {"type": menu_item} for menu_item in menu_list}
            }
        }

    else:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#root > div > div > div.chat_container > div > div > div:nth-child(5) > div:nth-child(3) > div > div > div > div:nth-child(1) > div"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        restaurants = soup.select("#root > div > div > div.chat_container > div > div > div:nth-child(5) > div:nth-child(3) > div > div > div")

        restaurants_list = list()
        for i in range(n):
            restaurant = restaurants[0].select(f".bubble_box:nth-child({i+1})")
            restaurants_list.append(restaurant)
            
        for restaurant_unit in restaurants_list:
            meal_data = restaurant_unit[0].select_one(".bubble_box > .bubble_unit > span").get_text()
            menu_lines = meal_data.split('🔹')  # '🔹'로 각 메뉴를 구분

            if "참슬기식당" in menu_lines[0]:
                menu_A = menu_lines[1].split('-')[1].split(',')  # 첫 번째 메뉴
                menu_B = menu_lines[2].split('-')[1].split(',')  # 두 번째 메뉴

                school_restaurant_data["참슬기식당(310관 B4층)"] = {
                    "A": {"menu":{item.strip(): {"type": item.strip()} for item in menu_A}},
                    "B": {"menu":{item.strip(): {"type": item.strip()} for item in menu_B}}
                }
                continue
            
            restaurant_name = menu_lines[0].split(' ')[1]

            menu_list = list()
            for menu in menu_lines[1:]:
                menu = menu.split('-')[1].split(',')
                menu_list.extend(menu)
            
            school_restaurant_data[restaurant_name] = {
                "menu":{item:{'type': item} for item in menu_list}
            }
    
    
    driver.quit()

    # 파일 명에 코드를 실행한 날짜와 시간을 반영
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"school_meal_{current_time}.json"

    # 학식 정보 dictionary를 문자열로 변환 후 JSON파일에 저장
    json_data = json.dumps(school_restaurant_data, indent=2, ensure_ascii=False)
    with open(save_path, 'w', encoding="utf-8") as f:
        f.write(json_data)

    return save_path


if __name__ == "__main__":
    # 음식점 크롤링 예시
    radius = 15  # 반경 15km
    print(f"Crawled restaurant data saved to: {crawl(radius)}")

    # 학식 크롤링 예시
    print(f"Crawled school meal data saved to: {crawl_school_meal()}")
