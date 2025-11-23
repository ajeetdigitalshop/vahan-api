from flask import Flask, request
import pytesseract
import requests
import cv2
import numpy as np
from PIL import Image
from bs4 import BeautifulSoup, SoupStrainer
from io import BytesIO
import re
from time import sleep

app = Flask(__name__)

APP_URL = 'https://vahan.nic.in/nrservices/faces/user/searchstatus.xhtml'
CAPTCHA_URL = 'https://vahan.nic.in/nrservices/cap_img.jsp'

def enhance():
    img = cv2.imread('captcha.png', 0)
    kernel = np.ones((2,2), np.uint8)
    img_erosion = cv2.erode(img, kernel, iterations=1)
    img_dilation = cv2.dilate(img_erosion, kernel, iterations=1)
    final = cv2.GaussianBlur(img_dilation, (1,1), 0)
    return final

def solve_captcha():
    iresponse = requests.get(CAPTCHA_URL)
    img = Image.open(BytesIO(iresponse.content))
    img.save("captcha.png")

    enhanced = enhance()
    text = pytesseract.image_to_string(enhanced)
    return re.sub(r"[^A-Za-z0-9]", "", text)

def check_vehicle(number):
    r = requests.get(APP_URL)
    cookies = r.cookies
    soup = BeautifulSoup(r.text, 'html.parser')
    viewstate = soup.select('input[name="javax.faces.ViewState"]')[0]['value']
    button = soup.find("button", {"type": "submit"})
    captcha = solve_captcha()
    data = {
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': button['id'],
        'javax.faces.partial.execute': '@all',
        'javax.faces.partial.render': 'rcDetailsPanel resultPanel userMessages capatcha txt_ALPHA_NUMERIC',
        button['id']: button['id'],
        'masterLayout': 'masterLayout',
        'regn_no1_exact': number,
        'txt_ALPHA_NUMERIC': captcha,
        'javax.faces.ViewState': viewstate,
        'j_idt32': ''
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Faces-Request': 'partial/ajax',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': "Mozilla/5.0"
    }
    sleep(1)
    post = requests.post(APP_URL, data=data, headers=headers, cookies=cookies)
    rsoup = BeautifulSoup(post.text, 'html.parser')
    table = SoupStrainer('tr')
    result = BeautifulSoup(rsoup.get_text(), 'html.parser', parse_only=table)
    return result.get_text("\n").strip()

@app.route("/")
def home():
    return "Vahan API Running ✔"

@app.route("/check")
def check():
    num = request.args.get("number")
    if not num:
        return "missing: ?number=MH12AB1234"
    result = check_vehicle(num)
    return f"<pre>{result}</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
