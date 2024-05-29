from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from tqdm import tqdm
import json

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
        radius = float(input("==> "))
    except ValueError:
        continue

    if 13 <= radius <= 16:
        break

# 범위를 반영하여 네이버 지도 접속
driver = webdriver.Chrome()
url = f"https://map.naver.com/p?c={radius},0,0,0,dh"
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
time.sleep(1.5)

# 음식점 1페이지 끝까지 스크롤
for _ in range(10):
    element = driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container > ul > li")[-1]
    driver.execute_script("arguments[0].scrollIntoView(true);", element)

# html parsing
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# 크롬 창 닫기
driver.quit()

# 가게 이름과 메뉴 종류 리스트 생성
restaurant_names = [restaurant_name.text for restaurant_name in soup.select('.place_bluelink')] 
restaurant_menus = [restaurant_menu.text for restaurant_menu in soup.select('.KCMnt')] 

# 가게 정보를 담을 딕셔너리
restaurant_data = {}

# 별점, 출연한 TV 프로그램, 리뷰 수의 정보를 크롤링하여 딕셔너리에 담음
# 해당 세 정보는 크롤링 시에 존재하지 않는 경우가 존재하여 따로 크롤링을 진행
# 크롤링 시간이 오래 걸려 tqdm으로 사용자에게 진행 현황 시각화
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

    # 리뷰 정보를 담은 html 태그의 위치가 가게에 따라 두 가지의 경우로 나뉘어 아래와 같이 작성
    try:
        restaurant_data[restaurant_names[i-1]]["review"] = int(restaurant_review[0].text.lstrip("리뷰 ").rstrip('+'))
    except ValueError:
        try:
            restaurant_review = soup.select(f"{RESTAURANT_CONTAINER} > span:nth-last-child(2)")
            restaurant_data[restaurant_names[i-1]]["review"] = int(restaurant_review[0].text.lstrip("리뷰 ").rstrip('+'))
        except ValueError:
            restaurant_data[restaurant_names[i-1]]["review"] = None

# 가게 정보 딕셔너리를 JSON 타입의 문자열로 변환 후 json 파일에 저장
json_data = json.dumps(restaurant_data, indent=2, ensure_ascii=False)
with open("data.json", 'w', encoding="utf-8") as f:
    f.write(json_data)
