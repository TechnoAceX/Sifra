from flask import Flask, request, render_template, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from extract_data import extract_text_from_pdf
from ai_response import get_response

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '7472272168fe83a1e126d7d7ada17f474d672c02a40cc206'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB file size limit
logged_in = False

db = SQLAlchemy(app)

import random

# List of random quotes for Sifra
sifra_quotes = [
    ".Sifra - Success begins with self-belief!",
    ".Sifra - Every day is a new opportunity!",
    ".Sifra - Push yourself, because no one else will!",
    ".Sifra - Dream big, work hard, stay focused!",
    ".Sifra - Turn obstacles into stepping stones!",
    ".Sifra - Small progress is still progress!",
    ".Sifra - Your only limit is your mind!",
    ".Sifra - Make today count!",
    ".Sifra - Great things take time, keep going!",
    ".Sifra - Discipline beats motivation every time!",
    ".Sifra - Consistency is the key to success!",
    ".Sifra - You are stronger than you think!",
    ".Sifra - Success is built on daily habits!"
]

sifra_greetings = [
    "💡 Sifra says: Health is the greatest possession. Contentment is the greatest treasure. (Lao Tzu) 🌟 Q: How may I assist you in achieving a healthier life today? 🤔",
    "💡 Sifra says: Take care of your body; it’s the only place you have to live. (Jim Rohn) 🏡 Q: What’s one small step you’d like to take for your well-being? 💪",
    "💡 Sifra says: The greatest wealth is health. (Virgil) 💰 Q: How can I support you in investing in your well-being? 🏆",
    "💡 Sifra says: Strive for progress, not perfection. 🚀 Q: Every small step matters! How can I support your journey? 🏁",
    "💡 Sifra says: When you feel like quitting, think about why you started. 🔥 Q: Let’s push forward together—how can I assist you? 💯",

    "🩺 Sifra says: Happiness is the highest form of health. (Dalai Lama) 😊 Q: Let’s work together to build a happier, healthier you! 🌈",
    "🩺 Sifra says: Your health is an investment, not an expense. 📈 Q: Ready to make a positive change today? 🔥",
    "🩺 Sifra says: The first wealth is health. (Ralph Waldo Emerson) 💎 Q: Let’s focus on what truly matters—your well-being! ✨",
    "🩺 Sifra says: The pain you feel today will be the strength you feel tomorrow. 💪 Q: Keep going! Need motivation? I’m here for you! 🔥",
    "🩺 Sifra says: No one is perfect, but everyone can improve. 🎯 Q: Small improvements lead to great results! How may I guide you today? 🚀",

    "⚕️ Sifra says: The groundwork for all happiness is good health. (Leigh Hunt) 🌟 Q: How can I help you take a step toward happiness today? 😊",
    "⚕️ Sifra says: He who has health has hope, and he who has hope has everything. (Arabian Proverb) 🙌 Q: What health goal can I assist you with today? 🎯",
    "⚕️ Sifra says: Health is like money, we never have a true idea of its value until we lose it. (Josh Billings) 💸 Q: How may I help you protect your greatest asset? 🛡️",
    "⚕️ Sifra says: To keep the body in good health is a duty… otherwise, we shall not be able to keep the mind strong and clear. (Buddha) 🧘‍♂️ Q: How can I support you in balancing mind and body? 🌿",
    "⚕️ Sifra says: It’s never too late to start. It’s always too early to quit. ⏳ Q: Let’s begin your journey—how can I help? 🚀",

    "🌿 Sifra says: A healthy outside starts from the inside. (Robert Urich) 🍏 Q: How may I assist you in nurturing your inner health? 🌱",
    "🌿 Sifra says: Physical fitness is the first requisite of happiness. (Joseph Pilates) 🏃‍♂️ Q: Let’s find a way to keep you moving and feeling great! 💪",
    "🌿 Sifra says: The food you eat can be either the safest and most powerful form of medicine or the slowest form of poison. (Ann Wigmore) 🥗 Q: Need guidance on making better food choices? 🍽️",
    "🌿 Sifra says: Your body is your greatest asset—treat it well! 💖 Q: What’s one healthy habit you’d like to start today? 🏆",
    "🌿 Sifra says: Your health is your wealth, invest wisely. 💰 Q: What’s one step you’d like to take today for a healthier future? 🚀"
]


@app.route('/get_greeting', methods=['GET'])
def get_greeting():
    return jsonify({'greeting': random.choice(sifra_greetings)})

# Randomly pick a quote for the chatbot header
@app.route('/get_quote', methods=['GET'])
def get_quote():
    return jsonify({'quote': random.choice(sifra_quotes)})

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Correct field name

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)  # Hash the password

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Create the database
with app.app_context():
    db.create_all()


# Home Route (Login/Register Page)
@app.route("/", methods=['GET', 'POST'])
def home():
    if logged_in:
        return render_template("index.html")
    else:
        return render_template("login.html")


# Ensure the upload folder exists
UPLOAD_FOLDER = 'static/files'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store extracted text with unique file IDs
uploaded_reports = {}


# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# File upload route (Extracts text from the uploaded file)
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            unique_id = str(uuid.uuid4())
            filename = f"{unique_id}_{secure_filename(file.filename)}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            extracted_text = extract_text_from_pdf(file_path)
            uploaded_reports[unique_id] = extracted_text

            return jsonify({'message': f'File {filename} uploaded successfully', 'file_id': unique_id}), 200
        else:
            return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        print(f"Error in upload: {e}")
        return jsonify({'error': str(e)}), 500


# Chat route for processing user messages
@app.route("/chat", methods=['GET', 'POST'])
def chat():
    try:
        if request.content_type != 'application/json':
            return jsonify({'error': 'Unsupported Media Type'}), 415

        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message']
        file_id = data.get('file_id', '')

        report = uploaded_reports.get(file_id, "I'm here to chat! Feel free to ask me anything.")
        raw_response = get_response(report=report, text=user_message)

        # Clean up the response to remove excessive <br> tags
        cleaned_response = clean_response(raw_response)

        return jsonify({'response': cleaned_response})
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({'error': str(e)}), 500



# Login Route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            flash("Login successful!", "success")
            global logged_in
            logged_in = True
            return redirect("/")
        else:
            flash("Invalid credentials. Please try again.", "error")
            return redirect("/")
    else:
        return render_template("login.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already taken. Try a different one.", "error")
            return redirect("/")

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Try logging in.", "error")
            return redirect("/")

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        global logged_in
        logged_in = True

        flash("Registration successful! Please log in.", "success")
        return redirect("/")
    else:
        return render_template("register.html")


# Logout Route
@app.route("/logout")
def logout():
    global logged_in
    logged_in = False
    flash("You have been logged out.", "success")

    # Check if it's an AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": "You have been logged out."})

    return redirect("/")

import re

def clean_response(text):
    text = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', text)  # Replace 3+ <br> with 2
    text = re.sub(r'(<br\s*/?>\s*){2}', '<br>', text)  # Replace double <br> if still present
    text = re.sub(r'\n{3,}', '\n\n', text)  # Replace 3+ new lines with just 2
    return text.strip()


if __name__ == "__main__":
    app.run(debug=True)
