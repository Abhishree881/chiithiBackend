from LeXmo import LeXmo
from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin
import requests
from nltk.stem.snowball import SnowballStemmer
from nltk import word_tokenize
import pandas as pd
from fastapi import FastAPI
from typing import Union
import nltk
import matplotlib.pyplot as plt


cred = credentials.Certificate('servicekey.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()
doc_ref = db.collection(u'chats')
# .document(u'72bS8jJYa1Oci3xfYPnxdtCygjP2')
# msg_set= set()
msg = []
doc = doc_ref.get()

# type(doc)
for i in doc:
    if i.exists:
        doc_data = i.to_dict()
        # print(f'Document data: {doc_data}')
        data = doc_data.values()
        data = list(data)
        # print(len(data[0]))
        for j in data:
            for k in j:
                # print(k["text"])
                msg.append(k["text"])
    else:
        print(u'No such document!')
uni_msg = set(msg)
msg_data = ""
for i in uni_msg:
    msg_data = msg_data+i+". "

# print(uni_msg)

emo = LeXmo.LeXmo(msg_data)
emo.pop('text', None)
emo_dict = {k: v for k, v in emo.items() if v > 0.00}

# Data to plot
labels = []
values = []

show = {k: v for k, v in sorted(emo_dict.items(), key=lambda item: item[1])}

for x, y in show.items():
    labels.append(x)
    values.append(y)

# Plot
plt.pie(values, labels=labels, autopct=lambda p: '{:.000f}%'.format(p))
# plt.show()
plt.bar(range(len(emo_dict)), list(emo_dict.values()),
        align='center', color="deepskyblue")
plt.xticks(range(len(emo_dict)), list(emo_dict.keys()))

# plt.axis('equal')
# plt.show()

moods = list(show.keys())
mood = moods[len(moods)-1]
# print(moods[len(moods)-1])

app = FastAPI()


@app.get("/api")
def read_root():
    return moods
