from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Test server is running!'

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Server is healthy'})

if __name__ == '__main__':
    print("Starting test server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)