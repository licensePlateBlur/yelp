from flask import Flask, render_template, send_from_directory, url_for, request,send_from_directory,make_response
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
            print("photo_id below")
            print(photo_id)

            return render_template('business.html', image_filename=url_for('display_image', filename=photo_id + '.jpg'))

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
        pipelines.append({'$project': {'_id': 0, 'business_id': "$business.business_id", 'business_name' : "$business.name", 'count':1 ,'business_stars' : "$business.stars"
                                       ,'business_city' : "$business.city",'business_address' : "$business.address", 'real_average_stars': "$business.real_stars"}})
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
        
        for result in updated_results:
            print(result)
        return render_template('business.html',data=updated_results)
    
    return "에러입니다."


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
