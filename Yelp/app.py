from flask import Flask, render_template, request
import pymongo
from urllib import parse
import pandas as pd
import json
import plotly
import plotly.express as px
app = Flask(__name__)

host = "localhost"
port = "27017"
user = "root"
pwd = "root"
db = "yelp"
client = pymongo.MongoClient("mongodb://{}:".format(user)+ parse.quote(pwd)+ "@{}:{}/{}".format(host,port,db))
db_conn = client.get_database(db)

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/business")
def business():
    return render_template('business.html')
@app.route("/user")
def user():
    collection_user = db_conn.get_collection("yelp_user")
    query = {}
    results = collection_user.find(query).sort('review_count',-1).limit(10)

    return render_template('user.html',data=results)

@app.route('/date', methods=['GET', 'POST'])
def date():
    if request.method == 'POST':
        date = request.form['date']  # 전송된 폼 데이터 받기
        collection_review = db_conn.get_collection("yelp_review")
        pipelines = list()
        # pipelines.append({'$match':{'date':{'$gte': "2018-07-07 22:09:11"}}})
        pipelines.append({'$match':{'date':{'$gte': date}}})
        pipelines.append({'$group':{'_id':'$business_id', 'count':{'$sum':1}}})
        pipelines.append({'$lookup':{'from':"yelp_business",'localField':"_id", 'foreignField':"business_id", 'as':"business"}})
        pipelines.append({'$unwind':"$business"})
        pipelines.append({'$sort':{'count': -1}})
        pipelines.append({'$project': {'_id': 0, 'business_name' : "$business.name", 'count':1 ,'business_stars' : "$business.stars"
                                       ,'business_city' : "$business.city",'business_address' : "$business.address"}})
        pipelines.append({'$limit':100})
        results = collection_review.aggregate(pipelines)
        return render_template('business.html',data=results)
    return "에러입니다."
