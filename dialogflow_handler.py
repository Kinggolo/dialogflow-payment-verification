import logging
from intents.verify_payment_intent import verify_payment  # Ensure this import is correct
#from intents.subject_details_intent import get_subject_details  # Ensure this import is correct

def handle_intent(data):
    try:
        intent_name = data['queryResult']['intent']['displayName']
        user_input = data['queryResult'].get('parameters', {})
        payload = data.get('originalDetectIntentRequest', {}).get('payload', {})

        # Debugging logs for intent name and user input
        logging.info(f"Intent Name: {intent_name}")  
        logging.info(f"User Input: {user_input}")

        # Handling different intents
        if intent_name == "Payment Verification":
            # Call the payment verification function
            response = verify_payment(user_input)
            return response  # Ensure the response is returned properly
        
        #elif intent_name == "Subject Details":  
            response = get_subject_details(user_input) 
            return response  # Ensure the response is returned properly

    except Exception as e:
        logging.error(f"Error: {e}")
        return {"fulfillmentText": "An error occurred while processing the request."}

    # Default response if intent is not recognized
    return {"fulfillmentText": "Sorry, I didn't understand your request."}
