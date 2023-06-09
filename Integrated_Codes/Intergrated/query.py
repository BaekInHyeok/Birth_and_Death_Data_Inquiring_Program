import pymongo
from urllib import parse

host = "localhost"
port = "27017"
user = "user2"
pwd = "admin"
db = "bigdata_ch1"

client = pymongo.MongoClient("mongodb://{}:".format(user)
                                + parse.quote(pwd)
                                + "@{}:{}/{}".format(host, port, db))

db_conn = client.get_database(db)

def return_query(case, region, keyword):
    if case==1:
        pipeline=[
            {
                "$match":{
                    "시도":region
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
    collection = db_conn.get_collection("birth_data")  #컬렉션이름

    pipeline = [
        {
            "$match": {
                "시도": region
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
    collection = db_conn.get_collection("birth_data")  #컬렉션이름

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

def GenderComparision(start_date,end_date):
    pipeline=[
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
    
    return pipeline

def regionQuery():
    pipeline=[
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
    
    return pipeline

def Top3Query():
    pipeline=[
        {
            "$group":{
                "_id": {
                    "월": { "$substr": ["$조회기간", 5, 2] }
                },
                "발생건수": { "$sum": { "$toInt": "$건수" } }
            }
        },
        {
            "$sort": {
                "발생건수": -1
            }
        },
        {
            "$limit": 3
        }
    ]
    
    return pipeline

def ManWomanTop5():
    pipeline=[
        {"$group": {
            "_id": {"시도": "$시도", "시군구": "$시군구", "성별": "$성별"},
            "건수": {"$sum": {"$toInt": "$건수"}}
        }},
        {"$group": {
            "_id": {"시도": "$_id.시도", "시군구": "$_id.시군구"},
            "남자": {"$sum": {"$cond": [{"$eq": ["$_id.성별", "남자"]}, "$건수", 0]}},
            "여자": {"$sum": {"$cond": [{"$eq": ["$_id.성별", "여자"]}, "$건수", 0]}}
        }},
        {"$project": {
            "_id": 0,
            "지역": {"$concat": ["$_id.시군구", ", ", "$_id.시도"]},
            "차이비율": {
                "$cond": {
                    "if": {"$eq": ["$남자", 0]},
                    "then": 0,
                    "else": {"$abs": {"$divide": [{"$subtract": ["$남자", "$여자"]}, "$남자"]}}
                }
            }
        }},
        {"$sort": {"차이비율": -1}},
        {"$limit": 5}
    ]
    
    return pipeline

def MainPageQuery():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "연도": { "$substr": ["$조회기간", 0, 4] }
                },
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

def sort_droprate():    #하락률 정렬쿼리
    collection = db_conn.get_collection("birth_data")  #컬렉션이름

    pipeline_2008 = [
        {
            "$match": {
                "조회기간": { "$regex": "^2008" }
            }
        },
        {
            "$group": {
                "_id": {
                    '시도': '$시도'
                },
                "건수": { "$sum": { "$toInt": "$건수" } }
            }
        }
    ]   

    pipeline_2022 = [
        {
            "$match": {
                "조회기간": { "$regex": "^2022" }
            }
        },
        {
            "$group": {
                "_id": {
                    '시도': '$시도'
                },
                "건수": { "$sum": { "$toInt": "$건수" } }
            }
        }
    ]   

    results_2008 = collection.aggregate(pipeline_2008)
    results_2022 = collection.aggregate(pipeline_2022)

    list_2008 = []
    for d in results_2008:
        region = (d["_id"]["시도"])
        total = d["건수"]
        temp = {
            "region" : region,
            "total" : total
        }
        list_2008.append(temp)

    list_2022 = []
    for d in results_2022:
        region = (d["_id"]["시도"])
        total = d["건수"]
        temp = {
            "region" : region,
            "total" : total
        }
        list_2022.append(temp)

    results = []
    for i in range(len(list_2008)):
        region = list_2008[i]['region']
        total_2008 = list_2008[i]['total']
        
        for j in range(len(list_2022)):
            if list_2022[j]['region'] == region:
                total_2022 = list_2022[j]['total']
                rate = ((total_2008 - total_2022) / total_2008) * 100
                temp = {
                    "region" : region,
                    "rate" : rate
                }
                results.append(temp)
                break

    sorted_results = sorted(results, key=lambda x: x["rate"]) #내림차순정렬

    return sorted_results

#망한코드
