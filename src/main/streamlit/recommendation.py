from enum import Enum
from typing import *
import json
import os
import random
import glob


class FoodType(Enum):
    KOREAN = (1, "한식")
    CHINESE = (2, "중식")
    JAPANESE = (3, "일식")
    WESTERN = (4, "양식")
    ASIAN = (5, "아시안")
    DESSERT = (6, "디저트")
    OTHER = (7, "그외")

    @staticmethod
    def value_of(value: int):
        for e in FoodType:
            if e.value[0] == value:
                return e
        raise ValueError(f"No such type: {value}")

    def __str__(self) -> str:
        return self.value[1]


class Menu:
    def __init__(self, name: str, food_type: FoodType = None, description: str = None, price: int = None):
        self.name: Final[str] = name
        self.food_type: Final[FoodType | None] = food_type
        self.description: Final[str | None] = description
        self.price: Final[int | None] = price
        self.weight: int = 0  # 가중치 초기값

    def __str__(self) -> str:
        result: str = f"{self.name}"
        if self.food_type is not None:
            result += f" ({self.food_type})"
        if self.description is not None:
            result += f"\n설명: {self.description}"
        if self.price is not None:
            result += f"\n가격: {self.price}원"
        result += f"\n가중치: {self.weight}"
        return result


# JSON 파일에서 데이터를 로드하는 함수
def load_data(filename: str) -> Any:
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# 음식 섭취 기록을 기반으로 가중치를 계산하는 함수
def calculate_weights(food_history: dict[str, List[FoodType]]) -> dict[FoodType, int]:
    weights = {food_type: 0 for food_type in FoodType}
    weight_values = {"1일 전": 3, "2일 전": 2, "3일 전": 1}

    for day, food_types in food_history.items():
        for food_type in food_types:
            weights[food_type] -= weight_values[day]

    return weights


# 데이터를 기반으로 가중치를 적용하는 함수
def apply_weights(data: dict[str, Any], weights: dict[FoodType, int]):
    for restaurant, details in data.items():
        food_type_str = details["category"]
        food_type = next(e for e in FoodType if e.value[1] == food_type_str)
        details["weight"] = weights[food_type]

        if details["program"] is not None:
            details["weight"] += 3

        if details["rate"] is not None:
            details["weight"] += details["rate"] * 0.3

        if details["review"] is not None:
            details["weight"] += details["review"] * 0.001


# 최신 분류된 파일을 가져오는 함수
def get_latest_classified_file() -> str:
    list_of_files = glob.glob("classified_data_*.json")
    latest_file = max(list_of_files, key=os.path.getmtime)
    return latest_file


# 추천을 생성하는 함수
def get_recommendations(food_history: dict[str, list[FoodType]]) -> tuple[list[Menu], list[Menu]]:
    filename = get_latest_classified_file()
    if not os.path.exists(filename):
        raise FileNotFoundError(f"No data file found: {filename}")

    data = load_data(filename)
    weights = calculate_weights(food_history)
    apply_weights(data, weights)

    recommendations = []
    dessert_recommendations = []

    for name, details in data.items():
        food_type_str = details["category"]
        food_type = next(e for e in FoodType if e.value[1] == food_type_str)
        menu = Menu(name, food_type, description=details["menu"], price=None)
        menu.weight = details["weight"]
        if food_type == FoodType.DESSERT:
            dessert_recommendations.append(menu)
        else:
            recommendations.append(menu)

    recommendations.sort(key=lambda x: x.weight, reverse=True)
    dessert_recommendations.sort(key=lambda x: x.weight, reverse=True)

    # 가중치가 높은 상위 3개 추천
    top_recommendations = recommendations[:3]

    # 나머지 2개를 랜덤으로 선택
    remaining_recommendations = recommendations[3:]
    if len(remaining_recommendations) > 2:
        top_recommendations.extend(random.sample(remaining_recommendations, 2))
    else:
        top_recommendations.extend(remaining_recommendations[:2])

    top_dessert_recommendations = dessert_recommendations[:2]

    return top_recommendations, top_dessert_recommendations
