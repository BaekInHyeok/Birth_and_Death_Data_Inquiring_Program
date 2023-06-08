from flask import Flask, render_template, request
from urllib import parse
import pymongo
import plotly.graph_objs as go

app = Flask(__name__)

# db 접속
host = "localhost"
port = "27017"
user = "user1"
pwd = "user1"
db = "term_pj"

client = pymongo.MongoClient("mongodb://{}:".format(user)
                             + parse.quote(pwd)
                             + "@{}:{}/{}".format(host, port, db))

db_conn = client.get_database(db)
birth_collection = db_conn.get_collection("birth")
death_collection = db_conn.get_collection("death")


@app.route('/')
def index():
    # 조회 기간 드롭다운 옵션 생성
    options = get_date_options()
    return render_template('index.html', options=options)


@app.route('/graph', methods=['POST'])
def graph():
    # 선택한 조회 기간과 데이터 유형(birth/death) 받아오기
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    data_type = request.form.get('data_type')

    if data_type == 'birth':
        collection = birth_collection
        graph_title = '출생 데이터'
    elif data_type == 'death':
        collection = death_collection
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
    district_graph = create_district_graph(data, collection)

    return render_template('graph.html', gender_graph=gender_graph, district_graph=district_graph, title=graph_title)


def get_date_options():
    # 조회 기간 드롭다운 옵션 생성
    options = []
    years = range(2008, 2023)

    for year in years:
        for month in range(1, 13):
            option = f"{year}.{month:02d}"
            options.append(option)

    return options


def create_gender_comparison_graph(data, data_type, start_date, end_date, collection):
    # 남자와 여자의 건수 비교 그래프 생성
    male_counts = {}
    female_counts = {}

    pipeline = [
        {
            '$match': {
                "조회기간": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            '$group': {
                '_id': {
                    'gender': '$성별',
                    'date': '$조회기간'
                },
                'count': {'$sum': {'$toInt': '$건수'}}
            }
        },
        {
            '$group': {
                '_id': '$_id.date',
                'male_counts': {
                    '$sum': {
                        '$cond': [{'$eq': ['$_id.gender', '남자']}, '$count', 0]
                    }
                },
                'female_counts': {
                    '$sum': {
                        '$cond': [{'$eq': ['$_id.gender', '여자']}, '$count', 0]
                    }
                }
            }
        }
    ]

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
    layout = go.Layout(title=title, xaxis_title='조회 기간', yaxis_title='건수', width=800, height=500)
    fig = go.Figure(data=data, layout=layout)

    return fig.to_html(full_html=False)


def create_district_graph(data, collection):
    # 시도 별 건수 그래프 생성
    district_counts = {}

    pipeline = [
        {
            '$group': {
                '_id': '$시도',
                'count': {'$sum': {'$toInt': '$건수'}}
            }
        },
        {
            '$project': {
                '_id': 0,
                'district': '$_id',
                'count': 1
            }
        }
    ]

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


if __name__ == '__main__':
    app.run()
