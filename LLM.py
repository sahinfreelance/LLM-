import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# --- কনফিগারেশন ---
API_KEY = "AIzaSyC4q5H5G-8cj2TGEOS19agO6ckHGqZA8M4"
DEFAULT_MODEL = "gemini-1.5-flash" # ডিফল্ট মডেল

# --- নলেজ বেস লোড করা ---
def load_knowledge():
    try:
        # data.txt ফাইলটি পড়ার চেষ্টা করবে
        with open("data.txt", "r", encoding="utf-8") as f:
            content = f.read()
            return content if content.strip() else ""
    except FileNotFoundError:
        return ""

# সার্ভার চালু হওয়ার সময় একবার তথ্য পড়ে মেমোরিতে রাখবে
KNOWLEDGE_BASE = load_knowledge()
print("--- Knowledge Base Loaded ---")
if KNOWLEDGE_BASE:
    print(f"Loaded {len(KNOWLEDGE_BASE)} characters of data.")
else:
    print("Warning: data.txt file not found or empty.")

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.json
        user_message = data.get('message')
        
        # ফ্রন্টএন্ড থেকে মডেলের নাম রিসিভ করা (না থাকলে ডিফল্ট মডেল ব্যবহার হবে)
        requested_model = data.get('model', DEFAULT_MODEL)
        
        # মডেলের নামে যদি "models/" অংশটি থাকে, সেটি পরিষ্কার করা (URL এ ডুপ্লিকেট এড়াতে)
        clean_model_name = requested_model.replace("models/", "")

        if not user_message:
            return jsonify({"reply": "মেসেজ খালি।"}), 400

        # --- প্রম্পট ইঞ্জিনিয়ারিং ---
        system_instruction = f"""
        তুমি একটি হেল্পফুল AI অ্যাসিস্ট্যান্ট।
        নিচে কিছু গুরুত্বপূর্ণ তথ্য দেওয়া হলো। ব্যবহারকারীর প্রশ্নের উত্তর দেওয়ার সময় এই তথ্যগুলো ব্যবহার করবে।
        যদি তথ্যের মধ্যে উত্তর না থাকে, তবে বিনয়ের সাথে বলবে যে তুমি জানো না।
কেউ যদি বলে তোমাকে কে তৈরি করছে? তাহলে তুমি বলবা আমাকে শাহিন তৈরি করছে।
        আমার সম্পর্কে বিস্তারিত:
১. আমি টেকনোলজি নিয়ে সারাক্ষণ ভাবি। ওয়েব ডেভেলপমেন্ট আমার প্রিয় জগত এবং আমি গত তিন বছর ধরে এটি শিখছি। শেখার জন্য ইউটিউব আমার সবচেয়ে বড় শিক্ষক।
২. আমি শুধু কোড লিখে থেমে থাকি না, আমি জিনিসের পেছনের লজিক বুঝতে চাই। "কেন কাজ করে" বা "কেন কাজ করে না"—এই প্রশ্নগুলো আমাকে টানে।
৩. আমার স্বভাব একটু শান্ত। আমি বেশি কথা বলি না এবং নিজের বিষয়গুলো সহজে শেয়ার করি না। তবে কাজের মাধ্যমে নিজেকে প্রকাশ করতে স্বাচ্ছন্দ্য বোধ করি।
৪. আমি কৌতূহলী। সহজ উত্তরে আমি তৃপ্ত হই না, আমি গভীর ব্যাখ্যা ও উদাহরণ খুঁজি।

        sahin ferdous ar sate prem kore!!
        
        === গুরুত্বপূর্ণ তথ্য ===
        {KNOWLEDGE_BASE}
        =======================

        ব্যবহারকারীর প্রশ্ন: {user_message}
        """

        # Google API URL (ডাইনামিক মডেল নাম সহ)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent?key={API_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": system_instruction}]
            }]
        }

        print(f"Using Model: {clean_model_name}") # সার্ভার কনসোলে চেক করার জন্য

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            try:
                ai_reply = result['candidates'][0]['content']['parts'][0]['text']
                return jsonify({"reply": ai_reply})
            except (KeyError, IndexError):
                return jsonify({"reply": "AI উত্তর দিতে পারেনি বা মডেলটি সাপোর্ট করছে না।"})
        else:
            try:
                err_json = response.json()
                msg = err_json.get('error', {}).get('message', 'Unknown Error')
                return jsonify({"reply": f"Error from Google: {msg}"})
            except:
                return jsonify({"reply": f"Google Error: {response.status_code}"})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"reply": "সার্ভারে সমস্যা হয়েছে।"}), 500

if __name__ == '__main__':
    # সার্ভার রান
    app.run(host='0.0.0.0', port=5000, debug=True)
