from flask import Flask, render_template, send_from_directory, url_for
import pymongo
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