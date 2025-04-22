# Standard Library Imports
import os
import time
import uuid
import random
import re
import base64
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Third-party Imports
from flask import Flask, request, render_template, redirect, session, flash, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pydub import AudioSegment
import speech_recognition as sr
import pyttsx3
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Custom Imports
from extract_data import extract_text_from_pdf
from ai_response import get_response
from sifra_quotes import sifra_greetings, sifra_quotes


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


# Random quote
print(random.choice(sifra_quotes))

# Random greeting
print(random.choice(sifra_greetings))

def speak(text):
    engine.say(text)
    engine.runAndWait()


# Load pre-trained model and tokenizer
model_name = "sentence-transformers/all-MiniLM-L6-v2"  # You can choose another model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)


#RAG Model
def get_embedding(text):
    # Tokenize the input text
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)

    # Forward pass through the model
    with torch.no_grad():
        outputs = model(**inputs)

    # Take the mean of token embeddings (you can use different strategies for aggregation)
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

    return embeddings


def query_context(question, n_results=3):
    results = collection.query(
        query_texts=[question],
        n_results=10  # Retrieve more documents
    )

    # Get the embeddings of the query and the retrieved chunks
    query_embedding = get_embedding(question)
    chunk_embeddings = [get_embedding(doc) for doc in results['documents']]

    # Compute cosine similarities
    similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]

    # Rank the results by similarity
    ranked_chunks = sorted(zip(results['documents'], similarities), key=lambda x: x[1], reverse=True)

    # Select the top 'n_results'
    top_chunks = [chunk for chunk, _ in ranked_chunks[:n_results]]

    return top_chunks


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


def clean_response(text):
    text = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', text)  # Replace 3+ <br> with 2
    text = re.sub(r'(<br\s*/?>\s*){2}', '<br>', text)  # Replace double <br> if still present
    text = re.sub(r'\n{3,}', '\n\n', text)  # Replace 3+ new lines with just 2
    return text.strip()


if __name__ == "__main__":
    app.run(debug=True)