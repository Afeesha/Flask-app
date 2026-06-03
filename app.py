from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["email_service"]
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

@app.route('/org', methods=['POST'])
def add_org():
    data = request.json

    db.organizations.update_one(
        {"org_name": data["org_name"]},
        {"$set": {"emails": data["emails"]}},
        upsert=True
    )

    return jsonify({
        "message": "Organization saved successfully"
    }), 200

@app.route('/sendmail/<org_name>', methods=["POST"])
def sendemail(org_name):

    payload = request.json

    org = db.organizations.find_one({
        "org_name": org_name
    })

    if not org:
        return jsonify({
            "message": "Organization not found"
        }), 404

    emails = org["emails"]

    msg = Message(
        subject=f"Contact Form - {org_name}",
        sender=os.getenv("MAIL_USERNAME"),
        recipients=emails
    )

    msg.body = str(payload)

    mail.send(msg)

    db.email_logs.insert_one({
        "org_name": org_name,
        "emails": emails,
        "content": payload
    })

    return jsonify({
        "message": "Email sent successfully"
    }), 200

@app.route('/emails', methods=['GET'])
def email_history():

    logs = list(db.email_logs.find())

    return render_template(
        "emails.html",
        logs=logs
    )

@app.route('/')
def home():
    return "Flask Email Service Running"

if __name__ == "__main__":
    app.run(debug=True)