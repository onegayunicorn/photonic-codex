from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return 'CodexO Realm Portal Active'
app.run(host='0.0.0.0', port=7070)
