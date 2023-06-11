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

from query import *
import garbage

class TextForm(FlaskForm):
    content = StringField('내용', validators=[DataRequired()])
    
#Config setting
app = Flask(__name__)

###db 접속###
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


###메인화면용###    
def conn():
    
    pipeline = MainPageQuery()
    
    result1=collection1.aggregate(pipeline)
    result2=collection2.aggregate(pipeline)
    
    return result1, result2

###지역검색용###
def conn2(case, region, keyword):
    collection_name = "Birth" if case in [1, 2, 3] else "Death"
    collection = db_conn.get_collection(collection_name)

    pipeline = return_query(case, region, keyword)

    #쿼리 실행
    results = collection.aggregate(pipeline)

    #일반 케이스
    if case == 1 or case == 2:
        return results
    
    #리스트 리턴
    elif case == 3 or case == 6:
        list = []
        for d in results:
            date = (d["_id"]["년도"] +'.'+ d["_id"]["월"])
            region = (d["_id"]["읍면"])
            total = d["건수"]
            temp = {
                "date" : date,
                "region" : region,
                "total" : total
            }
            list.append(temp)
        
        return list

    elif case == 4 or 5:
        return results
    
    else :
        list = []
        for d in results:
            date = (d["_id"]["년도"] +'.'+ d["_id"]["월"])
            region = (d["_id"]["읍면"])
            total = d["건수"]
            temp = {
                "date" : date,
                "region" : region,
                "total" : total
            }
            list.append(temp)
        
        return list
    
###기타통계-월별###
def conn3():    
    pipeline = Top3Query()
    
    result1=collection1.aggregate(pipeline)
    result2=collection2.aggregate(pipeline)
    
    return result1, result2

###기타통계-남녀성비###
def conn4():
    pipeline=ManWomanTop5()
    
    result3=collection1.aggregate(pipeline)
    
    return result3

###조회 기간 드롭다운 옵션 생성###
def get_date_options():
    
    options = []
    years = range(2008, 2023)

    for year in years:
        for month in range(1, 13):
            option = f"{year}.{month:02d}"
            options.append(option)

    return options

###남자와 여자의 건수 비교 그래프 생성###
def create_gender_comparison_graph(data, data_type, start_date, end_date, collection):
    
    male_counts = {}
    female_counts = {}

    pipeline = GenderComparision(start_date,end_date)

    result = collection.aggregate(pipeline)

    male_counts = {}
    female_counts = {}

    for doc in result:
        date = doc['_id']
        male_counts[date] = doc['male_counts']
        female_counts[date] = doc['female_counts']

    dates = list(set(male_counts.keys()).union(set(female_counts.keys())))
    dates.sort()

    x = [date for date in dates]
    male_y = [male_counts[date] if date in male_counts else 0 for date in dates]
    female_y = [female_counts[date] if date in female_counts else 0 for date in dates]

    if data_type == 'birth':
        title = '남녀 출생 비율'
    elif data_type == 'death':
        title = '남녀 사망 비율'

    male_trace = go.Bar(x=x, y=male_y, name='남자')
    female_trace = go.Bar(x=x, y=female_y, name='여자')

    data = [male_trace, female_trace]
    layout = go.Layout(title=title, xaxis_title='조회 기간', yaxis_title='건수')
    fig = go.Figure(data=data, layout=layout)

    return fig.to_html(full_html=False)

###시도 별 건수 그래프 생성###
def create_district_graph(data, collection,start_date,end_date):
    
    district_counts = {}

    pipeline = regionQuery(start_date,end_date)

    result = collection.aggregate(pipeline)

    x = []
    y = []

    for doc in result:
        x.append(doc['district'])
        y.append(doc['count'])

    trace = go.Bar(x=x, y=y)

    data = [trace]
    layout = go.Layout(title='시도 별 건수', xaxis_title='시도', yaxis_title='건수')
    fig = go.Figure(data=data, layout=layout)

    return fig.to_html(full_html=False)

###날짜구간 검색 결과 그래프 페이지###
@app.route('/graph', methods=['POST'])
def graph():
    # 선택한 조회 기간과 데이터 유형(birth/death) 받아오기
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    data_type = request.form.get('data_type')

    if data_type == 'birth':
        collection = collection1
        graph_title = '출생 데이터'
    elif data_type == 'death':
        collection = collection2
        graph_title = '사망 데이터'
    else:
        return render_template('graph.html', error_message='err')

    query = {
        "조회기간": {"$gte": start_date, "$lte": end_date}
    }

    data = list(collection.find(query))

    # 남자와 여자의 건수 비교 그래프 생성
    gender_graph = create_gender_comparison_graph(data, data_type, start_date, end_date, collection)

    # 시도 별 건수 그래프 생성
    district_graph = create_district_graph(data, collection,start_date,end_date)

    return render_template('DateGraph.html', gender_graph=gender_graph, district_graph=district_graph, title=graph_title)


###날짜 구간 검색 페이지###
@app.route('/DateSearch')
def Datesearch():
   # 조회 기간 드롭다운 옵션 생성
    options = get_date_options()
    return render_template('DateSearch.html', options=options) 
    

###지역별 검색 결과 그래프 페이지###
@app.route("/region", methods=['GET'])
def region_graph():
    choice = request.args.get('birth_death')   #출생 or 사망
    region = request.args.get('region')   #지역
    keyword = request.args.get('search')  #세부지역

    #출생 데이터 선택 시
    if choice == "출생":
        #지역 검색(상세 시도군 설정X)
        if keyword is None or keyword.strip() == "":
            #각 쿼리 실행
            results = list(conn2(1, region, keyword))       #리스트 형태로 변화(안하면 에러)
            list_results = conn2(3, region, keyword)
            max_year = region_search_max_year(region, 1)
            list_results_region_sort = region_sort_max_year(region, 1)
            
            #막대그래프 그리기
            men_data = [d['건수'] for d in results if d['성별'] == '남자']
            women_data = [d['건수'] for d in results if d['성별']== '여자']
            year = sorted(set([d['년도'] for d in results]))
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=year, y=men_data, name='남자', marker_color='skyblue'))
            fig.add_trace(go.Bar(x=year, y=women_data, name='여자', marker_color='rgba(255, 192, 203, 1)'))

            fig.update_layout(
                title=region + ' ' +'년도별 남녀 출생 데이터',
                xaxis_title='년도',
                yaxis_title='건수',
                barmode='group'
            )

            graph = fig.to_html(full_html=False)

            #파이차트 그리기
            total_values = [item['total'] for item in list_results_region_sort]
            region_dates = [f"{item['region']} - {item['date']}" for item in list_results_region_sort]
            
            total_sum = sum(total_values)
            percentages = [(value / total_sum) * 100 for value in total_values]

            fig2 = go.Figure(data=[go.Pie(labels=region_dates, values=percentages)])
            fig2.update_layout(title= max_year + "년도 " + region + "지역 상위 6개 데이터")
            
            pie = fig2.to_html(full_html=False)

            return render_template('region_graph.html', graph=graph, results = list_results, pie = pie, choice = choice)
        
        #지역 상세 검색
        else :
            results = list(conn2(2, region, keyword))       #리스트 형태로 변화(안하면 에러)
            list_results = sort_list(region, keyword)
            max_year = garbage.region_search_max_year2(region, keyword, 1)
            list_results_region_sort = garbage.region_sort_max_year2(region, keyword, 1)

            men_data = [d['건수'] for d in results if d['성별'] == '남자']
            women_data = [d['건수'] for d in results if d['성별']== '여자']
            year = sorted(set([d['년도'] for d in results]))
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=year, y=men_data, name='남자', marker_color='skyblue'))
            fig.add_trace(go.Bar(x=year, y=women_data, name='여자', marker_color='rgba(255, 192, 203, 1)'))

            fig.update_layout(
                title=region + ' ' + keyword + ' ' +'년도별 남녀 출생 데이터',
                xaxis_title='년도',
                yaxis_title='건수',
                barmode='group'
            )

            #graph = fig.to_html(full_html=False, default_height=500, default_width=700)
            graph = fig.to_html(full_html=False)
            
            #파이차트 그리기
            total_values = [item['total'] for item in list_results_region_sort]
            region_dates = [f"{item['region']} - {item['date']}" for item in list_results_region_sort]
            
            total_sum = sum(total_values)
            percentages = [(value / total_sum) * 100 for value in total_values]

            fig2 = go.Figure(data=[go.Pie(labels=region_dates, values=percentages)])
            fig2.update_layout(title= max_year + "년도 " + region + " " + keyword + "지역 상위 6개 데이터")
            
            pie = fig2.to_html(full_html=False)

            return render_template('region_graph.html', graph=graph, results = list_results, pie = pie, choice = choice)
        
    #사망 데이터 선택 시
    else:
        #지역 검색(상세 시도군 설정X)
        if keyword is None or keyword.strip() == "":
            #각 쿼리 실행
            results = list(conn2(4, region, keyword))       #리스트 형태로 변화(안하면 에러)
            list_results = conn2(6, region, keyword)
            max_year = region_search_max_year(region, 4)
            list_results_region_sort = region_sort_max_year(region, 4)

            #막대그래프 그리기
            men_data = [d['건수'] for d in results if d['성별'] == '남자']
            women_data = [d['건수'] for d in results if d['성별']== '여자']
            year = sorted(set([d['년도'] for d in results]))
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=year, y=men_data, name='남자', marker_color='skyblue'))
            fig.add_trace(go.Bar(x=year, y=women_data, name='여자', marker_color='rgba(255, 192, 203, 1)'))

            fig.update_layout(
                title=region + ' ' +'년도별 남녀 사망 데이터',
                xaxis_title='년도',
                yaxis_title='건수',
                barmode='group'
            )

            graph = fig.to_html(full_html=False)

            #파이차트 그리기
            total_values = [item['total'] for item in list_results_region_sort]
            region_dates = [f"{item['region']} - {item['date']}" for item in list_results_region_sort]
            
            total_sum = sum(total_values)
            percentages = [(value / total_sum) * 100 for value in total_values]

            fig2 = go.Figure(data=[go.Pie(labels=region_dates, values=percentages)])
            fig2.update_layout(title= max_year + "년도 " + region + " " + keyword + "지역 상위 6개 데이터")
            
            pie = fig2.to_html(full_html=False)

            return render_template('region_graph.html', graph=graph, results = list_results, pie = pie, choice = choice)
        
        #지역 상세 검색(사망)
        else :
            results = list(conn2(5, region, keyword))       #리스트 형태로 변화(안하면 에러)
            list_results = sort_list(region, keyword)
            max_year = garbage.region_search_max_year2(region, keyword, 4)
            list_results_region_sort = garbage.region_sort_max_year2(region, keyword, 4)

            men_data = [d['건수'] for d in results if d['성별'] == '남자']
            women_data = [d['건수'] for d in results if d['성별']== '여자']
            year = sorted(set([d['년도'] for d in results]))
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=year, y=men_data, name='남자', marker_color='skyblue'))
            fig.add_trace(go.Bar(x=year, y=women_data, name='여자', marker_color='rgba(255, 192, 203, 1)'))

            fig.update_layout(
                title=region + ' ' + keyword + ' ' +'년도별 남녀 사망 데이터',
                xaxis_title='년도',
                yaxis_title='건수',
                barmode='group'
            )

            #graph = fig.to_html(full_html=False, default_height=500, default_width=700)
            graph = fig.to_html(full_html=False)

            #파이차트 그리기
            total_values = [item['total'] for item in list_results_region_sort]
            region_dates = [f"{item['region']} - {item['date']}" for item in list_results_region_sort]
            
            total_sum = sum(total_values)
            percentages = [(value / total_sum) * 100 for value in total_values]

            fig2 = go.Figure(data=[go.Pie(labels=region_dates, values=percentages)])
            fig2.update_layout(title= max_year + "년도 " + region + " " + keyword + "지역 상위 6개 데이터")
            
            pie = fig2.to_html(full_html=False)

            return render_template('region_graph.html', graph=graph, results = list_results, pie = pie, choice = choice)

###지역별 검색 페이지###    
@app.route('/regionSearch')
def region_search():
    return render_template('region_graph.html')

###기타 통계 페이지###
@app.route('/etc')
def etc():
    
    ###출생 및 사망 TOP3월###
    
    x_data1 = []
    y_data1 = []

    x_data2 = []
    y_data2 = []
    
    result1, result2 = conn3()
    
    # 쿼리 결과를 이용하여 데이터 추출
    for data in result1:
        x_data1.append(data['_id']['월'])
        y_data1.append(data['발생건수'])

    for data in result2:
        x_data2.append(data['_id']['월'])
        y_data2.append(data['발생건수'])
        
    # 그래프 생성
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=x_data1, y=y_data1, width=0.3, name='출생'))
    
    # 그래프 생성
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=x_data2, y=y_data2, width=0.3, name='사망'))
    
    # 그래프 레이아웃 설정
    fig1.update_layout(
        title='월별 출생 그래프',
        xaxis_title='월',
        yaxis_title='발생건수'
    )
    
    # 그래프 레이아웃 설정
    fig2.update_layout(
        title='월별 사망 그래프',
        xaxis_title='월',
        yaxis_title='발생건수'
    )
    
    ####지역 남녀 출생비율차 TOP5###
    result3=conn4()

    # 그래프 데이터 생성
    data = {
        "지역": [],
        "차이비율": []
    }
    for result in result3:
        data["지역"].append(result["지역"])
        data["차이비율"].append(result["차이비율"])
    
    #지역별 출생률 하락 차트 그리는 부분
    sorted_results = sort_droprate()        #정렬 쿼리 리스트로 가져옴
    
    regions = [data['region'] for data in sorted_results]
    rates = [data['rate'] for data in sorted_results]

    colors = []
    for rate in rates:
        if rate > 50:
            colors.append('red')
        elif rate > 40:
            colors.append('orange')
        elif rate > 30:
            colors.append('yellow')

    text = [f'{rate:.2f}%' for rate in rates] #퍼센테이지 소숫점아래 2자리표시

    fig3 = go.Figure(data=[
        go.Bar(
            x=rates,
            y=regions,
            orientation='h',
            marker=dict(color=colors),
            text=text,
            textposition='auto'
        )
    ])

    fig3.update_layout(
        title='지역별 하락률',
        xaxis=dict(title='하락률'),
        yaxis=dict(title='지역')
    )

    #차트추가
    chart1 = fig1.to_html(full_html=False)
    chart2 = fig2.to_html(full_html=False)
    chart3 = fig3.to_html(full_html=False)

    return render_template('etc.html', chart1=chart1, chart2=chart2, chart3 = chart3, data=data)

###메인페이지###
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
        x_data1.append(data['_id']['연도'])
        y_data1.append(data['발생건수'])

    for data in result2:
        x_data2.append(data['_id']['연도'])
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
    
    return render_template('Main.html', chart=chart)

app.run()