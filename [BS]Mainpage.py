from flask import Flask
from flask import render_template

import pymongo
from urllib import parse

import plotly.graph_objects as go

app = Flask(__name__)

def conn():
    host="localhost"
    port="27017"
    user="user1"
    pwd="user1"
    db="TeamProject"
    
    client=pymongo.MongoClient("mongodb://{}:".format(user)
                               +parse.quote(pwd)
                               +"@{}:{}/{}".format(host,port,db))
    
    db_conn=client.get_database(db)
    
    collection1=db_conn.get_collection("Birth")
    collection2=db_conn.get_collection("Death")

    
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

@app.route("/")
def home_page():
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
    
    css_string="""
    <style>
        /* 메뉴바 스타일 */
        .sidenav {
            height: 100%;
            width: 200px;
            position: fixed;
            z-index: 1;
            top: 0;
            left: 0;
            background-color: #111;
            overflow-x: hidden;
            padding-top: 20px;
        }

        /* 메뉴바 항목 스타일 */
        .sidenav a {
            padding: 6px 8px 6px 16px;
            text-decoration: none;
            font-size: 25px;
            color: #818181;
            display: block;
        }
        /* 메뉴바 항목 호버 스타일 */
        .sidenav a:hover {
            color: #f1f1f1;
        }

        /* 본문 스타일 */
        .main {
            margin-left: 200px; /* 메뉴바 너비만큼 여백 추가 */
        }
        
        h1{
            
            font-size : 50px;
        }
        
        h2{
            font-size : 25px;
        }
        
        h3{
            font-size: 15px;
        }
        
        h5{
            border-bottom : 1px solid black;
        }
    </style>
    """

    html_string = f"""
    <html>
        <head>
            <title>12조 Team Project</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            {css_string}
            
        </head>
        
        <body>
        <!-- 메뉴바 -->
        <div class="sidenav">
            <a href="#home">메인화면</a>
            <a href="#Date">날짜구간조회</a>
            <a href="#Area">지역별 조회</a>
        </div>

        <!-- 본문 -->
        <div class="main">
            <h1>2008 ~ 2022 전국 출생/사망자 통계 조회</h1>
            <h2>자료 출처 : 대법원 전자가족관계등록시스템</h2>
            <h3>Data 1 : 2008~2022 성별 출생 현황
            <h3>Data 2 : 2008~2022 성별 사망 현황
            <h5></h5>
            <h2>제공 기능</h2>
            <h3>2008 ~ 2022 출생/사망자 변동 추이 시각화</h3>
            <h3>날짜 구간별 출생자/사망자 조회</h3>
            <h3>지역별 출생자/사망자 조회</h3>
            <h5></h5>
            {chart}
        </div>
        </body>
    </html>
    """

    return html_string

app.run()
