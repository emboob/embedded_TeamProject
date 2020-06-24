from urllib.request import urlopen, Request
import urllib
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from gtts import gTTS
import pymysql
import os
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
PIR_PIN = 7
GPIO.setup(PIR_PIN, GPIO.IN)
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")


def running():
    del_list = []  # 삭제할 row 목록
    success_list = []  # 완료된 row 목록
    db = pymysql.connect("localhost", "root", "1234", "umbrella")
    cur = db.cursor()
    cur.execute("SELECT * FROM memo;")
    result = cur.fetchall()
    for rs in result:
        if check_time_range(rs[3]) and check_last_output(rs[4]):
            if rs[6] == 0:
                play_gtts(rs[2])
            elif rs[6] == 1:
                typecast(rs[2])
            else:
                play_gtts(rs[2])
            if rs[5] == 0:  # 한 번만 출력하는 경우 삭제할 목록에 추가
                del_list.append(rs[0])
            else:  # 마지막 출력 시간 저장을 위해 목록에 추가
                success_list.append(rs[0])

    for dl in del_list:
        cur.execute("DELETE FROM memo WHERE memo_no = %s;", (dl))
        db.commit()
    for sl in success_list:
        cur.execute("UPDATE memo SET memo_lastoutput = %s WHERE memo_no = %s",
                    (datetime.today().strftime("%Y-%m-%d %H:%M:%S"), sl))
        db.commit()
    db.close()


def check_time_range(res_time):  # 설정한 시간에서 +-1시간 이내이면 true
    if res_time is None:
        return False
    elif res_time == "":
        return False
    date_time = datetime.strptime(datetime.today().strftime("%Y-%m-%d") + " " + res_time.split(' ')[1],
                                  "%Y-%m-%d %H:%M:%S")
    if date_time > datetime.today() - timedelta(hours=1) and date_time < datetime.today() + timedelta(hours=1):
        return True
    else:
        return False


def check_last_output(res_time):  # 마지막 출력이 없거나 오늘이 아니면 true
    if res_time is None:
        return True
    elif res_time == "":
        return True
    # res_time = res_time.replace(" ", "")
    date_time = datetime.strptime(res_time, "%Y-%m-%d %H:%M:%S")
    if date_time < datetime.today() - timedelta(days=1):
        return True
    else:
        return False


def typecast(input_data):  # 크롤링을 통해 typecast라는 사이트를 이용
    # 화면 없이 실행
    driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', chrome_options=options)

    # 화면 띄우면서 실행
    # driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')

    # Login
    driver.get('https://typecast.ai/login');  # 접속
    search_box = driver.find_element_by_css_selector('#email')  # email 입력칸
    search_box.send_keys('emboob@naver.com')  # 키워드를 입력하고
    search_box = driver.find_element_by_css_selector('#password')  # password 입력칸
    search_box.send_keys('jksd1633!')  # 키워드를 입력하고
    search_box = driver.find_element_by_css_selector('#app > div.view > form')  # Login 버튼
    search_box.submit()  # 실행합니다.
    time.sleep(5)  # wait loading

    # 출력
    search_box = driver.find_element_by_css_selector(
        '#app > div.tool-wrapper.view > div > div.menu-all.tool-menu > div:nth-child(5) > div > div > div > div > img')  # 홍보화면 x버튼
    search_box.click()  # 실행합니다.
    search_box = driver.find_element_by_css_selector(
        '#app > div.tool-wrapper.view > div > div.tool-body > div.editor-container.editor-layout.editor-view > div.editor-container-box.ns-column > div.editor > div.editor__wrapper.d-flex > div > div')  # 텍스트 입력창
    search_box.send_keys(input_data)  # 키워드를 입력하고
    search_box = driver.find_element_by_css_selector(
        '#app > div.tool-wrapper.view > div > div.tool-body > div.player-bar-container.editor-container.player-bar > div.player-bar-container-box.editor-container-box.ns-fill-grey.ns-column > div.player-content > div.player-img.icon-play')  # element name이 q인 곳을 찾아
    search_box.click()  # 실행합니다.
    time.sleep(10)  # 음성출력 대기
    driver.close()


def play_gtts(text):  # google tts
    tts = gTTS(text=text, lang='ko')
    tts.save('temp.mp3')
    time.sleep(3)
    os.system('omxplayer temp.mp3')
    os.remove('temp.mp3')


def get_weather():  # naver 날씨 크롤링
    search = urllib.parse.quote('날씨')
    url = 'https://search.naver.com/search.naver?ie=utf8&query=' + search
    req = Request(url)
    page = urlopen(req)
    html = page.read()
    soup = BeautifulSoup(html, 'html5lib')
    result = soup.find('ul', class_='info_list').find('p', class_='cast_txt').text
    result = "오늘 날씨는 " + result.replace('˚', '도')
    return result


if __name__ == "__main__":
    try:
        while True:
            if GPIO.input(PIR_PIN) == GPIO.HIGH:
                print("detected")
                weather = get_weather()
                play_gtts(weather)
                running()

    except KeyboardInterrupt:
        print(" quit ")
        GPIO.cleanup()
