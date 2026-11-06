import os
import zipfile
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    
    if request.method == 'POST':
        # Form ကနေ ဖိုင်ပါလာခြင်း ရှိမစစ်ဆေးခြင်း
        if 'zip_file' not in request.files or 'wordlist_file' not in request.files:
            error = "ဖိုင်များ မပြည့်စုံပါ။"
            return render_template('index.html', result=result, error=error)
            
        zip_file = request.files['zip_file']
        wordlist_file = request.files['wordlist_file']
        
        if zip_file.filename == '' or wordlist_file.filename == '':
            error = "ဖိုင်ရွေးချယ်ထားခြင်း မရှိပါ။"
            return render_template('index.html', result=result, error=error)
            
        if zip_file and wordlist_file:
            zip_filename = secure_filename(zip_file.filename)
            wordlist_filename = secure_filename(wordlist_file.filename)
            
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
            wordlist_path = os.path.join(app.config['UPLOAD_FOLDER'], wordlist_filename)
            
            zip_file.save(zip_path)
            wordlist_file.save(wordlist_path)
            
            # Password Attack စတင်ခြင်း
            found_password = None
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    with open(wordlist_path, 'rb') as f:
                        for line in f:
                            password = line.strip()
                            try:
                                zf.extractall(pwd=password)
                                found_password = password.decode('utf-8', errors='ignore')
                                break
                            except Exception:
                                continue
                
                if found_password:
                    result = f"အောင်မြင်ပါပြီ! Password မှာ: {found_password}"
                else:
                    error = "Wordlist ထဲတွင် မှန်ကန်သော Password မရှိပါ။"
            except Exception as e:
                error = f"Error ဖြစ်ပေါ်သည်: {str(e)}"
            
            # အသုံးပြုပြီး ဖိုင်များကို ပြန်ဖျက်ရန် (Disk Space ရှင်းလင်းရန်)
            if os.path.exists(zip_path): os.remove(zip_path)
            if os.path.exists(wordlist_path): os.remove(wordlist_path)
            
    return render_template('index.html', result=result, error=error)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
