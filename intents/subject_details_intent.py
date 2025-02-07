import logging
import re
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]
payments_collection = db["payments"]
subjects_collection = db["subjects"]

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG,  # Set log level to DEBUG for all logs
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Fetch Subject Details Dynamically from DB
def get_subject_details(user_input):
    subject_name = user_input.get("subject_name", "").strip()
    email = user_input.get("email", "").strip()  # Get email if provided
    logging.info(f"Received subject_name: {subject_name} and email: {email}")

    if not subject_name:
        return {"fulfillmentText": "Please specify a subject name."}

    # Sanitize subject_name to avoid issues with special characters
    subject_name = re.escape(subject_name)  # Escape special characters
    logging.info(f"Sanitized subject_name: {subject_name}")

    try:
        # Find subject in the collection
        subject = subjects_collection.find_one({
            "subject": {"$regex": f"^{subject_name}$", "$options": "i"}
        })
        logging.info(f"Found subject: {subject}")

        if subject:
            # Look for a payment entry matching subject and email
            user_payment = payments_collection.find_one({
                "subject": subject_name,
                "email": email
            })
            logging.info(f"User payment: {user_payment}")

            # Fallback PDF link if no payment is found
            pdf_link = "Demo PDF link" if not user_payment else subject.get('pdf_link', 'N/A')

            return {
                "fulfillmentText": f"Subject: {subject.get('subject', 'N/A')}\n"
                                   f"Description: {subject.get('description', 'N/A')}\n"
                                   f"Price: ₹{int(subject.get('price', 0))}\n"
                                   f"Link: {subject.get('link', 'N/A')}\n"
                                   f"PDF Link: {pdf_link}"
            }
        else:
            logging.warning(f"Subject '{subject_name}' not found.")
            return {"fulfillmentText": f"Sorry, subject '{subject_name}' not found."}
    except Exception as e:
        logging.error(f"Error fetching subject details: {e}")
        return {"fulfillmentText": "An error occurred while fetching subject details."}
