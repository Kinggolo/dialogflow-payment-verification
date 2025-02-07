# dialogflow-payment-verification

# Flask App Deployment on Koyeb

This repository contains a Flask web application deployed on **Koyeb** using **Gunicorn** as the WSGI server.

## Features
- Flask backend with API endpoints
- Deployed on **Koyeb** for easy scaling
- Uses **Gunicorn** for production
- Secure and optimized for live deployment

## Prerequisites
Make sure you have the following installed:

- Python 3.x
- Pip (Python Package Installer)
- Git
- Virtualenv

## Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository
```

### 2. Create & Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate    # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Flask App Locally (for testing)
```bash
python app.py
```

The app should now be running at:
```
http://127.0.0.1:5000
```

---

## Deployment on Koyeb

### 1. Create a `Procfile`
Ensure you have a **Procfile** in the root directory:
```plaintext
web: gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. Push to GitHub
```bash
git add .
git commit -m "Prepare for Koyeb deployment"
git push origin main
```

### 3. Deploy on Koyeb
- Go to [Koyeb Dashboard](https://app.koyeb.com/)
- Click **Create Service**
- Select **GitHub Repository**
- Choose your repository
- Set the **Run Command** to: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
- Click **Deploy**

### 4. Check Logs (Optional)
```bash
kubectl logs -f <your-app-name>
```

---

## Environment Variables
In production, configure the following environment variables on Koyeb:
```plaintext
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
```

---

## Updating the App
To update your live service, make changes and then:
```bash
git add .
git commit -m "Updated features"
git push origin main
```
Koyeb will **automatically redeploy** the new version.

---

## Useful Commands
- **Run Locally:** `python app.py`
- **Activate Virtual Env:** `source venv/bin/activate`
- **Update Dependencies:** `pip freeze > requirements.txt`
- **Deploy to Koyeb:** `git push origin main`

---

## License
This project is licensed under the MIT License.

---

## Author
- **Your Name**  
- GitHub: [yourusername](https://github.com/yourusername)
- Email: your-email@example.com

