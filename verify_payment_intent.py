import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]
payments_collection = db["payments"]
paid_subjects_collection = db["paid_subjects"]  # Correct collection for paid subjects
subjects_collection = db["subjects"]  # Correct collection for subjects

# Payment Verification with Correct Price & PDF Link (Time-based Access)
def verify_payment(user_input):
    query = {}

    # Build dynamic query for MongoDB to check if any of these details match
    if user_input.get("email"):
        query["email"] = user_input["email"]
    if user_input.get("payment_id"):
        query["payment_id"] = user_input["payment_id"]
    if user_input.get("transaction_id"):
        query["transaction_id"] = user_input["transaction_id"]

    if not query:
        return {"fulfillmentText": "Please provide your email, payment ID, or transaction ID."}

    # Find matching payment data
    purchased_items = list(payments_collection.find(query))

    if not purchased_items:
        return {"fulfillmentText": "I'm sorry, no payment found with the given details."}

    response_text = "Your Payment is Successful!\n\n"

    for payment_data in purchased_items:
        # Extract necessary details from the payment data
        subject_name = payment_data.get('subject', 'N/A')
        price_str = payment_data.get('price', 'N/A')
        language = payment_data.get('language', 'N/A')
        payment_date_str = payment_data.get('date', 'N/A')

        # Convert payment date string to datetime object (full datetime format)
        if payment_date_str != 'N/A':
            try:
                payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d %H:%M:%S')  # Full datetime format
            except ValueError:
                payment_date = None
        else:
            payment_date = None

        # Check if the payment was made more than 7 days ago
        if payment_date and (datetime.now() - payment_date) > timedelta(weeks=1):
            return {
                "fulfillmentText": "Sorry, your payment details are no longer available. The access period has expired."
            }

        # Convert price to integer if it contains "₹" symbol or if it's a string
        price = None
        if isinstance(price_str, str):
            price = int(''.join(filter(str.isdigit, price_str)))
        elif isinstance(price_str, int):
            price = price_str

        # Commented out logging function for future use
        logging.info(f"Payment Data: Subject: {subject_name}, Price: {price}, Language: {language}")

        # Try to find subject info in paid_subjects collection
        subject_info = paid_subjects_collection.find_one({
            "subject_name": {"$regex": f"^{subject_name}$", "$options": "i"},
            "price": price,
            "language": {"$regex": f"^{language}$", "$options": "i"} if language != 'N/A' else {}
        })

        # If no subject info found, try more relaxed queries
        if not subject_info:
            # Try matching by subject name and price only
            subject_info = paid_subjects_collection.find_one({
                "subject_name": {"$regex": f"^{subject_name}$", "$options": "i"},
                "price": price
            })

        # If still no subject info, try matching by price and language
        if not subject_info:
            subject_info = paid_subjects_collection.find_one({
                "price": price,
                "language": {"$regex": f"^{language}$", "$options": "i"}
            })

        if subject_info:
            pdf_link = subject_info.get("pdf_link", "N/A")
            response_text += (
                f"Payment ID: {payment_data.get('payment_id', 'N/A')}\n\n"
                f"Date: {payment_data.get('date', 'N/A')}\n\n"
                f"Subject: {subject_name}\n\n"
                f"Price: ₹{price}\n\n"
                f"Language: {language}\n\n"
                f"PDF Link: {pdf_link}\n\n"
            )
        else:
            response_text += f"No paid content found for the subject '{subject_name}' at price ₹{price}.\n"

    response_text += "Thanks for your support! 😊"
    return {"fulfillmentText": response_text}
