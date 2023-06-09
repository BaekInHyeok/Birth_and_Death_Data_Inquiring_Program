from flask import Flask, render_template
from urllib import parse
import pymongo

app = Flask(__name__)

# MongoDB 연결 설정
host = "localhost"
port = "27017"
user = "user1"
pwd = "user1"
db = "term_pj"

client = pymongo.MongoClient("mongodb://{}:".format(user)
                             + parse.quote(pwd)
                             + "@{}:{}/{}".format(host, port, db))

db_conn = client.get_database(db)
collection = db_conn.get_collection("birth")

@app.route('/')
def index():
    query = [
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
    results = list(collection.aggregate(query))

    # 그래프 데이터 생성
    data = {
        "지역": [],
        "차이비율": []
    }
    for result in results:
        data["지역"].append(result["지역"])
        data["차이비율"].append(result["차이비율"])

    # 웹 페이지에 데이터 전달
    return render_template('index2.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
