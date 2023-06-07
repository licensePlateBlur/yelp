from flask import Flask, render_template, send_from_directory, url_for, request,send_from_directory,make_response,jsonify,g
import pymongo
import pandas as pd
import json
import plotly
import plotly.express as px
from urllib import parse
import urllib.parse
import os
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

    business = collection_business.find_one(query)

    if business:
        business_id = business['business_id']

        collection_photo = db_conn.get_collection("yelp_photo")
        query_photo = {'business_id': business_id}

        photo = collection_photo.find_one(query_photo)

        if photo:
            photo_id = photo['photo_id']
            # print("photo_id below")
            # print(photo_id)

            return render_template('business.html', image_filename=url_for('display_image', filename=photo_id + '.jpg'))

    return 'Business not found or image not available.'




@app.route("/user")
def search_useful_review():

    collection_review = db_conn.get_collection("yelp_review")
    query = {'useful':{'$gte':500}}

    reviews = collection_review.find(query).sort('useful',-1)

    update_result=[]
    for review in reviews:
        business_id = review['business_id']

        collection_business = db_conn.get_collection("yelp_business")
        query_business = {'business_id': business_id}

        business = collection_business.find(query_business)
        for i in business:
            update_result.append(i)
    return render_template('user.html',data=list(update_result))

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
        #pipelines.append({'$lookup': {'from': "yelp_photo", 'localField': "business_id", 'foreignField': "business_id", 'as': "photos"}})
        pipelines.append({'$sort':{'count': -1}})
        pipelines.append({'$project': {'_id': 0, 'business_id': "$business.business_id", 'business_name' : "$business.name", 'count':1 ,'business_stars' : "$business.stars"
                                       ,'business_city' : "$business.city",'business_address' : "$business.address", 'real_average_stars': "$business.real_stars", 'photo_id': {'$arrayElemAt': ['$photos.photo_id', 0]}}})
        pipelines.append({'$limit':100})
        results = collection_review.aggregate(pipelines)

        collection_photo = db_conn.get_collection("yelp_photo")
        updated_results = []

        for result in results:
            business_id = result['business_id']
            query_photo = {'business_id': business_id}
            photo = collection_photo.find_one(query_photo)

            if photo: 
                result['photo_id'] = photo['photo_id']
            
            updated_results.append(result)
        
        return render_template('business.html',data=updated_results)
    
    return "에러입니다."

@app.route('/goodplace', methods=['GET', 'POST'])
def goodplace():
    #평점을 높게준 사람이 (평균 평점 4점 이상) 낮게 평가한(2점 이하) (좋은 장소 추출)
    collection_review = db_conn.get_collection("yelp_review")
    pipelines = list()
    pipelines.append({'$match':{'date':{'$gte': "2018-07-07 22:09:11"}}})
    pipelines.append({'$lookup':{'from':"yelp_user",'localField':"user_id", 'foreignField':"user_id", 'as':"user"}})
    pipelines.append({'$lookup':{'from':"yelp_business",'localField':"business_id", 'foreignField':"business_id", 'as':"business"}})
    pipelines.append({'$lookup': {'from': "yelp_review", 'localField': "business_id", 'foreignField': "business_id", 'as': "reviews"}})
    #pipelines.append({'$lookup': {'from': "yelp_photo", 'localField': "business_id", 'foreignField': "business_id", 'as': "photos"}})
    pipelines.append({'$match':{"user.average_stars":{'$lte':2}, 'stars':{'$gt':4}}})
    pipelines.append({'$sort':{'stars': -1}})
    pipelines.append({'$project': {'_id': 0, 'business_id': "$business.business_id", 'business_name' : "$business.name", 'count':1 ,'business_stars' : {'$arrayElemAt': ['$business.stars', 0]}
                                       ,'business_city' : "$business.city",'business_address' : "$business.address", 'real_average_stars': {'$arrayElemAt': ['$business.real_stars', 0]}, 'text': "$reviews.text", 'photo_id': {'$arrayElemAt': ['$photos.photo_id', 0]}}})
    pipelines.append({'$limit':5})
    good = collection_review.aggregate(pipelines)


    collection_photo = db_conn.get_collection("yelp_photo")
    
    updated_results_good = []

    for result in good:
        business_id = result['business_id'][0]
        business_id = str(business_id)
        print("good")
        query_photo = {'business_id': business_id}
        print(query_photo)
        photo = collection_photo.find_one(query_photo)

        if photo: 
            result['photo_id'] = photo['photo_id']
            
            
        updated_results_good.append(result)

    return render_template('goodplace.html',good=updated_results_good)
@app.route('/badplace', methods=['GET', 'POST'])
def badplace():
    #평점을 낮게준 사람이 (평균 평점 2점 이하) 높게 평가한(4점 이상) (좋은 장소 추출)
    collection_review = db_conn.get_collection("yelp_review")
    pipelines = list()
    pipelines.append({'$lookup':{'from':"yelp_user",'localField':"user_id", 'foreignField':"user_id", 'as':"user"}})
    pipelines.append({'$lookup':{'from':"yelp_business",'localField':"business_id", 'foreignField':"business_id", 'as':"business"}})
    pipelines.append({'$lookup': {'from': "yelp_review", 'localField': "business_id", 'foreignField': "business_id", 'as': "reviews"}})
    #pipelines.append({'$lookup': {'from': "yelp_photo", 'localField': "business_id", 'foreignField': "business_id", 'as': "photos"}})
    pipelines.append({'$match':{"user.average_stars":{'$gte':4}, 'stars':{'$lte':2}}})
    pipelines.append({'$sort':{'stars': 1}})
    pipelines.append({'$project': {'_id': 0, 'business_id': "$business.business_id", 'business_name' : "$business.name", 'count':1 ,'business_stars' : {'$arrayElemAt': ['$business.stars', 0]}
                                       ,'business_city' : "$business.city",'business_address' : "$business.address", 'real_average_stars': {'$arrayElemAt': ['$business.real_stars', 0]}, 'text': "$reviews.text", 'photo_id': {'$arrayElemAt': ['$photos.photo_id', 0]}}})
    pipelines.append({'$limit':5})
    bad = collection_review.aggregate(pipelines)

    collection_photo = db_conn.get_collection("yelp_photo")
    updated_results_bad = []

    for result in bad:
        business_id = result['business_id'][0]
        business_id = str(business_id)
        print("bad")
        query_photo = {'business_id': business_id}
        print(query_photo)
        photo = collection_photo.find_one(query_photo)

        if photo: 
            result['photo_id'] = photo['photo_id']
            
        updated_results_bad.append(result)

    return render_template('badplace.html',bad=updated_results_bad)

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


@app.route('/photos/<photo_id>.jpg')
def serve_photo(photo_id):
    photo_path = os.path.join("C:/Users/yjson/Downloads/yelpPhoto/photos", f"{photo_id}.jpg")
    # 사진 경로를 각 컴퓨터의 로컬 환경에 맞게 변경해주세용
    if os.path.isfile(photo_path):
        directory = os.path.dirname(photo_path)
        filename = os.path.basename(photo_path)
        return send_from_directory(directory, filename)
    else:
        return "Photo not found"
