from flask import Flask, request, render_template, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from extract_data import extract_text_from_pdf
from ai_response import get_response
import speech_recognition as sr
import pyttsx3
import base64
from pydub import AudioSegment
import io
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '7472272168fe83a1e126d7d7ada17f474d672c02a40cc206'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB file size limit
logged_in = False

db = SQLAlchemy(app)
engine = pyttsx3.init()

# Create the database
with app.app_context():
    db.create_all()

from flask import Flask, render_template, request, redirect, url_for, session, flash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



users = {}

# Function to send a welcome email
def send_welcome_email(user_email, username):
    sender_email = "sifra.care.ai@gmail.com"
    sender_password = "ydir txqo aavz uwdf"  # Use App Password if using Gmail
    subject = "Welcome to Sifra!"

    # Email body
    body = f"""
    Hi {username},

    Welcome to Sifra! 🎉 We're excited to have you on board.

    Best,
    Sifra Team
    """

    # Setup email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = user_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        print(f"Welcome email sent to {user_email}")
    except Exception as e:
        print(f"Error sending email: {e}")


# Signup route
# Signup route
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    if email in users:
        flash("Email already registered. Please log in.", "error")
        return redirect(url_for("home"))  # Redirect to login if email exists

    # Save user details
    users[email] = {"username": username, "password": password}

    # ✅ Send welcome email
    send_welcome_email(email, username)

    # ✅ Set session so user is logged in automatically
    session['user'] = username

    flash("Signup successful! Welcome, " + username, "success")

    # ✅ Redirect to index.html after signup
    return redirect(url_for("index"))




@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Store user details securely (replace with actual database logic)
        users[username] = password

        # ✅ Automatically log in the user
        session['user'] = username
        print("Session after signup:", session.get('user'))  # Debugging

        flash("Signup successful! Welcome, " + username, "success")
        return redirect(url_for('index'))  # ✅ Redirect to index.html



# Dashboard (protected route)
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return f"Welcome, {session['user']}! This is your dashboard."
    else:
        flash("Please log in first.", "error")
        return redirect(url_for("home"))


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

def speak(text):
    engine.say(text)
    engine.runAndWait()

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError:
            return "Speech recognition service is unavailable."

@app.route("/recognize_speech", methods=['POST'])
def recognize_speech_route():
    try:
        data = request.get_json()
        if 'audio_data' not in data:
            return jsonify({"error": "No audio data provided."}), 400

        audio_data = data['audio_data']

        # Decode the base64 audio data
        audio_bytes = base64.b64decode(audio_data)

        # Convert the audio bytes into an AudioSegment
        audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))  # Adjust for the actual audio format

        # Now we can use speech recognition
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)  # Listen to the audio
            user_input = recognizer.recognize_google(audio)  # Recognize speech using Google's API
            print(f"User said: {user_input}")

            # Process the recognized speech with your AI model
            response = get_response(text=user_input)

            # Speak the response back
            speak(response)

            return jsonify({"response": response})

    except Exception as e:
        print(f"Error in recognize_speech_route: {e}")
        return jsonify({"error": "Something went wrong with speech recognition."}), 500


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


# Home Route (Login/Register Page)
@app.route("/", methods=['GET', 'POST'])
def home():
    if logged_in:
        return render_template("index.html")
    else:
        return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')  # Assuming login is via email
    password = request.form.get('password')

    # Check if user exists in the database
    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):  # Verify password
        session['user'] = user.username  # Store user session
        flash("Login successful!", "success")
        return redirect(url_for('index'))  # Redirect to index.html
    else:
        flash("Invalid credentials. Please try again.", "error")
        return redirect(url_for('home'))  # Redirect back to login page


@app.route('/index')
def index():
    print("Session before rendering index:", session.get('user'))  # Debugging
    if 'user' in session:  # Check if user is logged in
        return render_template('index.html')
    flash("Please log in first.", "error")
    return redirect(url_for('home'))  # Redirect to login if not logged in




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


import speech_recognition as sr
import pyttsx3
from ai_response import get_response
import time

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Set speech rate (speed) and volume (optional, you can adjust this)
engine.setProperty('rate', 150)  # 150 words per minute (you can change this)
engine.setProperty('volume', 1)  # Volume range is from 0.0 to 1.0


# Function to speak the response
def speak(text):
    print("Sifra is speaking: ", text)
    engine.say(text)
    engine.runAndWait()


# Function to listen for voice input and process it
def listen_for_voice():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening for your question...")
        recognizer.adjust_for_ambient_noise(source)  # Adjust to ambient noise
        audio = recognizer.listen(source)

        try:
            query = recognizer.recognize_google(audio)
            print(f"You said: {query}")

            # Send the recognized text to AI model
            response = get_response(report="", text=query)

            # Speak the response if it's not empty
            if response:
                speak(response)
                print("Sifra's response: ", response)

        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            speak("Sorry, I did not understand that.")
        except sr.RequestError:
            print("Sorry, I'm having trouble connecting to the speech service.")
            speak("Sorry, I'm having trouble connecting to the speech service.")


# Function to handle text input (for keyboard-based input)
def handle_text_input(user_input):
    # Process the text input with the AI model
    response = get_response(report="", text=user_input)

    # If there is a response, display it as text or speak if required
    if response:
        print("Sifra's response: ", response)

    return response



# Main function to start listening
def main():
    while True:
        print("Press 'Enter' to type your question or press 'q' to quit.")

        # You can handle text input here if you like
        user_input = input("Your question: ")

        if user_input.lower() == 'q':
            break

        # Handle typing input
        if user_input:
            response = handle_text_input(user_input)

        # Otherwise, listen for voice input
        else:
            listen_for_voice()

        time.sleep(1)


@app.route("/voice_chat", methods=['POST'])
def voice_chat():
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({"error": "No message provided."}), 400

        user_message = data['message']
        print(f"You said: {user_message}")

        # Get response from AI model (you might pass the report or other parameters here)
        response = get_response(text=user_message)

        # Speak the response
        speak(response)

        return jsonify({"response": response})

    except Exception as e:
        print(f"Error in voice_chat route: {e}")
        return jsonify({"error": "Something went wrong. Please try again later."}), 500


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