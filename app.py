import os
import zipfile
import threading
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__, template_folder='.')
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# လက်ရှိလုပ်ဆောင်နေမှု အခြေအနေများကို သိမ်းဆည်းရန်
progress_status = {
    "running": False,
    "current_count": 0,
    "total_passwords": 0,
    "current_password": "",
    "result": None,
    "error": None
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    global progress_status
    if 'zip_file' not in request.files or 'wordlist_file' not in request.files:
        return jsonify({"error": "ဖိုင်များ မပြည့်စုံပါ။"})
        
    zip_file = request.files['zip_file']
    wordlist_file = request.files['wordlist_file']
        
    if zip_file.filename == '' or wordlist_file.filename == '':
        return jsonify({"error": "ဖိုင်ရွေးချယ်ထားခြင်း မရှိပါ။"})
        
    zip_filename = secure_filename = zip_file.filename
    wordlist_filename = wordlist_file.filename
    
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    wordlist_path = os.path.join(app.config['UPLOAD_FOLDER'], wordlist_filename)
    
    zip_file.save(zip_path)
    wordlist_file.save(wordlist_path)
    
    # Password စုစုပေါင်း အရေအတွက်ကို ဦးစွာရေတွက်မည်
    try:
        with open(wordlist_path, 'rb') as f:
            total_lines = sum(1 for _ in f)
    except Exception as e:
        return jsonify({"error": f"ဖိုင်ဖတ်ရှုရာတွင်အမှားအယွင်းရှိသည်: {str(e)}"})

    # အခြေအနေများကို အစပျိုးမည်
    progress_status = {
        "running": True,
        "current_count": 0,
        "total_passwords": total_lines,
        "current_password": "",
        "result": None,
        "error": None
    }

    # နောက်ခံ Thread ဖြင့် Password စစ်ဆေးခြင်းကို စတင်မည် (UI မပိတ်သွားစေရန်)
    threading.Thread(target=crack_zip_task, args=(zip_path, wordlist_path)).start()
    
    return jsonify({"success": True})

def crack_zip_task(zip_path, wordlist_path):
    global progress_status
    found_password = None
    try:
        with zipfile.ZipFile(zip_path) as zf:
            with open(wordlist_path, 'rb') as f:
                for idx, line in enumerate(f, 1):
                    if not progress_status["running"]:
                        break
                    password = line.strip()
                    try:
                        decoded_pwd = password.decode('utf-8', errors='ignore')
                    except:
                        decoded_pwd = str(password)

                    progress_status["current_count"] = idx
                    progress_status["current_password"] = decoded_pwd

                    try:
                        zf.extractall(pwd=password)
                        found_password = decoded_pwd
                        break
                    except Exception:
                        continue

        if found_password:
            progress_status["result"] = f"အောင်မြင်ပါပြီ! Password မှာ: {found_password}"
        else:
            progress_status["error"] = "Password List ထဲတွင်မှန်ကန်သောPasswordမရှိပါ။"
    except Exception as e:
        progress_status["error"] = f"Error ဖြစ်ပေါ်သည်: {str(e)}"
    finally:
        progress_status["running"] = False
        if os.path.exists(zip_path): os.remove(zip_path)
        if os.path.exists(wordlist_path): os.remove(wordlist_path)

@app.route('/stream')
def stream():
    def generate():
        import json, time
        while progress_status["running"] or progress_status["result"] or progress_status["error"]:
            yield f"data: {json.dumps(progress_status)}\n\n"
            if not progress_status["running"]:
                break
            time.sleep(0.1)
        # ပြီးဆုံးသွားကြောင်း နောက်ဆုံးအကြိမ် ပို့ပေးရန်
        yield f"data: {json.dumps(progress_status)}\n\n"
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
