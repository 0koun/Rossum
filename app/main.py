import os
import datetime
import requests
from flask import Flask, render_template, request
from xml.etree import ElementTree

#user = os.environ.get("ROSSUM_USER")
#password = os.environ.get("ROSSUM_PASSWORD")


app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        #print(request.form["input_annotation"])
        xml_data = download_data(request.form["input_annotation"])
        #print(xml_data)
        xml_restructure(xml_data)
    return render_template("index.html")

def download_data(annotation_id):
    queue_id = annotation_id  # 108576
    username = os.environ.get("ROSSUM_USER")  # 'covave4442@flmcat.com'
    password = os.environ.get("ROSSUM_PASSWORD")  # 'rossum_test'
    endpoint = 'https://elis.rossum.ai/api/v1'
    #endpoint = 'https://api.elis.rossum.ai/v1'

    data = {'username': username, 'password': password}

    response = requests.post(
        f'{endpoint}/auth/login',
        json={'username': username, 'password': password}
    )
    #print(response.headers)
    #print(response.url)
    if not response.ok:
        print("Fail")
        raise ValueError(f'Failed to authorize: {response.status_code}')
    print("OK")
    auth_token = response.json()["key"]

    date_today = datetime.date.today()
    date_end = date_today
    date_start = date_today - datetime.timedelta(days=10)
    response = requests.get(
        f'https://elis.rossum.ai/api/v1/queues/{queue_id}/export?format=xml&',
        headers={'Authorization': f'Token {auth_token}'}
    )

    if not response.ok:
        raise ValueError(f'Failed to export: {response.status_code}')

    #print(response.content)
    return response.content

def xml_restructure(xml_data):
    dom = ElementTree.fromstring(xml_data)
    file_tree = ElementTree.ElementTree(dom)
    file_tree.write("test_xml2.xml", encoding="utf-8")
    '''results = dom.findall("results")
    for r in results:
        for i in r:
            doc = i.find("document")
            for d in doc:
                print(d)'''


if __name__ == '__main__':
    app.run()
