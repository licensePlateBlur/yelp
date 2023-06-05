from flask import Flask, render_template, send_from_directory, url_for, request,send_from_directory,make_response,jsonify,g
import pymongo
import pandas as pd
import json
import plotly
import plotly.express as px
from urllib import parse
import urllib.parse
app = Flask(__name__)

host = "localhost"
port = "27017"
user = "root"
pwd = "root"
db = "yelp"
client = pymongo.MongoClient("mongodb://{}:".format(user)+ parse.quote(pwd)+ "@{}:{}/{}".format(host,port,db))
db_conn = client.get_database(db)


# 영재 이거 추가하면됨
@app.route('/static/css/<path:path>')
def send_css(path):
    response = make_response(send_from_directory('static/css', path))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/")
def main():
    return render_template('index.html')


@app.route('/image/<filename>')
def display_image(filename):
    print("image return requested")
    return send_from_directory('C:/Users/yjson/Downloads/yelpPhoto/photos', filename)

@app.route("/business")
def business():
    return render_template('business.html')



@app.route('/business/<name>')
def search_business(name):

    decoded_name = urllib.parse.unquote(name)
    collection_business = db_conn.get_collection("yelp_business")
    query = {'name': decoded_name}

    # Search for the business in the "yelp_business" collection
    business = collection_business.find_one(query)

    if business:
        # Get the business ID
        business_id = business['business_id']

        # Search for the corresponding image in the "yelp_photo" collection
        collection_photo = db_conn.get_collection("yelp_photo")
        query_photo = {'business_id': business_id}

        photo = collection_photo.find_one(query_photo)

        if photo:
            # Get the photo ID (image filename without extension)
            photo_id = photo['photo_id']
            print("photo_id below")
            print(photo_id)

            # Render the template and pass the image filename
            return render_template('business.html', image_filename=url_for('display_image', filename=photo_id + '.jpg'))

    # Business not found or image not found
    return 'Business not found or image not available.'




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

@app.route('/place', methods=['GET', 'POST'])
def place():
    #평점을 높게준 사람이 (평균 평점 4점 이상) 낮게 평가한(2점 이하) (좋은 장소 추출)
    collection_review = db_conn.get_collection("yelp_review")
    pipelines = list()
    pipelines.append({'$lookup':{'from':"yelp_user",'localField':"user_id", 'foreignField':"user_id", 'as':"user"}})
    pipelines.append({'$lookup':{'from':"yelp_business",'localField':"business_id", 'foreignField':"business_id", 'as':"business"}})
    pipelines.append({'$match':{"user.average_stars":{'$lte':2}, 'stars':{'$gt':4}}})
    pipelines.append({'$sort':{'stars': -1}})
    pipelines.append({'$project': {'_id': 0,'business_id':1, 'business_name': {'$arrayElemAt': ['$business.name', 0]}}})
    pipelines.append({'$limit':20})
    good = collection_review.aggregate(pipelines)

    #평점을 낮게준 사람이 (평균 평점 2점 이하) 높게 평가한(4점 이상) (좋은 장소 추출)
    collection_review = db_conn.get_collection("yelp_review")
    pipelines = list()
    pipelines.append({'$lookup':{'from':"yelp_user",'localField':"user_id", 'foreignField':"user_id", 'as':"user"}})
    pipelines.append({'$lookup':{'from':"yelp_business",'localField':"business_id", 'foreignField':"business_id", 'as':"business"}})
    pipelines.append({'$match':{"user.average_stars":{'$gte':4}, 'stars':{'$lte':2}}})
    pipelines.append({'$sort':{'stars': -1}})
    pipelines.append({'$project': {'_id': 0,'business_id':1, 'business_name': {'$arrayElemAt': ['$business.name', 0]}, 'text':1}})
    pipelines.append({'$limit':20})
    bad = collection_review.aggregate(pipelines)


    return render_template('place.html',good=good , bad=bad)

@app.route('/category', methods=['GET', 'POST'])
def showCate():
    collection_busi = db_conn.get_collection("yelp_business")
    pipelines = list()
    pipelines.append({'$unwind':"$categories"})
    pipelines.append({'$group': {'_id': "null",'uniqueCategories': {"$addToSet": "$categories"}}})
    pipelines.append({'$project':{'_id': 0, 'categories': "$uniqueCategories"}})
    pipelines.append({'$limit':100})
    global_category = collection_busi.aggregate(pipelines)

    collection_busi = db_conn.get_collection("yelp_business")
    pipelines = list()
    pipelines.append({'$group': {'_id': "null",'uniqueCities': {"$addToSet": "$city"}}})
    pipelines.append({'$project':{'_id': 0, 'city': "$uniqueCities"}})
    pipelines.append({'$limit':100})
    global_city= collection_busi.aggregate(pipelines)


    return render_template('category.html',category=global_category, city=global_city)

@app.route('/cate', methods=['GET', 'POST'])
def searchBusi1():
    collection_busi = db_conn.get_collection("yelp_business")
    pipelines = list()
    pipelines.append({'$unwind':"$categories"})
    pipelines.append({'$group': {'_id': "null",'uniqueCategories': {"$addToSet": "$categories"}}})
    pipelines.append({'$project':{'_id': 0, 'categories': "$uniqueCategories"}})
    pipelines.append({'$limit':100})
    global_category = collection_busi.aggregate(pipelines)

    collection_busi = db_conn.get_collection("yelp_business")
    pipelines = list()
    pipelines.append({'$group': {'_id': "null",'uniqueCities': {"$addToSet": "$city"}}})
    pipelines.append({'$project':{'_id': 0, 'city': "$uniqueCities"}})
    pipelines.append({'$limit':100})
    global_city= collection_busi.aggregate(pipelines)
    cate = request.form['cate']
    cy = request.form['cy'] 
    option = request.form['option']
    print(cate + cy + option)

    collection_busi = db_conn.get_collection("yelp_business")
    query = {
        "categories":cate,
        "city":cy
    }

    if(option == 'asc'):
        results = collection_busi.find(query).sort('stars',1)
        print("오름")
        return render_template('category.html',data=results,category=global_category, city=global_city) 
    elif(option == 'desc'):
        print("내림")
        results = collection_busi.find(query).sort('stars',-1)
        return render_template('category.html',data=results,category=global_category, city=global_city) 
    else:
        return "잘못입력하셨습니다."

