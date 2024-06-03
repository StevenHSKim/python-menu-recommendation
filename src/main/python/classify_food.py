import openai
import json
import os
from datetime import datetime
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# OpenAI API 키 설정
# 1. OpenAI API 계정 생성: https://platform.openai.com/signup
# 2. 신용카드 등록 <- 이거 안 하면 아마 오류 발생할거에요. (등록시 $5 소요 - 앞으로 AI학과 재학중에 쓸 일 많으실 겁니다)
# 2. API 키 발급: https://platform.openai.com/account/api-keys
# 3. 발급받은 API 키를 아래 your_openai.api_key에 설정
openai.api_key = 'your_openai_api_key'

def classify_food_type(restaurant_name: str, menu: str) -> str:
    """
    GPT API를 사용하여 음식 카테고리를 분류합니다.
    """
    prompt = (
        f"식당 이름: {restaurant_name}\n"
        f"메뉴: {menu}\n"
        "이 식당의 음식 카테고리를 다음 중 하나로 분류하세요: "
        "한식, 중식, 일식, 양식, 아시안, 디저트, 그외\n"
        "카테고리 이름만 응답하세요. 예를 들어, 한식, 중식, 일식, 양식, 아시안, 디저트, 그외 중 하나만 작성하세요."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that classifies restaurant food categories."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        n=1,
        stop=None,
        temperature=0.0,
    )

    category = response.choices[0].message['content'].strip()
    
    # 유효한 카테고리인지 확인
    valid_categories = ["한식", "중식", "일식", "양식", "아시안", "디저트", "그외"]
    if category not in valid_categories:
        print(f"Invalid category: {category}. Setting category to '그외'")
        category = "그외"  # 기본값으로 설정
    
    return category

def post_process_category(details: Dict[str, Any]) -> str:
    """
    메뉴 설명을 기반으로 카테고리를 후처리합니다.
    """
    menu_description = details['menu']
    
    POSTPROCESSING_KEYWORDS = ['해물', '생선', '포장마차', '대게요리'] # 한식으로 처리할 메뉴 키워드
    
    if any(keyword in menu_description for keyword in POSTPROCESSING_KEYWORDS):
        return "한식"
    
    return details['category']

def process_restaurant(restaurant, details):
    """
    개별 식당의 카테고리를 분류하고 후처리합니다.
    """
    try:
        category = classify_food_type(restaurant, details['menu'])
        details['category'] = category
        details['category'] = post_process_category(details)  # 후처리 단계 추가
    except Exception as e:
        print(f"Error classifying {restaurant}: {e}")
        details['category'] = "그외"  # 기본값으로 설정
    
    return restaurant, details

def process_restaurants(input_file: str):
    """
    입력 파일에서 식당 데이터를 읽고, 카테고리를 분류하여 출력 파일에 저장합니다.
    """
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    classified_data = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_restaurant = {executor.submit(process_restaurant, restaurant, details): restaurant for restaurant, details in data.items()}
        for future in as_completed(future_to_restaurant):
            restaurant, details = future.result()
            classified_data[restaurant] = details
    
    # 현재 시간을 기반으로 파일 이름 생성
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"classified_data_{current_time}.json"

    with open(save_path, 'w', encoding='utf-8') as file:
        json.dump(classified_data, file, ensure_ascii=False, indent=4)
    
    print(f"분류된 데이터가 {save_path}에 저장되었습니다.")

if __name__ == "__main__":
    input_filename = "crawled_data_20240603_003043.json"  # 예시 파일 이름
    process_restaurants(input_filename)