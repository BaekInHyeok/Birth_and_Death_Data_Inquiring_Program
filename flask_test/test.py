from flask import Flask, render_template, request
from pymongo import MongoClient
import plotly.graph_objs as go
from datetime import datetime

# db 접속
app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['term_pj']
collection = db['birth']


@app.route('/')
def index():
    # 조회 기간 드롭다운 옵션 생성
    options = get_date_options()
    return render_template('index.html', options=options)


@app.route('/graph', methods=['POST'])
def graph():
    # 선택한 조회 기간 받아오기
    date_range = request.form.get('date_range')

    # 선택한 조회 기간에 해당하는 데이터 가져오기
    start_date = datetime.strptime(f"{date_range}.01", "%Y.%m")
    end_date = datetime.strptime(f"{date_range}.12", "%Y.%m")

    query = {
        "조회기간": {
            "$gte": start_date.strftime("%Y.%m"),
            "$lte": end_date.strftime("%Y.%m")
        }
    }

    data = list(collection.find(query))

    # 남자와 여자의 건수 비교 그래프 생성
    gender_graph = create_gender_comparison_graph(data)

    # 시도 별 건수 그래프 생성
    district_graph = create_district_graph(data)

    return render_template('graph.html', gender_graph=gender_graph, district_graph=district_graph)


def get_date_options():
    # 조회 기간 드롭다운 옵션 생성
    options = []
    years = range(2008, 2023)

    for year in years:
        option = str(year)
        options.append(option)

    return options


def create_gender_comparison_graph(data):
    # 남자와 여자의 건수 비교 그래프 생성

    year_counts = {}

    for item in data:
        gender = item['성별']
        count = int(item['건수'])
        year = int(item['조회기간'].split('.')[0])

        if year in year_counts:
            if gender == '남자':
                year_counts[year]['남자'] += count
            elif gender == '여자':
                year_counts[year]['여자'] += count
        else:
            year_counts[year] = {'남자': 0, '여자': 0}
            if gender == '남자':
                year_counts[year]['남자'] = count
            elif gender == '여자':
                year_counts[year]['여자'] = count

    x = list(year_counts.keys())
    male_counts = [year_counts[year]['남자'] for year in x]
    female_counts = [year_counts[year]['여자'] for year in x]

    male_trace = go.Bar(x=x, y=male_counts, name='남자')
    female_trace = go.Bar(x=x, y=female_counts, name='여자')

    data = [male_trace, female_trace]
    layout = go.Layout(title='남녀 출생 비율', xaxis_title='조회 기간', yaxis_title='건수', width=500, height=400)
    fig = go.Figure(data=data, layout=layout)

    return fig.to_html(full_html=False)


def create_district_graph(data):
    # 시도 별 건수 그래프 생성
    district_counts = {}

    for item in data:
        district = item['시도']
        count = int(item['건수']) if '건수' in item else 0

        if district in district_counts:
            district_counts[district] += count
        else:
            district_counts[district] = count

    x = list(district_counts.keys())
    y = list(district_counts.values())

    trace = go.Bar(x=x, y=y)

    data = [trace]
    layout = go.Layout(title='시도 별 건수', xaxis_title='시도', yaxis_title='건수')
    fig = go.Figure(data=data, layout=layout)

    return fig.to_html(full_html=False)


if __name__ == '__main__':
    app.run()
