from flask import Flask, render_template, redirect, request
from datetime import datetime
import pymysql

app = Flask(__name__)
db = pymysql.connect("localhost", "root", "1234", "umbrella")
cur = db.cursor()


@app.route('/')
def index_page():
    cur.execute("SELECT * FROM memo;")
    result = cur.fetchall()
    memo = []
    for rs in result:
        m_repeat = ""
        m_option = ""

        # convert repeat option
        if (rs[5] == 0):
            m_repeat = "한 번"
        elif (rs[5] == 1):
            m_repeat = "매 번"
        else:
            m_repeat = "한 번"

        # convert output option
        if (rs[6] == 0):
            m_option = "기본 음성"
        elif (rs[6] == 1):
            m_option = "찬구"
        else:
            m_option = "기본 음성"
        memo.append([rs[1], rs[2], rs[3], m_repeat, m_option, rs[0]])
    return render_template('index.html', memos=memo)


@app.route('/addMemo')
def add_memo():
    return render_template('addMemo.html')

@app.route('/insert', methods=['POST'])
def insert_memo():
    m_title = str(request.form.get('title'))
    m_body = str(request.form.get('content'))
    m_time = str(request.form.get('time'))
    m_repeat = str(request.form.get('repeat'))
    m_output = str(request.form.get('output'))

    # convert date
    if m_time == "":
        m_time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    else:
        m_time = datetime.today().strftime("%Y-%m-%d") + " " + m_time + ":00"

    # convert option
    if m_output == "기본":
        m_output = "0"
    elif m_output == "찬구":
        m_output = "1"
    else:
        m_output = "0"


    cur.execute("insert into memo(memo_title, memo_content, memo_reservation, memo_repeat, memo_option) value(%s,%s,%s,%s,%s);",(m_title, m_body, m_time, m_repeat, m_output))
    db.commit()
    return redirect('/')


@app.route('/delete', methods=['POST'])
def delete_memo():
    memo = str(request.form.get('no'))
    cur.execute("DELETE FROM memo WHERE memo_no = %s;", (memo))
    db.commit()
    return redirect('/')


if __name__ == '__main__':
    app.run(host="0.0.0.0")
