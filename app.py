from flask import Flask, request, jsonify
from razorpay import handle_razorpay_webhook
from dialogflow_handler import handle_intent

app = Flask(__name__)

# ✅ Root Route - Health Check
@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "It's working!"})

# ✅ Health Check Endpoint
@app.route('/health', methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "API is running"}), 200


# Set up logging configuration
#import logging
#logging.basicConfig(level=logging.DEBUG,  # Set log level to DEBUG for all logs
                    #format='%(asctime)s - %(levelname)s - %(message)s')

# Dialogflow Fulfillment Endpoint
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        #logging.info(f"Received webhook data: {data}")  # Log the received data
        response = handle_intent(data)
        return jsonify(response)
    except Exception as e:
        #logging.error(f"Error in webhook: {e}")
        return jsonify({"fulfillmentText": "An error occurred."})

# ✅ Razorpay Webhook Route
@app.route('/razorpay-webhook', methods=['POST'])
def razorpay_webhook():
    return handle_razorpay_webhook()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

