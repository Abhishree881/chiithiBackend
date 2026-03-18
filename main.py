from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from nrclex import NRCLex
import os
import logging
import nltk

nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

credentials_dict = {
    "type": "service_account",
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_CERT_URL")
}

cred = credentials.Certificate(credentials_dict)
firebase_admin.initialize_app(cred)


def calculate_mood(messages):
    """
    Calculate mood from a list of message strings using emotion classification.
    Returns a dict of emotions with scores > 0, sorted by score descending.
    """
    if not messages:
        return {}

    uni_msg = set(messages)
    msg_data = ". ".join(uni_msg) + "."

    if not msg_data.strip():
        return {}

    try:
        emo = NRCLex()
        emo.load_raw_text(msg_data)
        # affect_frequencies already provides normalized scores (0..1)
        scores = emo.affect_frequencies
        return {k: v for k, v in sorted(scores.items(), key=lambda item: item[1], reverse=True) if v > 0}
    except Exception as e:
        logger.error(f"Error calculating mood: {e}")
        return {}


def get_all_messages():
    """
    Fetch all messages from the 'chats' collection.
    """
    try:
        db = firestore.client()
        docs = db.collection('chats').stream()
        all_messages = []
        for doc in docs:
            doc_dict = doc.to_dict()
            messages = doc_dict.get('messages', [])
            for msg in messages:
                if 'text' in msg:
                    all_messages.append(msg['text'])
        return all_messages
    except Exception as e:
        logger.error(f"Error fetching all messages: {e}")
        raise HTTPException(status_code=500, detail="Error fetching data")


def get_user_messages(user_id):
    """
    Fetch messages for a specific user from the 'chats' collection.
    """
    try:
        db = firestore.client()
        docs = db.collection('chats').stream()
        user_messages = []
        for doc in docs:
            doc_dict = doc.to_dict()
            messages = doc_dict.get('messages', [])
            for msg in messages:
                if msg.get('senderId') == user_id and 'text' in msg:
                    user_messages.append(msg['text'])
        return user_messages
    except Exception as e:
        logger.error(f"Error fetching user messages for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching data")


app = FastAPI(title="Chat Mood Analyzer", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/mood")
async def get_overall_mood():
    """
    Get the overall mood from all chat messages.
    """
    messages = get_all_messages()
    mood = calculate_mood(messages)
    return {"mood": mood}


@app.get("/mood/{user_id}")
async def get_user_mood(user_id: str):
    """
    Get the mood for a specific user's messages.
    """
    messages = get_user_messages(user_id)
    mood = calculate_mood(messages)
    return {"mood": mood}
