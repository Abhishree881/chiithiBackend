from LeXmo import LeXmo
from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from dotenv import load_dotenv
import threading
import os

load_dotenv()


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
app = firebase_admin.initialize_app(cred)
callback_done = threading.Event()
global_msg = []
global_userId = ""


def calculate_mood(msg):
    global global_msg
    uni_msg = set(msg)
    msg_data = ""
    for i in uni_msg:
        msg_data = msg_data+i+". "

    # print(uni_msg)
    emo = LeXmo.LeXmo(msg_data)
    emo.pop('text', None)
    emo_dict = {k: v for k, v in emo.items() if v > 0.00}

    show = {k: v for k, v in sorted(
        emo_dict.items(), key=lambda item: item[1], reverse=True)}

    global_msg = []
    return show


def on_snapshot(doc_snapshot, changes, read_time):
    global global_msg
    for doc in doc_snapshot:
        doc_dict = doc.to_dict()
        # print(f"Received document snapshot: {doc.id} => {doc_dict}")
        # print(doc_dict['messages'][0]['text'])
        messages = doc_dict['messages']
        for i in messages:
            # print(i['text'])
            global_msg.append(i['text'])
    # print("Message: ", msg)
    callback_done.set()


def on_user_snapshot(doc_snapshot, changes, read_time):
    global global_msg
    global global_userId
    for doc in doc_snapshot:
        doc_dict = doc.to_dict()
        messages = doc_dict['messages']
        for i in messages:
            if i['senderId'] == global_userId:
                # print("User: ", i['text'])
                global_msg.append(i['text'])
    callback_done.set()


def databaseMood():

    db = firestore.client()
    doc_ref = db.collection(u'chats')
    # .document(u'72bS8jJYa1Oci3xfYPnxdtCygjP2')
    # Create an Event for notifying main thread.
    doc_watch = doc_ref.on_snapshot(on_snapshot)
    # msg_set= set()
    # msg = []
    # doc = doc_ref.get()

    # # type(doc)
    # for i in doc:
    #     if i.exists:
    #         doc_data = i.to_dict()
    #         # print(f'Document data: {doc_data}')
    #         data = doc_data.values()
    #         data = list(data)
    #         # print(len(data[0]))
    #         for j in data:
    #             for k in j:
    #                 # print(k["text"])
    #                 msg.append(k["text"])
    #     else:
    #         print(u'No such document!')
    callback_done.wait()
    global global_msg
    callback_done.clear()
    # print(global_msg)
    return calculate_mood(global_msg)


def chatMood(user_id):
    global global_userId
    global global_msg
    # print(global_msg)
    global_userId = user_id
    db = firestore.client()
    doc_ref = db.collection(u'chats')
    doc_watch = doc_ref.on_snapshot(on_user_snapshot)
    callback_done.wait()
    callback_done.clear()
    # print(global_msg)
    return calculate_mood(global_msg)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)


@app.get("/mood/{user_id}")
async def read_item(user_id: str):
    return chatMood(user_id)


@app.get("/mood")
async def read_root():
    return databaseMood()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
