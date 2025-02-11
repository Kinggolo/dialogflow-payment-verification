import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# MongoDB Connection with Error Handling
try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DATABASE_NAME")]
    payments_collection = db["payments"]
    paid_subjects_collection = db["paid_subjects"]
except Exception as e:
    logging.error(f"MongoDB Connection Error: {e}")
    raise SystemExit("Failed to connect to MongoDB.")

def extract_price(price_str):
    if isinstance(price_str, str):
        match = re.search(r"\d+", price_str)
        return int(match.group()) if match else None
    return price_str if isinstance(price_str, int) else None

def parse_date(date_str):
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d-%m-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def verify_payment(user_input):
    if not user_input.get("email") and not user_input.get("payment_id") and not user_input.get("rrn"):
        return {
        "fulfillmentMessages": [
            {
                "platform": "TELEGRAM",
                "payload": {
                    "telegram": {
                        "text": "To proceed with payment verification, kindly provide your email, or payment ID, or transaction ID.\n\nExmp1: username@gmail.com\n\nExmp2: pay_PtCdM6OrdeDrfF\n\nExmp3: 232597928040 (12 digit)\n\nPlease enter anyone of them.",
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "How to find it?", "callback_data": "How to find it"}],
                               
                            ]
                        }
                    }
                }
            }
        ]
    }

    query = {"$or": [{"email": user_input.get("email")},
                     {"payment_id": user_input.get("payment_id")},
                     {"rrn": user_input.get("rrn")}]}

    projection = {
        "_id": 0,
        "rrn": 0,
        "mobile_no": 0,
        "currency": 0,
        "status": 0
    }




    purchased_items = list(payments_collection.find(query, projection))
    if not purchased_items:
        return  {
        "fulfillmentMessages": [
            {
                "platform": "TELEGRAM",
                "payload": {
                    "telegram": {
                        "text": "We couldn't verify a payment with the provided details. If you believe this is an error, please contact our support team for assistance. \n\nIf you have not made a payment yet, please complete your purchase first and then try again.\n\nAvailable for just ₹20",
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "Purchase Now", "callback_data": "Purchase Now"}],
                                [{"text": "Contect Support", "callback_data": "Contect Support"}],
                            ]
                        }
                    }
                }
            }
        ]
    }


    response_messages = []

    for payment_data in purchased_items:
        subject_name = payment_data.get('subject')
        price = payment_data.get('price')
        language = payment_data.get('language', 'N/A')
        month = payment_data.get('month', 'N/A')
        payment_id = payment_data.get('payment_id', 'N/A')
        payment_date = payment_data.get('date', 'N/A')

        # Convert price correctly if needed
        if isinstance(price, dict) and "$numberInt" in price:
            price = int(price["$numberInt"])  # Ensure integer format

        # If subject is missing, fetch it from paid_subjects_collection
        if not subject_name:
            subject_info = paid_subjects_collection.find_one({
                "price": price,
                "language": language
            })
            if subject_info:
                subject_name = subject_info.get("subject", "Unknown Subject")
            else:
                subject_name = "Unknown Subject"

        # Query for the PDF link
        subject_info = paid_subjects_collection.find_one({
            "price": price,
            "language": language
        })

        pdf_link = subject_info.get("pdf_link", "N/A") if subject_info else "N/A"

        response_text = "✅ Payment Verified!\n\n"
        response_text += f"📌 Payment ID: {payment_id}\n\n"
        response_text += f"📅 Date: {payment_date}\n\n"
        response_text += f"📖 Subject: {subject_name}\n\n"
        response_text += f"📆 Month: {month}\n\n"
        response_text += f"💰 Price: ₹{price}\n\n"
        response_text += f"🗣 Language: {language}\n\n"

        if pdf_link != "N/A":
            response_text += f"📄 PDF Link: {pdf_link}\n\n"
        else:
            response_text += "⚠️ No PDF link found for this subject.\n\n"

        response_text += "🙏 Thank you for your support! 😊"

        # Har ek purchase ke liye alag response message
        response_messages.append({"text": {"text": [response_text]}})

    return {"fulfillmentMessages": response_messages}
