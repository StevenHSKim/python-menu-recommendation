from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import csv
import pandas as pd

# 사용자에게 설정할 범위를 실수로 입력받음
# 주어진 조건에 부합하지 않을 경우 계속 input 요청함
while True:
    print("위치 범위를 설정해주세요.")
    print("13~16 사이의 실수만 입력 가능하며, 수가 커질수록 검색 범위는 좁아집니다.")
    print("각 수에 대한 거리 범위는 아래와 같습니다.")
    print("- 13~14: 반경 약 4km ~ 2km")
    print("- 14~15: 반경 약 2km ~ 1km")
    print("- 15~16: 반경 약 1km ~ 0.5km")

    try:
        scope = float(input("==> "))
    except ValueError:
        continue

    if 13 <= scope <= 16:
        break

# 범위를 반영하여 네이버 지도 접속
driver = webdriver.Chrome()
# PyCharm can't follow code paths, assuming a variable declared in loops might not be bound
# Name 'scope' can be undefined
# noinspection PyUnboundLocalVariable
url = f"https://map.naver.com/p?c={scope},0,0,0,dh"
driver.get(url)
driver.maximize_window()

# 접속 시 완전히 페이지가 업로드 되도록 3초 sleep
time.sleep(3)

# 내부에 들어가 음식점 버튼 클릭
restaurant_btn = driver.find_element(By.CSS_SELECTOR, ".item_bubble_keyword:first-child button")
restaurant_btn.send_keys(Keys.ENTER)

time.sleep(2)

# 새로 생긴 탭으로 iframe 전환
driver.switch_to.frame("searchIframe")

time.sleep(1)

# 필터링 버튼 클릭
option_btn = driver.find_element(By.CSS_SELECTOR, "._restaurant_filter_item:first-child > a")
option_btn.send_keys(Keys.ENTER)

time.sleep(1)

# "많이찾는" 버튼 클릭 -> 사람들이 더 선호하는 식당 중심으로 수집 가능
most_btn = driver.find_element(By.CSS_SELECTOR, "#_popup_rank+div > span:first-child > a")
most_btn.send_keys(Keys.ENTER)

time.sleep(1)

# "영업중" 버튼 클릭
working_btn = driver.find_element(By.CSS_SELECTOR, "#_popup_property+div > span:first-child > a")
working_btn.send_keys(Keys.ENTER)

# "결과보기" 버튼 클릭
result_btn = driver.find_element(By.CSS_SELECTOR, ".qeVvz a:last-child")
result_btn.send_keys(Keys.ENTER)

time.sleep(1)

# 음식점 1페이지 끝까지 스크롤
for _ in range(10):
    element = driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container > ul > li")[-1]
    driver.execute_script("arguments[0].scrollIntoView(true);", element)

# html parsing
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

restaurant_names = soup.select(".place_bluelink")  # 가게 이름
restaurant_menus = soup.select(".KCMnt")  # 메뉴 또는 종류

# 크롤링 데이터 -> 리스트
name_list = [name.text for name in restaurant_names]
menu_list = [menu.text for menu in restaurant_menus]

# 데이터 리스트 -> csv
data = {"name": name_list, "menu": menu_list}
data_frame = pd.DataFrame(data)
data_frame.to_csv("data.csv", encoding="utf-8-sig")
