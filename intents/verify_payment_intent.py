import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

# Setup Logging
#logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Connection
try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DATABASE_NAME")]
    payments_collection = db["payments"]
    paid_subjects_collection = db["paid_subjects"]
except Exception as e:
    #logging.error(f"MongoDB Connection Error: {e}")
    raise SystemExit("Failed to connect to MongoDB.")

def extract_price(price_data):
    """ Convert MongoDB's {"$numberInt": "1"} format to integer """
    if isinstance(price_data, dict) and "$numberInt" in price_data:
        return int(price_data["$numberInt"])
    return price_data if isinstance(price_data, int) else None

def clean_value(value):
    """ Convert 'null' string or None to proper None type """
    return None if value in ["null", None] else value


def verify_payment(user_input):
    #logging.info(f"User Input: {user_input}")

    query = {"$or": [{"email": user_input.get("email")},
                     {"payment_id": user_input.get("payment_id")},
                     {"rrn": user_input.get("rrn")}]}

    if not any(query["$or"]):
        return {"fulfillmentMessages": [{"text": {"text": ["Please provide your email, payment ID, or transaction ID."]}}]}

    purchased_items = list(payments_collection.find(query, {"_id": 0, "currency": 0, "status": 0, "mobile_no": 0}))
    #logging.info(f"Purchased Items: {purchased_items}")

    if not purchased_items:
        return {"fulfillmentMessages": [{"text": {"text": ["No payment found with the given details."]}}]}

    fulfillment_messages = []

    for idx, payment_data in enumerate(purchased_items, start=1):
        subject_name = clean_value(payment_data.get('subject'))
        language = clean_value(payment_data.get('language'))
        month = clean_value(payment_data.get('month'))
        price = extract_price(payment_data.get('price'))
        payment_id = payment_data.get('payment_id', 'N/A')

        #logging.info(f"Checking Subject: {subject_name}, Language: {language}, Price: {price}, Month: {month}")

        subject_query = {"price": {"$in": [price, str(price)]}}
        if subject_name:
            subject_query["subject"] = {"$regex": f"^{re.escape(subject_name)}$", "$options": "i"}
        if language:
            subject_query["language"] = {"$regex": f"^{re.escape(language)}$", "$options": "i"}
        if month:
            subject_query["month"] = {"$regex": f"^{re.escape(month)}$", "$options": "i"}

        #logging.info(f"Querying MongoDB: {subject_query}")
        subject_info = paid_subjects_collection.find_one(subject_query)

        if subject_info:
            subject_name = subject_name or subject_info.get("subject", "Unknown")
            language = language or subject_info.get("language", "Unknown")
            month = month or subject_info.get("month", "Unknown")
            pdf_link = subject_info.get("pdf_link", "N/A")
        else:
            #logging.warning(f"No matching subject found for: {subject_query}")
            pdf_link = "N/A"

        #logging.info(f"PDF Link Found: {pdf_link}")

        text_block = f"""✅ Payment Verified!  
🆔 Payment ID: {payment_id}        
💰 Price: ₹{price}  

📌 Product {idx}:
📖 Subject: {subject_name}  
📆 Month: {month}  
🗣 Language: {language}  
"""

        if pdf_link != "N/A":
            text_block += f"\n📄 Download PDF: {pdf_link}\n"
        else:
            text_block += "\n⚠️ No PDF link found for this subject.\n"

        text_block += "\n🙏 Thank you for your support! 😊"

        fulfillment_messages.append({"text": {"text": [text_block]}})

    return {"fulfillmentMessages": fulfillment_messages}

