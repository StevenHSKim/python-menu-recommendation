import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QRadioButton, QButtonGroup, QMessageBox, QProgressDialog, QDialog, QCheckBox, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer
import crawling
import recommendation
import classify_food
from recommendation import FoodType, Menu


class LoadingDialog(QProgressDialog):
    """
    로딩 중임을 나타내는 진행 표시 대화 상자 클래스
    """
    def __init__(self, message: str, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("로딩 중...")
        self.setLabelText(message)
        self.setCancelButton(None)
        self.setRange(0, 100)
        self.setValue(0)
        self.setWindowModality(Qt.WindowModal)

    def update_message(self, message: str):
        self.setLabelText(message)
        self.setValue(self.value() + 10)
        QApplication.processEvents()


class ReRecommendationDialog(QDialog):
    """
    재추천 옵션을 선택할 수 있는 대화 상자 클래스
    """
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("재추천 옵션")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.retry_check = QCheckBox("다시 추천해줘")
        self.cafeteria_check = QCheckBox("그럼 학식은 어떠세요?")

        re_groupcheck = QButtonGroup(self)
        re_groupcheck.addButton(self.retry_check)
        re_groupcheck.addButton(self.cafeteria_check)

        layout.addWidget(self.retry_check)
        layout.addWidget(self.cafeteria_check)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)
        self.setLayout(layout)


class ResultDialog(QDialog):
    yes_check = None
    no_check = None
    buttons = None

    def __init__(self, recommendations: list[Menu], dessert_recommendations: list[Menu], parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("추천 결과")
        self.setGeometry(100, 100, 800, 600)
        self.recommendations = recommendations
        self.dessert_recommendations = dessert_recommendations

        layout = QVBoxLayout()

        result_str = "오늘은 이런 메뉴 어때요?\n"
        result_str += "\n\n".join([self.format_menu(i, menu) for i, menu in enumerate(self.recommendations)])

        dessert_str = "오늘 이런 디저트는 어때요?\n"
        dessert_str += "\n\n".join([self.format_menu(i, menu) for i, menu in enumerate(self.dessert_recommendations)])

        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_text.setText(f"{result_str}\n\n{dessert_str}")

        layout.addWidget(result_text)

        satisfaction_label = QLabel("추천 결과에 만족하시나요?")
        layout.addWidget(satisfaction_label)

        self.yes_check = QCheckBox("예")
        self.no_check = QCheckBox("아니오")

        result_group = QButtonGroup(self)
        result_group.addButton(self.yes_check)
        result_group.addButton(self.no_check)

        layout.addWidget(self.yes_check)
        layout.addWidget(self.no_check)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.on_accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def format_menu(self, index: int, menu: Menu) -> str:
        """
        메뉴 포맷을 설정하는 함수
        """
        menu_str = f"{index + 1}. {menu.name} ({menu.food_type})\n"
        menu_str += "메뉴:\n"
        for dish in menu.description.split(", "):
            menu_str += f"{dish}\n"
        return menu_str

    def on_accept(self):
        if self.yes_check.isChecked():
            QMessageBox.information(self, "종료", "메뉴 추천 프로그램을 종료합니다.")
            self.accept()
            QApplication.quit()
        elif self.no_check.isChecked():
            re_recommendation_dialog = ReRecommendationDialog(self)
            if re_recommendation_dialog.exec_() == QDialog.Accepted:
                if re_recommendation_dialog.retry_check.isChecked():
                    self.retry_recommendation()
                elif re_recommendation_dialog.cafeteria_check.isChecked():
                    self.recommend_school_meal()

    def retry_recommendation(self):
        """
        최신 분류된 데이터에서 랜덤으로 추천하는 함수
        """
        filename = recommendation.get_latest_classified_file()
        data = recommendation.load_data(filename)

        recommendations: list[Menu] = []
        dessert_recommendations: list[Menu] = []

        for name, details in data.items():
            food_type_str: str = details["category"]
            food_type: FoodType = next(e for e in FoodType if e.value[1] == food_type_str)
            menu = Menu(name, food_type, description=details["menu"], price=None)
            if food_type == FoodType.DESSERT:
                dessert_recommendations.append(menu)
            else:
                recommendations.append(menu)

        if len(recommendations) > 5:
            recommendations = random.sample(recommendations, 5)
        if len(dessert_recommendations) > 2:
            dessert_recommendations = random.sample(dessert_recommendations, 2)

        new_dialog = ResultDialog(recommendations, dessert_recommendations, self)
        new_dialog.exec_()

    def recommend_school_meal(self):
        """
        학교 급식을 추천하는 함수
        """
        progress_dialog = LoadingDialog("학식 정보를 가져오는 중입니다...", self)
        progress_dialog.show()
        QApplication.processEvents()

        school_meal_filename = crawling.crawl_school_meal()
        progress_dialog.close()

        data = recommendation.load_data(school_meal_filename)

        recommendations: list[Menu] = []
        for cafeteria, details in data.items():
            if 'menu' in details:
                for menu_name, info in details["menu"].items():
                    menu = Menu(menu_name, description=info["type"])
                    recommendations.append(menu)
            else:
                for sub_cafeteria in details.values():
                    for menu_name, info in sub_cafeteria["menu"].items():
                        menu = Menu(menu_name, description=info["type"])
                        recommendations.append(menu)

        new_dialog = SchoolMealResultDialog(data, self)
        new_dialog.exec_()


class SchoolMealResultDialog(QDialog):
    def __init__(self, data, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("학식 추천 결과")
        self.setGeometry(100, 100, 800, 600)
        self.data = data

        layout = QVBoxLayout()

        result_str = self.format_school_meal_data(self.data)

        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_text.setText(result_str)

        layout.addWidget(result_text)
        self.setLayout(layout)
        satisfaction_label = QLabel("추천 결과에 만족하시나요?")
        layout.addWidget(satisfaction_label)

        self.yes_check = QCheckBox("예")
        self.no_check = QCheckBox("아니오")

        school_group = QButtonGroup(self)
        school_group.addButton(self.yes_check)
        school_group.addButton(self.no_check)
        
        layout.addWidget(self.yes_check)
        layout.addWidget(self.no_check)

        self.buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.on_accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def format_school_meal_data(self, data) -> str:
        result_str = ""
        for cafeteria, details in data.items():
            if "menu" in details:
                result_str += f"{cafeteria}:\n메뉴:\n"
                for menu, info in details["menu"].items():
                    result_str += f"{menu}\n"
            else:
                for sub_cafeteria, sub_details in details.items():
                    result_str += f"{cafeteria} 메뉴 {sub_cafeteria}:\n"
                    for menu, info in sub_details["menu"].items():
                        result_str += f"{menu}\n"
            result_str += "\n"
        return result_str

    def format_menu(self, index: int, menu: Menu) -> str:
        """
        메뉴 포맷을 설정하는 함수
        """
        menu_str = f"{index + 1}. {menu.name} ({menu.food_type})\n"
        menu_str += "메뉴:\n"
        for dish in menu.description.split(", "):
            menu_str += f"{dish}\n"
        return menu_str

    def on_accept(self):
        if self.yes_check.isChecked():
            QMessageBox.information(self, "종료", "메뉴 추천 프로그램을 종료합니다.")
            self.accept()
            QApplication.quit()
        elif self.no_check.isChecked():
            re_recommendation_dialog = ReRecommendationDialog(self)
            if re_recommendation_dialog.exec_() == QDialog.Accepted:
                if re_recommendation_dialog.retry_check.isChecked():
                    self.retry_recommendation()
                elif re_recommendation_dialog.cafeteria_check.isChecked():
                    self.recommend_school_meal()

    def retry_recommendation(self):
        """
        최신 분류된 데이터에서 랜덤으로 추천하는 함수
        """
        filename = recommendation.get_latest_classified_file()
        data = recommendation.load_data(filename)

        recommendations: list[Menu] = []
        dessert_recommendations: list[Menu] = []

        for name, details in data.items():
            food_type_str: str = details["category"]
            food_type: FoodType = next(e for e in FoodType if e.value[1] == food_type_str)
            menu = Menu(name, food_type, description=details["menu"], price=None)
            if food_type == FoodType.DESSERT:
                dessert_recommendations.append(menu)
            else:
                recommendations.append(menu)

        if len(recommendations) > 5:
            recommendations = random.sample(recommendations, 5)
        if len(dessert_recommendations) > 2:
            dessert_recommendations = random.sample(dessert_recommendations, 2)

        new_dialog = ResultDialog(recommendations, dessert_recommendations, self)
        new_dialog.exec_()

    def recommend_school_meal(self):
        """
        학교 급식을 추천하는 함수
        """
        progress_dialog = LoadingDialog("학식 정보를 가져오는 중입니다...", self)
        progress_dialog.show()
        QApplication.processEvents()

        school_meal_filename = crawling.crawl_school_meal()
        progress_dialog.close()

        data = recommendation.load_data(school_meal_filename)

        recommendations: list[Menu] = []
        for cafeteria, details in data.items():
            if 'menu' in details:
                for menu_name, info in details["menu"].items():
                    menu = Menu(menu_name, description=info["type"])
                    recommendations.append(menu)
            else:
                for sub_cafeteria in details.values():
                    for menu_name, info in sub_cafeteria["menu"].items():
                        menu = Menu(menu_name, description=info["type"])
                        recommendations.append(menu)

        new_dialog = SchoolMealResultDialog(data, self)
        new_dialog.exec_()


class MenuRecommendationApp(QWidget):
    """
    메뉴 추천 애플리케이션 메인 클래스
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("메뉴 추천 프로그램")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QVBoxLayout()

        self.radius_label = QLabel("이동 방법을 선택해주세요:")
        self.main_layout.addWidget(self.radius_label)

        self.walk_nearby = QRadioButton("근처로 걸어가고 싶어요 (1km)")
        self.walk_more = QRadioButton("조금 더 걸어가도 돼요 (2km)")
        self.drive = QRadioButton("차를 타고 이동할거에요 (10km)")

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.walk_nearby)
        self.button_group.addButton(self.walk_more)
        self.button_group.addButton(self.drive)

        self.main_layout.addWidget(self.walk_nearby)
        self.main_layout.addWidget(self.walk_more)
        self.main_layout.addWidget(self.drive)

        self.history_label = QLabel("최근 3일 동안 먹은 음식 종류를 선택하세요:")
        self.main_layout.addWidget(self.history_label)

        self.food_types = ["한식", "중식", "일식", "양식", "아시안", "디저트", "그외"]
        self.meals = ["아침", "점심", "저녁"]
        self.days = ["1일 전", "2일 전", "3일 전"]

        self.radio_buttons = {}

        for day in self.days:
            day_layout = QHBoxLayout()
            day_label = QLabel(f"{day}:")
            day_layout.addWidget(day_label)

            for meal in self.meals:
                meal_layout = QVBoxLayout()
                meal_label = QLabel(f"{meal}")
                meal_layout.addWidget(meal_label)

                self.radio_buttons[f"{day}_{meal}"] = []
                button_group = QButtonGroup(self)

                for idx, food_type in enumerate(self.food_types):
                    radio_button = QRadioButton(f"{idx+1}: {food_type}")
                    meal_layout.addWidget(radio_button)
                    button_group.addButton(radio_button)
                    self.radio_buttons[f"{day}_{meal}"].append(radio_button)

                day_layout.addLayout(meal_layout)

            self.main_layout.addLayout(day_layout)

        self.recommend_button = QPushButton("메뉴 추천", self)
        self.recommend_button.clicked.connect(self.recommend_menu)
        self.main_layout.addWidget(self.recommend_button)

        self.result_text = QTextEdit(self)
        self.result_text.setReadOnly(True)
        self.main_layout.addWidget(self.result_text)

        self.setLayout(self.main_layout)

    def get_radius(self) -> int | None:
        """
        선택한 반경을 반환하는 함수
        """
        if self.walk_nearby.isChecked():
            return 15  # 1km 반경
        elif self.walk_more.isChecked():
            return 14  # 2km 반경
        elif self.drive.isChecked():
            return 11  # 10km 반경
        else:
            QMessageBox.warning(self, "Error", "이동 방법을 선택해주세요.")
            return None

    def get_food_history(self) -> dict[str, list[FoodType]]:
        """
        최근 3일 동안 먹은 음식 종류를 반환하는 함수
        """
        food_history = {day: [] for day in self.days}
        for day in self.days:
            for meal in self.meals:
                for idx, radio_button in enumerate(self.radio_buttons[f"{day}_{meal}"]):
                    if radio_button.isChecked():
                        food_history[day].append(FoodType.value_of(idx + 1))
                        break
        return food_history

    def crawl_and_classify(self, radius: int, progress_dialog: LoadingDialog):
        """
        크롤링 및 분류 작업을 수행하는 함수
        """
        # Start crawling
        progress_dialog.update_message("음식점 데이터 크롤링 중입니다. 잠시만 기다려주세요.")

        input_filename = crawling.crawl(radius)

        progress_dialog.update_message("음식점 분류 작업 중입니다. 잠시만 기다려주세요.")

        classify_food.process_restaurants(input_filename)

        progress_dialog.setValue(100)

    def recommend_menu(self):
        """
        메뉴 추천을 수행하는 함수
        """
        radius = self.get_radius()
        if radius is not None:
            progress_dialog = LoadingDialog("작업을 준비 중입니다...", self)
            progress_dialog.show()
            QApplication.processEvents()  # 업데이트 강제 실행

            self.crawl_and_classify(radius, progress_dialog)
            progress_dialog.close()

            food_history = self.get_food_history()
            if any(food_history.values()):
                try:
                    recommendations, dessert_recommendations = recommendation.get_recommendations(food_history)

                    self.show_result_dialog(recommendations, dessert_recommendations)
                except ValueError as e:
                    self.result_text.setText(str(e))
            else:
                self.result_text.setText("최근 3일 동안 먹은 음식 종류를 선택해주세요.")
        else:
            self.result_text.setText("반경을 선택해주세요.")

    def show_result_dialog(self, recommendations: list[Menu], dessert_recommendations: list[Menu]):
        """
        결과 대화 상자를 보여주는 함수
        """
        result_dialog = ResultDialog(recommendations, dessert_recommendations, self)
        result_dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MenuRecommendationApp()
    ex.show()
    sys.exit(app.exec_())
