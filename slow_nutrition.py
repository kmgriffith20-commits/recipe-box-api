from flask import Flask, jsonify
import time

app = Flask(__name__)

@app.get("/nutrition/<ingredient>")
def nutrition(ingredient):
    time.sleep(1)
    return jsonify({
        "ingredient": ingredient,
        "calories": 25,
        "status": "success"
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
