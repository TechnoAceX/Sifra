import random

sifra_quotes = [
    "Sifra - Success begins with self-belief!",
    "Sifra - Every day is a new opportunity!",
    "Sifra - Push yourself, because no one else will!",
    "Sifra - Dream big, work hard, stay focused!",
    "Sifra - Turn obstacles into stepping stones!",
    "Sifra - Small progress is still progress!",
    "Sifra - Your only limit is your mind!",
    "Sifra - Make today count!",
    "Sifra - Great things take time, keep going!",
    "Sifra - Discipline beats motivation every time!",
    "Sifra - Consistency is the key to success!",
    "Sifra - You are stronger than you think!",
    "Sifra - Success is built on daily habits!"
]

sifra_greetings = [
    "💡 Sifra says: Health is the greatest possession. Contentment is the greatest treasure. (Lao Tzu) 🌟",
    "💡 Sifra says: Take care of your body; it’s the only place you have to live. (Jim Rohn) 🏡",
    "💡 Sifra says: The greatest wealth is health. (Virgil) 💰",
    "💡 Sifra says: Strive for progress, not perfection. 🚀",
    "💡 Sifra says: When you feel like quitting, think about why you started. 🔥",
    "🩺 Sifra says: Happiness is the highest form of health. (Dalai Lama) 😊",
    "🩺 Sifra says: Your health is an investment, not an expense. 📈",
    "🩺 Sifra says: The first wealth is health. (Ralph Waldo Emerson) 💎",
    "🩺 Sifra says: The pain you feel today will be the strength you feel tomorrow. 💪",
    "🩺 Sifra says: No one is perfect, but everyone can improve. 🎯"
]

def get_random_quote():
    return random.choice(sifra_quotes)

def get_random_greeting():
    return random.choice(sifra_greetings)
