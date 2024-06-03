# 필요한 라이브러리 import
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime
from tqdm import tqdm
import json

def crawl(radius):
    """
    지정한 반경 내의 음식점 정보를 크롤링하여 JSON 파일로 저장하는 함수
    
    Parameters:
        radius (str): 크롤링할 반경
    
    Returns:
        str: 저장된 JSON 파일 경로
    """
    
    # 크롬 웹드라이버 초기화
    driver = webdriver.Chrome()
    
    # 네이버 지도 URL 설정 (반경 반영)
    url = f"https://map.naver.com/p?c={radius},0,0,0,dh"
    driver.get(url)

    # 페이지 로드 대기
    time.sleep(3)

    # '음식점' 버튼 클릭
    restaurant_btn = driver.find_element(By.CSS_SELECTOR, ".item_bubble_keyword:first-child button")
    restaurant_btn.send_keys(Keys.ENTER)
    time.sleep(2)

    # 검색 결과 iframe으로 전환
    driver.switch_to.frame("searchIframe")
    time.sleep(1)

    # 옵션 버튼 클릭
    option_btn = driver.find_element(By.CSS_SELECTOR, "._restaurant_filter_item:first-child > a")
    option_btn.send_keys(Keys.ENTER)
    time.sleep(1)

    # '많은 순' 버튼 클릭
    most_btn = driver.find_element(By.CSS_SELECTOR, "#_popup_rank+div > span:first-child > a")
    most_btn.send_keys(Keys.ENTER)
    time.sleep(1)

    # '영업 중' 버튼 클릭
    working_btn = driver.find_element(By.CSS_SELECTOR, "#_popup_property+div > span:first-child > a")
    working_btn.send_keys(Keys.ENTER)

    # 검색 결과 버튼 클릭
    result_btn = driver.find_element(By.CSS_SELECTOR, ".qeVvz a:last-child")
    result_btn.send_keys(Keys.ENTER)
    time.sleep(1.5)

    # 스크롤 다운하여 추가 데이터 로드
    for _ in range(10):
        element = driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container > ul > li")[-1]
        driver.execute_script("arguments[0].scrollIntoView(true);", element)

    # 페이지 소스 가져오기
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # 드라이버 종료
    driver.quit()

    # 음식점 이름과 메뉴 추출
    restaurant_names = [restaurant_name.text for restaurant_name in soup.select('.place_bluelink')] 
    restaurant_menus = [restaurant_menu.text for restaurant_menu in soup.select('.KCMnt')] 

    # 음식점 데이터를 저장할 딕셔너리 초기화
    restaurant_data = {}

    # 크롤링 진행 상황 표시
    print("----[Crawling Progress]----")
    restuarants = soup.select("#_pcmap_list_scroll_container > ul > li")
    for i in tqdm(range(1,len(restuarants)+1), ncols=80, leave=False):
        RESTAURANT_CONTAINER = f"#_pcmap_list_scroll_container ul li:nth-child({i}) .MVx6e"
        restaurant_rate = soup.select(f"{RESTAURANT_CONTAINER} .orXYY")
        restaurant_program = soup.select(f"{RESTAURANT_CONTAINER} .V1dzc")
        restaurant_review = soup.select(f"{RESTAURANT_CONTAINER} > span:nth-last-child(1)")

        restaurant_data[restaurant_names[i-1]] = {}
        restaurant_data[restaurant_names[i-1]]["menu"] = restaurant_menus[i-1]

        # 평점 정보가 없는 경우 None으로 설정
        if restaurant_rate == []:
            restaurant_data[name]["rate"] = None
        else:
            restaurant_data[name]["rate"] = float(restaurant_rate[0].text.lstrip("별점"))

        # 프로그램 정보가 없는 경우 None으로 설정
        if restaurant_program == []:
            restaurant_data[name]["program"] = None
        else:
            restaurant_data[name]["program"] = restaurant_program[0].text.lstrip("TV")

        # 리뷰 정보가 없는 경우 None으로 설정, 오류 발생 시 재시도
        try:
            restaurant_data[name]["review"] = int(restaurant_review[0].text.lstrip("리뷰 ").rstrip('+'))
        except ValueError:
            try:
                restaurant_review = soup.select(f"{RESTAURANT_CONTAINER} > span:nth-last-child(2)")
                restaurant_data[name]["review"] = int(restaurant_review[0].text.lstrip("리뷰 ").rstrip('+'))
            except ValueError:
                restaurant_data[name]["review"] = None

    # 현재 시간에 따라 파일 이름 설정
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"crawled_data_{current_time}.json"

    # JSON 파일로 저장
    json_data = json.dumps(restaurant_data, indent=2, ensure_ascii=False)
    with open(save_path, 'w', encoding="utf-8") as f:
        f.write(json_data)
    
    return save_path

def crawl_school_meal():
    """
    오늘의 학교 급식 메뉴를 크롤링하여 JSON 파일로 저장하는 함수
    
    Returns:
        str: 저장된 JSON 파일 경로
    """
    
    # 현재 시간에 따라 급식 시간을 설정
    now = datetime.now()
    if 13 <= now.hour < 18:  # 13:00 ~ 18:00 사이
        meal_time = "dinner"
    else:
        meal_time = "lunch"

    school_restaurant = "truly-wise"
    url = f"https://www.mealtify.com/univ/cau/{school_restaurant}/meal/today/{meal_time}"
    
    # 크롬 웹드라이버 초기화
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(3)
    
    # 페이지 소스 가져오기
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()

    # 학교 급식 데이터를 저장할 딕셔너리 초기화
    school_restaurant_data = {}
    
    # 급식 메뉴, 종류, 칼로리 추출
    school_menus = [school_menu.text for school_menu in soup.select(".pt-4 tbody tr td:nth-child(1)")[:-1]]
    school_types = [school_type.text for school_type in soup.select(".pt-4 tbody tr td:nth-child(2)")[:-1]]
    school_kcals = [school_kcal.text for school_kcal in soup.select(".pt-4 tbody tr td:nth-child(3)")[:-1]]
    
    # 추출한 데이터를 딕셔너리에 저장
    for i, menu in enumerate(school_menus):
        school_restaurant_data[menu] = {"type": school_types[i], "kcal": school_kcals[i]}

    # 현재 시간에 따라 파일 이름 설정
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"school_meal_{current_time}.json"
    
    # JSON 파일로 저장
    json_data = json.dumps(school_restaurant_data, indent=2, ensure_ascii=False)
    with open(save_path, 'w', encoding="utf-8") as f:
        f.write(json_data)
    
    return save_path
