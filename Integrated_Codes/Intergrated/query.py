import pymongo
from urllib import parse

def return_query(case, region, keyword):
    
    if case==1:
        pipeline=[
            {
                "$match":{
                    "시도":region,
                    "조회기간":{
                        "$regex":"20(0[8-9]|1[0-9]|2[0-2])"
                    }
                }
            },
            {
                "$group":{
                    "_id": {
                        "년도": { "$substr": ["$조회기간", 0, 4] },
                        "성별": "$성별"
                    },
                    "건수": { "$sum": { "$toInt": "$건수" } }
                }
            },
            {
                "$project":{
                    "_id": 0,
                    "년도": "$_id.년도",
                    "성별": "$_id.성별",
                    "건수": 1
                }
            },
            {
                "$sort": { "년도": 1 }
            }
        ]
    elif case == 2:
        pipeline=[
            {
                "$match":{
                    "시도": region,
                    "시군구":{
                        "$regex": keyword
                    },
                    "조회기간": {
                        "$regex": "20(0[8-9]|1[0-9]|2[0-2])"
                    }
                }
            },
            {
                "$group":{
                    "_id": {
                        "년도": { "$substr": ["$조회기간", 0, 4] },
                        "성별": "$성별"
                    },
                    "건수": { "$sum": { "$toInt": "$건수" } }
                }
            },
            {
                "$project":{
                    "_id": 0,
                    "년도": "$_id.년도",
                    "성별": "$_id.성별",
                    "건수": 1
                }
            },
            {
                "$sort": { "년도": 1}
            }
        ]
    elif case==3:
        pipeline=[
            {
                '$match':{
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
    return pipeline
        

def region_search_max_year(region):
    host="localhost"
    port="27017"
    user="user1"
    pwd="user1"
    db="TeamProject"
    
    client=pymongo.MongoClient("mongodb://{}:".format(user)
                               +parse.quote(pwd)
                               +"@{}:{}/{}".format(host,port,db))
    
    db_conn=client.get_database(db)
    collection = db_conn.get_collection("Birth")  #컬렉션이름

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
    host="localhost"
    port="27017"
    user="user1"
    pwd="user1"
    db="TeamProject"

    client = pymongo.MongoClient("mongodb://{}:".format(user)
                                  + parse.quote(pwd)
                                  + "@{}:{}/{}".format(host, port, db))

    db_conn = client.get_database(db)
    collection = db_conn.get_collection("Birth")  #컬렉션이름

    max_year = region_search_max_year(region)       #최고년도 가져오기

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

    return list

def MainPageQuery():
    pipeline = [
        {
            "$group": {
                "_id": "$조회기간",
                "발생건수": {"$sum": {"$toInt": "$건수"}}
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    return pipeline