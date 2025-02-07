import hashlib
import hmac
import os
import json
import logging
from datetime import datetime
from pymongo import MongoClient
from flask import request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]
payments_collection = db["payments"]

# Razorpay Webhook Secret
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def verify_razorpay_signature(request_data, received_signature):
    """Verify Razorpay webhook signature using HMAC-SHA256."""
    generated_signature = hmac.new(
        bytes(RAZORPAY_WEBHOOK_SECRET, 'utf-8'),
        msg=request_data,  # Raw binary data
        digestmod=hashlib.sha256
    ).hexdigest()
    
    logging.info(f"Generated Signature: {generated_signature}")
    logging.info(f"Received Signature: {received_signature}")

    return hmac.compare_digest(generated_signature, received_signature)

def handle_razorpay_webhook():
    """Handles Razorpay Webhook, verifies signature, and securely stores payment details."""
    request_data = request.data  # Get raw binary request body
    received_signature = request.headers.get('X-Razorpay-Signature')

    # Log the received request for debugging
    logging.info(f"Received Razorpay Webhook Data: {request_data}")
    logging.info(f"Received Signature: {received_signature}")

    # Reject request if signature is missing
    if not received_signature:
        logging.error("Webhook request missing signature!")
        return jsonify({"error": "Signature missing"}), 403

    # Verify Razorpay Signature
    if not verify_razorpay_signature(request_data, received_signature):
        logging.error("Signature verification failed! Possible fake request.")
        return jsonify({"error": "Invalid signature"}), 403  # Reject unauthorized requests

    # Parse JSON data
    data = json.loads(request_data)
    event = data.get("event")

    # Process only payment.captured events
    if event == "payment.captured":
        payment = data.get("payload", {}).get("payment", {}).get("entity", {})

        payment_id = payment.get("id", "N/A")
        amount = payment.get("amount", 0) // 100  # Convert paise to rupees
        currency = payment.get("currency", "INR")
        status = payment.get("status", "unknown")
        email = payment.get("email", "not_provided")
        mobile_no = payment.get("contact", "not_provided")
        transaction_id = payment.get("acquirer_data", {}).get("transaction_id", "N/A")
        date = payment.get("created_at", 0)

        # Convert date if available
        readable_date = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S') if date else "Unknown"
    
        notes = payment.get("notes", {})
        language = notes.get("language")
        subject = notes.get("subject")  # Changed from "course" to "subject"
        month = notes.get("month")  # Changed from "month_year" to "month"

        # Store payment details securely in MongoDB
        try:
            payments_collection.insert_one({
                "email": email,
                "mobile_no": mobile_no,
                "payment_id": payment_id,
                "transaction_id": transaction_id,
                "date": readable_date,
                "language": language,
                "subject": subject,
                "month": month,
                "price": amount,  # Now correctly in rupees
                "currency": currency,  # Added currency
                "status": status  # Added status
            })

            logging.info(f"✅ Payment {payment_id} stored successfully in MongoDB.")
            return jsonify({"message": "Payment details stored successfully"}), 201
        except Exception as e:
            logging.error(f"❌ MongoDB Insert Error: {str(e)}")
            return jsonify({"error": "Database error"}), 500
    else:
        logging.info("Ignoring non-payment event.")
        return jsonify({"message": "Event ignored"}), 200  # Ignore other events
