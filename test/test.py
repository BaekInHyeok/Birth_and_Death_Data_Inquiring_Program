import pymongo
from urllib import parse
import math
import random
from datetime import datetime
import plotly.graph_objects as go

def main():
    host = "localhost"
    port = "27017"
    user = "user2"
    pwd = "admin"
    db = "bigdata_ch1"

    client = pymongo.MongoClient("mongodb://{}:".format(user)
                                  + parse.quote(pwd)
                                  + "@{}:{}/{}".format(host, port, db))

    db_conn = client.get_database(db)
    collection = db_conn.get_collection("birth_data")  #컬렉션이름

    #query = {"조회기간": {"$regex": "2013.01"}}
    #projection = {"_id": 0}  # _id 필드를 제외하기 위한 프로젝션 설정
    #results = collection.find(query, projection)

    pipeline = [
        {
            "$match": {
                "시도": "전라북도",
                "조회기간": {
                    "$regex": "20(0[8-9]|1[0-9]|2[0-2])"
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "년도": { "$substr": ["$조회기간", 0, 4] },
                    "성별": "$성별"
                },
                "건수": { "$sum": { "$toInt": "$건수" } }
            }
        },
        {
            "$project": {
                "_id": 0,
                "년도": "$_id.년도",
                "성별": "$_id.성별",
                "건수": 1
            }
        },
        {
            "$sort": { "년도": 1, "성별": 1 }
        }
    ]

    results = collection.aggregate(pipeline)
    
    for data in results:
        print(data)

def conn(case, region, keyword):
    host = "localhost"
    port = "27017"
    user = "user2"
    pwd = "admin"
    db = "bigdata_ch1"

    client = pymongo.MongoClient("mongodb://{}:".format(user)
                                  + parse.quote(pwd)
                                  + "@{}:{}/{}".format(host, port, db))

    db_conn = client.get_database(db)
    collection = db_conn.get_collection("birth_data")  #컬렉션이름

    #query = {"조회기간": {"$regex": "2013.01"}} #/test용 코드
    #projection = {"_id": 0}  # _id 필드를 제외하기 위한 프로젝션 설정
    #results = collection.find(query, projection)


    if case == 3:
        pipeline = [
            {
                '$match': {
                    '시도': region,
                    '읍면': {'$ne': '재외국민 가족관계등록사무소'}
                }
            },
            {
                '$group': {
                    '_id': {
                        '년도': {'$substr': ['$조회기간', 0, 4]},
                        '월': {'$substr': ['$조회기간', 5, 2]},
                        '읍면': '$읍면'
                    },
                    '건수': {'$sum': {'$toInt': '$건수'}}
                }
            },
            {
                '$sort': {'건수': -1}
            },
            {
                '$limit': 10
            }
        ]

    results = collection.aggregate(pipeline)

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
    
    for d in list:
        print(d)

    #return results

def test():
    results = list(conn(2, "전라남도"))
    for d in results:
        print(d)
    남자_data = [d['건수'] for d in results if d['성별'] == '남자']
    여자_data = [d['건수'] for d in results if d['성별'] == '여자']
    년도_labels = sorted(set([d['년도'] for d in results]))

    fig = go.Figure()
    fig.add_trace(go.Bar(x=년도_labels, y=남자_data, name='남자'))
    fig.add_trace(go.Bar(x=년도_labels, y=여자_data, name='여자'))

    fig.update_layout(
        title='년도별 남녀 출생 데이터',
        xaxis_title='년도',
        yaxis_title='건수',
        barmode='group'
    )

    fig.show()

def region_search_max_year(region):
    host = "localhost"
    port = "27017"
    user = "user2"
    pwd = "admin"
    db = "bigdata_ch1"

    client = pymongo.MongoClient("mongodb://{}:".format(user)
                                  + parse.quote(pwd)
                                  + "@{}:{}/{}".format(host, port, db))

    db_conn = client.get_database(db)
    collection = db_conn.get_collection("birth_data")  #컬렉션이름

    pipeline = [
        {
            "$match": {
                "시도": region,
                "조회기간": { "$regex": "20(0[8-9]|1[0-9]|2[0-2])" }
            }
        },
        {
            "$group": {
                "_id": {
                    "년도": { "$substr": ["$조회기간", 0, 4] }
                },
                "건수": { "$sum": { "$toInt": "$건수" } }
            }
        },
        {
            "$sort": { "건수": -1 }
        },
        {
            "$limit": 1
        }
    ]

    results = list(collection.aggregate(pipeline))
    max_year = results[0]["_id"]["년도"]
    return max_year

def region_sort_max_year(region):
    host = "localhost"
    port = "27017"
    user = "user2"
    pwd = "admin"
    db = "bigdata_ch1"

    client = pymongo.MongoClient("mongodb://{}:".format(user)
                                  + parse.quote(pwd)
                                  + "@{}:{}/{}".format(host, port, db))

    db_conn = client.get_database(db)
    collection = db_conn.get_collection("birth_data")  #컬렉션이름

    max_year = region_search_max_year(region)

    pipeline = [
        {
            "$match": {
                "시도": region,
                "조회기간": { "$regex": max_year }
            }
        },
        {
            "$group": {
                "_id": {
                    "년도": "$조회기간" ,
                    "읍면" :  "$읍면" 
                },
                "건수": { "$sum": { "$toInt": "$건수" } }
            }
        },
        {
            "$sort": { "건수": -1 }
        },
        {
            "$limit": 6
        }
    ]

    results = collection.aggregate(pipeline)
    list = []
    for d in results:
        date = (d["_id"]["년도"])
        township = (d["_id"]["읍면"])
        total = d["건수"]
        temp = {
            "date" : date,
            "region" : township,
            "total" : total
        }
        list.append(temp)

    total_values = [item['total'] for item in list]
    region_dates = [f"{item['region']} - {item['date']}" for item in list]
    
    total_sum = sum(total_values)
    percentages = [(value / total_sum) * 100 for value in total_values]

    fig = go.Figure(data=[go.Pie(labels=region_dates, values=percentages)])
    fig.update_layout(title= max_year + "년도 " + region + "지역 상위 6개 데이터")
    
    fig.show()
    #pio.write_html(fig, file='region_graph.html', auto_open=True)

region_sort_max_year('서울특별시')