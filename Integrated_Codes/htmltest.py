#Call Lib
from flask import Flask
from flask import render_template
from flask import request

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

from bson import ObjectId 
from datetime import datetime

import pymongo
from urllib import parse

import plotly.graph_objects as go

class TextForm(FlaskForm):
    content = StringField('내용', validators=[DataRequired()])

#Config setting
app = Flask(__name__)

def conn():
    host = "localhost"
    port = "27017"
    user = "user2"
    pwd = "admin"
    db = "bigdata_ch1"

    client = pymongo.MongoClient("mongodb://{}:".format(user)
                                  + parse.quote(pwd)
                                  + "@{}:{}/{}".format(host, port, db))

    db_conn = client.get_database(db)
    collection1=db_conn.get_collection("Birth")
    collection2=db_conn.get_collection("Death")  #컬렉션이름

    #query = {"조회기간": {"$regex": "2013.01"}} #/test용 코드
    #projection = {"_id": 0}  # _id 필드를 제외하기 위한 프로젝션 설정
    #results = collection.find(query, projection)

    pipeline = [
        {
            "$group": {
                "_id": "$조회기간",
                "발생건수": { "$sum": { "$toInt": "$건수" } }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    result1=collection1.aggregate(pipeline)
    result2=collection2.aggregate(pipeline)


    return result1, result2

@app.route('/test2')
def index():
    # 데이터 초기화
    x_data1 = []
    y_data1 = []

    x_data2 = []
    y_data2 = []

    result1, result2 = conn()
    
     # 쿼리 결과를 이용하여 데이터 추출
    for data in result1:
        x_data1.append(data['_id'])
        y_data1.append(data['발생건수'])
    
    for data in result2:
        x_data2.append(data['_id'])
        y_data2.append(data['발생건수'])

    # 그래프 생성
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_data1, y=y_data1, mode='lines', name='출생'))
    fig.add_trace(go.Scatter(x=x_data2, y=y_data2, mode='lines', name='사망'))


    # 그래프 레이아웃 설정
    fig.update_layout(
        title='발생건수 그래프',
        xaxis_title='조회기간',
        yaxis_title='발생건수'
    )

    # 그래프를 HTML로 렌더링하여 반환
    chart = fig.to_html(full_html=False)

    return render_template('test.html', chart=chart)

@app.route('/test')
def render_test():
    data = {
        '조회기간': '2013.01',
        '시도': '서울특별시',
        '시군구': '서울특별시 도봉구',
        '읍면': '서울특별시 도봉구청',
        '성별': '여자',
        '건수': '119'
    }

    x = list(data.keys())
    y = list(data.values())

    fig = go.Figure(data=[go.Bar(x=x, y=y)])

    plot_div = fig.to_html(full_html=False)

    return render_template('b.html', plot_div=plot_div)

@app.route("/")
def home_page():
    #data = conn()
    return render_template('index.html')
    
if __name__ == "__main__":
    app.run()