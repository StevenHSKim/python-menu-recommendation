import sys
import random
import streamlit as st
from recommendation import FoodType, Menu
import crawling
import recommendation
import classify_food
from recommendation import get_recommendations


def show_result_dialog(recommendations, dessert_recommendations):
    """
    추천 결과를 스트림릿을 통해 보여주는 함수
    """
    st.subheader("추천 결과")
    
    st.write("### 오늘은 이런 메뉴 어때요?")
    for i, menu in enumerate(recommendations):
        st.write(f"**{i + 1}. {menu.name} ({menu.food_type})**")
        st.write(f"설명: {menu.description}")
        st.write(f"가중치: {menu.weight}")
        st.write("---")

    st.write("### 오늘 이런 디저트는 어때요?")
    for i, menu in enumerate(dessert_recommendations):
        st.write(f"**{i + 1}. {menu.name} ({menu.food_type})**")
        st.write(f"설명: {menu.description}")
        st.write(f"가중치: {menu.weight}")
        st.write("---")


def get_radius():
    """
    Streamlit에서 사용자가 선택한 반경을 반환하는 함수
    """
    radius = st.radio(
        "이동 방법을 선택해주세요:",
        ("근처로 걸어가고 싶어요 (1km)", "조금 더 걸어가도 돼요 (2km)", "차를 타고 이동할거에요 (10km)")
    )

    if radius == "근처로 걸어가고 싶어요 (1km)":
        return 15
    elif radius == "조금 더 걸어가도 돼요 (2km)":
        return 14
    elif radius == "차를 타고 이동할거에요 (10km)":
        return 11
    else:
        return None


def get_food_history():
    """
    사용자의 최근 섭취 음식을 Streamlit에서 입력받아 반환하는 함수
    """
    st.write("### 최근 3일 동안 먹은 음식 종류를 선택하세요:")

    food_types = ["한식", "중식", "일식", "양식", "아시안", "디저트", "그외"]
    meals = ["아침", "점심", "저녁"]
    days = ["1일 전", "2일 전", "3일 전"]

    food_history = {day: [] for day in days}

    for day in days:
        st.write(f"**{day}**:")
        for meal in meals:
            selected_food_type = st.selectbox(f"{meal}에 먹은 음식 종류", ["선택안함"] + food_types, key=f"{day}_{meal}")
            if selected_food_type != "선택안함":
                food_history[day].append(FoodType.value_of(food_types.index(selected_food_type) + 1))

    return food_history


def crawl_and_classify(radius):
    """
    크롤링 및 분류 작업을 수행하는 함수
    """
    with st.spinner("음식점 데이터 크롤링 및 분류 작업 중... 잠시만 기다려주세요."):
        input_filename = crawling.crawl(radius)
        classify_food.process_restaurants(input_filename)


def main():
    """
    Streamlit 애플리케이션 메인 함수
    """
    st.title("메뉴 추천 프로그램")

    # 반경 선택
    radius = get_radius()

    if radius is not None:
        st.write(f"선택된 반경: {radius}km")

        # 최근 음식 섭취 기록 받기
        food_history = get_food_history()

        if st.button("메뉴 추천"):
            # 크롤링 및 분류 작업 실행
            crawl_and_classify(radius)

            # 음식 섭취 기록을 기반으로 메뉴 추천
            if any(food_history.values()):
                try:
                    recommendations, dessert_recommendations = get_recommendations(food_history)
                    show_result_dialog(recommendations, dessert_recommendations)
                except ValueError as e:
                    st.error(str(e))
            else:
                st.warning("최근 3일 동안 먹은 음식 종류를 선택해주세요.")
    else:
        st.warning("이동 방법을 선택해주세요.")


if __name__ == "__main__":
    main()
