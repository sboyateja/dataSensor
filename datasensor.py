from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)  # Enables CORS globally for all routes

# MongoDB connection
client = MongoClient("mongodb+srv://i40:dbms2@cluster0.lixbqmp.mongodb.net/")
db = client["sensorapp"]
collection = db["sensordata"]

# Serve the frontend HTML
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Sync endpoint with CORS preflight support
@app.route('/mongodb/post', methods=['POST', 'OPTIONS'])
def post_gps_data():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response, 204

    try:
        data = request.get_json(force=True)
        if not data:
            response = jsonify({"error": "No data received"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400

        docs = [data] if isinstance(data, dict) else data if isinstance(data, list) else None
        if docs is None:
            response = jsonify({"error": "Invalid JSON format"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400

        unsynced_docs = [doc for doc in docs if not doc.get("synced", False)]
        if not unsynced_docs:
            response = jsonify({"message": "All data already synced."})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 200

        for doc in unsynced_docs:
            doc.pop("synced", None)

        result = collection.insert_many(unsynced_docs)
        inserted_ids = [str(_id) for _id in result.inserted_ids]

        response = jsonify({"message": "Inserted", "inserted_ids": inserted_ids})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 201

    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

# Bind to correct port for Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
