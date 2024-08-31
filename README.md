# Basic Programming - Team18
### Description
“Location-based menu recommendations for CAU students” with user location-based menu recommendation option and CAU cafeteria menu recommendation option.

<img alt="image" src="https://github.com/user-attachments/assets/7d63be67-5575-4f4d-8ae3-56282bcb2552"><br>

<br>

## Preparation

### To work properly (paid)

1. Put your OpenAI API Key in `classify_food.py`.
2. Run `app.py`.

### Just check operation (free)

Food is not being classified correctly and is all in the 'other' category.

1. Run `app.py`.

### How to set up an OpenAI API Key

1. Create an OpenAI API account: [https://platform.openai.com/signup](https://platform.openai.com/signup)
2. Register a credit card ← If you use the key without registering, you will get an error. (First registration costs $5)
3. Get an API key: [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
4. Write your secret API key to your_openai.api_key in `classify_food.py`.

```python
openai.api_key = “your_openai_api_key”
```
<br>

## Run on Web (Streamlit)

To run this program on the web, run the code below in your terminal.

```bash
streamlit run ./app_streamlit.py
```
<br>

## Dependencies

* Python 3.11
* [Beautiful Soup](https://pypi.org/project/beautifulsoup4/) 4.12.3
* [Selenium](https://pypi.org/project/selenium/) 4.21.0
* [Pandas](https://pypi.org/project/pandas/) 2.2.2
* [PyQt5](https://pypi.org/project/PyQt5/) 5.15.10
* [openai](https://pypi.org/project/openai/0.28.1/) 0.28.1
* [requests](https://pypi.org/project/requests/2.32.2) 2.32.2

<br>

## License

This project is licensed under the GNU GPL version 3.

<br>

## Third-party notices

See the [third party notices](/THIRD-PARTY-NOTICES) file.
