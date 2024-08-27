import openai
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# OpenAI API 키 설정
openai.api_key = "your_openai_api_key"


def classify_food_type(restaurant_name, menu):
    """
    GPT API를 사용하여 음식 카테고리를 분류합니다.

    Parameters:
        restaurant_name (str): 식당 이름
        menu (str): 메뉴 설명

    Returns:
        str: 분류된 음식 카테고리
    """
    # GPT 모델에 제공할 프롬프트 구성
    prompt = (
        f"식당 이름: {restaurant_name}\n"
        f"메뉴: {menu}\n"
        "이 식당의 음식 카테고리를 다음 중 하나로 분류하세요: "
        "한식, 중식, 일식, 양식, 아시안, 디저트, 그외\n"
        "카테고리 이름만 응답하세요. 예를 들어, 한식, 중식, 일식, 양식, 아시안, 디저트, 그외 중 하나만 작성하세요."
    )

    # GPT API 호출
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

    # GPT 응답에서 카테고리 추출
    category = response.choices[0].message["content"].strip()

    # 유효한 카테고리인지 확인
    valid_categories = ["한식", "중식", "일식", "양식", "아시안", "디저트", "그외"]
    if category not in valid_categories:
        print(f"Invalid category: {category}. Setting category to '그외'")
        category = "그외"  # 기본값으로 설정

    return category


def post_process_category(details):
    """
    메뉴 설명을 기반으로 카테고리를 후처리합니다.

    Parameters:
        details (dict): 메뉴 설명을 포함한 음식점 세부 정보

    Returns:
        str: 후처리된 음식 카테고리
    """
    menu_description = details["menu"]

    # 한식으로 처리할 메뉴 키워드
    postprocessing_keywords = ["해물", "생선", "포장마차", "대게요리"]

    if any(keyword in menu_description for keyword in postprocessing_keywords):
        return "한식"

    return details["category"]


def process_restaurant(restaurant, details):
    """
    개별 식당의 카테고리를 분류하고 후처리합니다.

    Parameters:
        restaurant (str): 식당 이름
        details (dict): 메뉴 설명을 포함한 음식점 세부 정보

    Returns:
        tuple: 식당 이름과 갱신된 세부 정보
    """
    try:
        # 음식 카테고리 분류
        category = classify_food_type(restaurant, details["menu"])
        details["category"] = category
        # 후처리 단계 추가
        details["category"] = post_process_category(details)
    except Exception as e:
        print(f"Error classifying {restaurant}: {e}")
        details["category"] = "그외"  # 기본값으로 설정

    return restaurant, details


def process_restaurants(input_file):
    """
    입력 파일에서 식당 데이터를 읽고, 카테고리를 분류하여 출력 파일에 저장합니다.

    Parameters:
        input_file (str): 입력 JSON 파일 경로
    """
    # 입력 파일 읽기
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    classified_data = {}

    # ThreadPoolExecutor를 사용하여 병렬로 카테고리 분류 작업 수행
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_restaurant = {executor.submit(process_restaurant, restaurant, details): restaurant for restaurant, details in data.items()}
        for future in as_completed(future_to_restaurant):
            restaurant, details = future.result()
            classified_data[restaurant] = details

    # 현재 시간을 기반으로 파일 이름 생성
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"classified_data_{current_time}.json"

    # 분류된 데이터를 JSON 파일로 저장
    with open(save_path, "w", encoding="utf-8") as file:
        json.dump(classified_data, file, ensure_ascii=False, indent=4)

    print(f"분류된 데이터가 {save_path}에 저장되었습니다.")


if __name__ == "__main__":
    # 예시 파일 이름 설정
    input_filename = "crawled_data_20240603_003043.json"
    process_restaurants(input_filename)
