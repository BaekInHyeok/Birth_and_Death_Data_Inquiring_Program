########여기 파일 신경안써도 됨##########

import pymongo
from urllib import parse

host="localhost"
port="27017"
user="user1"
pwd="user1"
db="TeamProject"

client = pymongo.MongoClient("mongodb://{}:".format(user)
                                + parse.quote(pwd)
                                + "@{}:{}/{}".format(host, port, db))

db_conn = client.get_database(db)

def region_search_max_year2(region, keyword, case):
    collection_name = "Birth" if case in [1, 2, 3] else "Death"
    collection = db_conn.get_collection(collection_name)  #컬렉션이름

    pipeline = [
        {
            "$match": {
                "시도": region,
                "읍면": { "$regex": keyword }
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

def region_sort_max_year2(region, keyword, case):
    collection_name = "Birth" if case in [1, 2, 3] else "Death"
    collection = db_conn.get_collection(collection_name)  #컬렉션이름

    max_year = region_search_max_year2(region, keyword, case)       #최고년도 가져오기

    pipeline = [
        {
            "$match": {
                "시도": region,
                "조회기간": { "$regex": max_year },
                "읍면": { "$regex": keyword }
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

    return list

#하락순 정렬 쿼리
def sort_birth_list(region, keyword):
    collection = db_conn.get_collection("Birth")  #컬렉션이름
    if keyword is not None:
        pipeline=[
                {
                    '$match':{
                        "시도": region,
                        "시군구":{
                            "$regex": keyword
                        },
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
                    '$sort': {'건수': 1}
                },
                {
                    '$limit': 10
                }
        ]

    else:
        pipeline=[
                {
                    '$match':{
                        "시도": region,
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
                    '$sort': {'건수': 1}
                },
                {
                    '$limit': 10
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
    for d in list:
        print(d)
        
sort_birth_list('충청북도',None)