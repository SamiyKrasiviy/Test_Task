from flask import Flask, render_template, url_for , request, redirect, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashlib import sha256
import requests
import json

shop_id = "5"
secretKey = "SecretKey01"
payway = "advcash_rub"


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
db = SQLAlchemy(app)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    currency = db.Column(db.String(100), nullable =False)
    amount = db.Column(db.String(100), nullable =False)
    date = db.Column(db.DateTime, default = datetime.utcnow)
    description = db.Column(db.Text, nullable =False)


    def __repr__(self):
        return '<Payment %r>' % self.id


@app.route('/', methods = ["POST", "GET"])
def index():
    if request.method == "POST":
        currency = request.form["currency"]
        amount = request.form["amount"]
        description = request.form["description"]

        if currency != "" and amount != "" and description != "":
            if currency == "EUR":
                currency = "978"
                return pay(currency, amount, description)
            elif currency == "RUB":
                currency = "643"
                return invoice(currency, amount, description)
            elif currency == "USD":
                currency = "840"
                return bill(currency, amount, description)


        else:
            return redirect('/')

    else:
        return render_template("index.html")

@app.route("/pay")
def pay(currency, amount, description):
    sign = amount + ":" + currency + ":" + shop_id +  ":" + "101" + secretKey
    sign = sha256(sign.encode('utf-8')).hexdigest()
    payment = Payment(currency="EUR", amount=amount, description=description)
    db.session.add(payment)
    db.session.commit()
    return render_template("pay.html", amount = amount, currency = currency, shop_id = shop_id, sign = sign)

@app.route("/bill", methods = ["POST"])
def bill(currency, amount, description):
    url = 'https://core.piastrix.com/bill/create'
    sign = currency + ":" + amount + ":" + currency + ":" + shop_id + ":" + "4239" + secretKey
    sign = sha256(sign.encode('utf-8')).hexdigest()
    data = {
        "description": description,
        "payer_currency": currency,
        "shop_amount": amount,
        "shop_currency": currency,
        "shop_id": shop_id ,
        "shop_order_id": 4239,
        "sign": sign
    }
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, data=json.dumps(data), headers=headers)
    if '"error_code": 0' in r.text:
        payment = Payment(currency="USD", amount=amount, description=description)
        db.session.add(payment)
        db.session.commit()
    return r.text

@app.route("/invoice", methods = ["POST", "GET"])
def invoice(currency, amount, description):
    url = ' https://core.piastrix.com/invoice/create'
    sign = amount + ":" + currency + ":" + payway + ":" + shop_id + ":" + "4239" + secretKey
    sign = sha256(sign.encode('utf-8')).hexdigest()
    data = {
        "description": description,
        "amount": amount,
        "currency" : currency,
        "payway":payway,
        "shop_id": shop_id,
        "shop_order_id" :4239,
        "sign" : sign
    }
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, data=json.dumps(data), headers=headers)
    if '"error_code": 0' in r.text:
        payment = Payment(currency="RUB", amount=amount, description=description)
        db.session.add(payment)
        db.session.commit()
        return render_template("invoice.html",url =r.json()["data"]["url"] ,
                               method = r.json()["data"]["method"] , ac_account_email =r.json()["data"]["data"]["ac_account_email"],
                               ac_sci_name = r.json()["data"]["data"]["ac_sci_name"], ac_amount =r.json()["data"]["data"]["ac_amount"],
                               ac_currency = r.json()["data"]["data"]["ac_currency"], ac_order_id =r.json()["data"]["data"]["ac_order_id"],
                               ac_sub_merchant_url = r.json()["data"]["data"]["ac_sub_merchant_url"], ac_sign = r.json()["data"]["data"]["ac_sign"],
                               )
    else:
        return r.text


if __name__ == "__main__":
    app.run(debug= True)