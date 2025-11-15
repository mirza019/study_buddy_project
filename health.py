from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return "StudyBuddy Bot is running", 200
