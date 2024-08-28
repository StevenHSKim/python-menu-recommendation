import random
import streamlit as st
import crawling
import recommendation
import classify_food
from recommendation import FoodType, Menu

# 상태 초기화
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'dessert_recommendations' not in st.session_state:
    st.session_state.dessert_recommendations = None
if 'school_meal_data' not in st.session_state:
    st.session_state.school_meal_data = None
if 'state' not in st.session_state:
    st.session_state.state = "start"

# 배경화면 설정 함수
def add_bg_from_url():
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("https://i.imgur.com/MwczjjT.png");
             background-attachment: fixed;
             background-size: cover;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

# 상태 변경 함수
def set_state(new_state):
    st.session_state.state = new_state

# 메뉴 추천을 위한 폼 구성
def input_page():
    add_bg_from_url()  # 배경화면 추가
    st.title("CAU 위치-기반 메뉴 추천 프로그램")
    st.subheader("CAU Location-Based Menu Recommendation Program")
    st.write("---")
    st.write("### 이동 반경을 선택하세요")
    # radius = st.radio(
    #     "이동 방법을 선택해주세요:",
    #     ["근처로 걸어가고 싶어요 (1km)", "조금 더 걸어가도 돼요 (2km)", "차를 타고 이동할거에요 (10km)"]
    # )
    radius = st.slider(
        "이동 반경을 선택해주세요 (11:약 10km, 15:약 1km):",
        min_value=11, max_value=15, value=11, step=1
    )


    food_types = ["한식", "중식", "일식", "양식", "아시안", "디저트", "그외"]
    meals = ["아침", "점심", "저녁"]
    days = ["1일 전", "2일 전", "3일 전"]

    food_history = {day: [] for day in days}

    st.write("### 최근 3일 동안 먹은 음식 종류를 선택하세요:")
    for day in days:
        st.write(f"**{day}**:")
        for meal in meals:
            selected_food_type = st.selectbox(f"{meal}에 먹은 음식 종류", ["선택안함"] + food_types, key=f"{day}_{meal}")
            if selected_food_type != "선택안함":
                food_history[day].append(FoodType.value_of(food_types.index(selected_food_type) + 1))

    # 메뉴 추천 버튼
    # if st.button("메뉴 추천"):
    #     if any(food_history.values()):
    #         radius_map = {"근처로 걸어가고 싶어요 (1km)": 15, "조금 더 걸어가도 돼요 (2km)": 14, "차를 타고 이동할거에요 (10km)": 11}
    #         radius_value = radius_map[radius]
    #         crawl_and_classify(radius_value, food_history)
    #     else:
    #         st.warning("최근 3일 동안 먹은 음식 종류를 선택해주세요.")
    if st.button("메뉴 추천"):
        if any(food_history.values()):
            crawl_and_classify(radius, food_history)
        else:
            st.warning("최근 3일 동안 먹은 음식 종류를 선택해주세요.")


# 크롤링 및 데이터 분류 작업 수행
def crawl_and_classify(radius, food_history):
    with st.spinner("음식점 데이터를 가져오는 중입니다..."):
        input_filename = crawling.crawl(radius)

    with st.spinner("음식점 데이터를 분류하는 중입니다..."):
        classify_food.process_restaurants(input_filename)

    try:
        recommendations, dessert_recommendations = recommendation.get_recommendations(food_history)
        st.session_state.recommendations = recommendations
        st.session_state.dessert_recommendations = dessert_recommendations
        set_state("result")
    except ValueError as e:
        st.error(str(e))

# 추천 결과를 보여주는 페이지
def result_page():
    add_bg_from_url()  # 배경화면 추가
    st.subheader("추천 결과")
    
    if st.session_state.recommendations:
        st.write("### 오늘은 이런 메뉴 어때요?")
        for i, menu in enumerate(st.session_state.recommendations):
            st.write(f"**{i + 1}. {menu.name} ({menu.food_type})**")
            st.write(f"설명: {menu.description}")
            st.write("---")

    if st.session_state.dessert_recommendations:
        st.write("### 오늘 이런 디저트는 어때요?")
        for i, menu in enumerate(st.session_state.dessert_recommendations):
            st.write(f"**{i + 1}. {menu.name} ({menu.food_type})**")
            st.write(f"설명: {menu.description}")
            st.write("---")
    else:
        st.write("디저트 추천이 없습니다.")

    st.write("### 추천 결과에 만족하시나요?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("예"):
            st.session_state.state = "start"
            st.success("감사합니다! 홈 화면으로 돌아갑니다.")

    with col2:
        if st.button("아니오"):
            st.session_state.state = "re_recommendation"

# 재추천 페이지
def re_recommendation_page():
    add_bg_from_url()  # 배경화면 추가
    st.write("### 어떤 재추천을 원하시나요?")
    
    col1, col2, col3 = st.columns([1, 1, 1], gap="large")
    
    with col1:
        st.write("")  # 여백 추가
        if st.button("다시 추천해줘", key="retry_button", help="다시 메뉴 추천을 받으세요"):
            with st.spinner("메뉴를 재추천 중입니다..."):
                retry_recommendation()
            set_state("result")

    with col2:
        st.write("")  # 여백 추가
        if st.button("그럼 학식은 어떠세요?", key="school_meal_button", help="오늘의 학식을 추천받으세요"):
            with st.spinner("학식 데이터를 가져오는 중입니다..."):
                recommend_school_meal()
            set_state("school_meal_result")

    with col3:
        st.write("")  # 여백 추가
        if st.button("홈 화면으로 돌아가기", key="home_button", help="메인 화면으로 돌아갑니다"):
            st.session_state.state = "start"
            st.success("홈 화면으로 돌아갑니다.")

# 학식 추천 결과 페이지
def school_meal_result_page():
    add_bg_from_url()  # 배경화면 추가
    st.subheader("학식 추천 결과")

    if st.session_state.school_meal_data:
        for cafeteria, details in st.session_state.school_meal_data.items():
            st.write(f"**{cafeteria}:**")
            if 'menu' in details:
                for menu, info in details["menu"].items():
                    st.write(f" - {menu}: {info['type']}")
            else:
                for sub_cafeteria, sub_details in details.items():
                    st.write(f"  *{sub_cafeteria}:*")
                    if 'menu' in sub_details:
                        for menu, info in sub_details["menu"].items():
                            st.write(f"   - {menu}: {info['type']}")
                    else:
                        st.write("   - 메뉴 정보가 없습니다.")
        st.write("---")

    if st.button("홈 화면으로 돌아가기"):
        st.session_state.state = "start"
        st.success("홈 화면으로 돌아갑니다.")

# 재추천 기능
def retry_recommendation():
    filename = recommendation.get_latest_classified_file()
    recommendations, dessert_recommendations = recommendation.get_random_recommendations(filename)
    st.session_state.recommendations = recommendations
    st.session_state.dessert_recommendations = dessert_recommendations

# 학식 추천 기능
def recommend_school_meal():
    school_meal_filename = crawling.crawl_school_meal()
    data = recommendation.load_data(school_meal_filename)
    st.session_state.school_meal_data = data

# 메인 페이지 흐름 관리
def main():
    current_state = st.session_state.state
    add_bg_from_url()  # 배경화면 추가

    if current_state == "start":
        input_page()
    elif current_state == "result":
        result_page()
    elif current_state == "re_recommendation":
        re_recommendation_page()
    elif current_state == "school_meal_result":
        school_meal_result_page()

if __name__ == "__main__":
    main()
