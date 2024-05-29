from typing import *
from enum import Enum


class FoodType(Enum):
    KOREAN = (1, "한식")
    ASIAN = (2, "아시아")
    CHINESE = (3, "중식")
    JAPANESE = (4, "일식")
    WESTERN = (5, "양식")

    def value(self) -> tuple[int, str]:
        return super().value()

    @staticmethod
    def value_of(value: int):
        for e in FoodType:
            if e.value()[0] == value:
                return e
        raise ValueError(f"No such type: {value}")

    def __str__(self) -> str:
        return self.value()[1]


class Menu:
    def __init__(self, name: str, food_type: FoodType | None = None, description: str | None = None, price: int | None = None):
        self.name: Final[str] = name
        self.food_type: Final[FoodType | None] = food_type
        self.description: Final[str | None] = description
        self.price: Final[int | None] = price

    def __str__(self) -> str:
        result: str = f"{self.name}"
        if self.food_type is not None:
            result += f" ({self.food_type})"
        if self.description is not None:
            result += f"\n설명: {self.description}"
        if self.price is not None:
            result += f"\n가격: {self.price}원"
        return result


def do_while(r: Callable[[], bool]):
    result: bool = r()
    while result is True:
        result = r()


def run():
    print("최근 일주일 이내 먹은 음식의 종류를 모두 입력하세요.", )
    print("\n".join(map(lambda it: f"{it.value()[0]}: {it.value()[1]}", FoodType)))
    print("예시: 1 3 4")
    types: list[FoodType] = []

    def require_food_history() -> bool:
        response: str = input(">> ")
        types.clear()
        for s in response.split(" "):
            try:
                types.append(FoodType.value_of(int(s)))
            except ValueError:
                print(f"알 수 없는 종류: {s}")
                return True
        return False

    do_while(require_food_history)
    history: set[FoodType] = set(types)
    # run_something(history)


def print_result(recommendations: list[Menu]):
    print("추천 메뉴는 다음과 같습니다:")
    print("\n\n".join(map(lambda it: f"{it[0]}. {it[1]}", enumerate(recommendations))))
