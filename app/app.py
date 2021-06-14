import os
import datetime
import requests
import xml.dom.minidom
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        xml_data = download_data(request.form["input_annotation"])
        info_dict, items = xml_separate_data(xml_data)
        xml_template(info_dict, items)
        send_data()
    return render_template("index.html")

def download_data(annotation_id):
    queue_id = annotation_id  # 108576
    username = os.environ.get("ROSSUM_USER")  # 'covave4442@flmcat.com'
    password = os.environ.get("ROSSUM_PASSWORD")  # 'rossum_test'
    endpoint = 'https://elis.rossum.ai/api/v1'

    data = {'username': username, 'password': password}

    response = requests.post(
        f'{endpoint}/auth/login',
        json={'username': username, 'password': password}
    )
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

    return response.content

def xml_separate_data(xml_data):
    info_dict = {}
    items = []
    xml_parsed = xml.dom.minidom.parseString(xml_data)
    xml_pretty = xml_parsed.toprettyxml()

    section_array = xml_parsed.getElementsByTagName("section")
    for section in section_array:
        data_dict = {}
        if section.getAttribute("schema_id"):
            if section.getAttribute("schema_id") == "line_items_section":
                items_data = section.getElementsByTagName("tuple")
                for item in items_data:
                    data_dict = {}
                    datapoints = item.getElementsByTagName("datapoint")
                    for datapoint in datapoints:
                        if datapoint.firstChild:
                            data_dict[datapoint.getAttribute("schema_id")] = datapoint.firstChild.nodeValue
                    items.append(data_dict)
            else:
                datapoints = section.getElementsByTagName("datapoint")
                for datapoint in datapoints:
                    if datapoint.firstChild:
                        data_dict[datapoint.getAttribute("schema_id")] = datapoint.firstChild.nodeValue
                info_dict[section.getAttribute("schema_id")] = data_dict
    return info_dict, items

def xml_template(info_dict, items):
    header = f'''<InvoiceRegisters>
  <Invoices>
    <Payable>
      <InvoiceNumber>{info_dict["invoice_info_section"]["document_id"]}</InvoiceNumber>
      <InvoiceDate>{info_dict["invoice_info_section"]["date_issue"]}T00:00:00</InvoiceDate>
      <DueDate>{info_dict["invoice_info_section"]["date_issue"]}T00:00:00</DueDate>
      <TotalAmount>{float(info_dict["amounts_section"]["amount_total_tax"])*1.04246925755848}</TotalAmount>
      <Notes/>
      <Iban>{info_dict["payment_info_section"]["iban"]}</Iban>
      <Amount>{info_dict["amounts_section"]["amount_total_tax"]}</Amount>
      <Currency>{(info_dict["amounts_section"]["currency"]).upper()}</Currency>
      <Vendor>{info_dict["vendor_section"]["recipient_name"]}</Vendor>
      <VendorAddress>{(info_dict["other_section"]["notes"]).replace(chr(10), " ")}</VendorAddress>
      <Details>
        '''

    body = ''
    for item in items:
        body += f'''<Detail>
          <Amount>{item["item_amount_total"]}</Amount>
          <AccountId/>
          <Quantity>{item["item_quantity"]}</Quantity>
          <Notes>{item["item_description"]}</Notes>
        </Detail>'''

    footer = f'''
    </Details>
    </Payable>
  </Invoices>
</InvoiceRegisters>'''
    final_xml = header + body + footer
    print(final_xml)
    f = open("test.xml", "w")
    f.write(final_xml)
    f.close()

def send_data():
    username = ""
    password = ""
    queue_id = 12345
    path = "test.xml"

    url = "https://my-little-endpoint.ok/rossum" % str(queue_id)
    with open(path, "rb") as f:
        response = requests.post(
            url,
            files={"content": f},
            auth=(username, password),
        )
    annotation_url = response.json()["results"][0]["annotation"]
    if not response.ok:
        print("cant send")
    print("file send")
    print("The file is reachable at the following URL:", annotation_url)


if __name__ == '__main__':
    app.run()
