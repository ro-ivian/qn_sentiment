# PART1 - Imports and useful functions to collect the results

import pandas as pd
import numpy as np
import re

from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report

import streamlit as st


an_df = pd.read_csv("data/an_df.csv")
tag_df = pd.read_csv("data/tag_df.csv")

TOTAL_COUNT = len(an_df)

TONE_DICT = {'Neutral':0, 'Positive':1, 'Negative':-1}
COMPANY = "publicrelay"

def getTitleAndBodyByAnalysisId(analysisId):
    entry = an_df[an_df['analysis_id']==analysisId]
    title = list(entry['title'])[0]
    body = list(entry['body'])[0]
    return [title, body]

def highlightTag(text, tag):

    pattern = re.compile(tag, re.IGNORECASE)
    return pattern.sub(f'<span style="background-color: #FFFF00">{tag}</span>', text)


def showAnalysis(n):
    _analysisId = tag_df['analysis_id'][n]
    _tag = tag_df['tag_name'][n]
    _title, _body = getTitleAndBodyByAnalysisId(_analysisId)
    _text = f'<span style="font-weight:bold">{_title}</span> \n\n {_body}'
    _hlText = highlightTag(_text, _tag)

    return [_hlText,_tag]

def recordAndNext(tone):
    recordAnswer(tone)
    gotoNextPage()

def gotoNextPage():
    #print("Old:",st.session_state.page)
    st.session_state.page += 1
    #if st.session_state.page+1 >= TOTAL_COUNT:
    #    st.session_state.page = 0
    #else:
    #    st.session_state.page += 1

    #print("New:",st.session_state.page)

def recordAnswer(tone):
    answers = st.session_state.answers
    answers.append(TONE_DICT[tone])
    st.session_state.answers = answers
    #print("Answers:", answers)



# PART2 : Imports and useful functions to submit results to mongo
import os
import pymongo
from pymongo import MongoClient
import urllib

# Loading Credentials
#with open("credentials.yaml", 'r') as stream:
#    credentials = yaml.safe_load(stream)

#mongoUsername = credentials['atlas']['username']
#mongoPass = credentials['atlas']['password']
mongoUsername = os.environ['ATLAS_USERNAME']
mongoPass = os.environ['ATLAS_PASS']
#print(mongoUsername,mongoPass)

emongoUsername = urllib.parse.quote_plus(mongoUsername)
emongoPass = urllib.parse.quote_plus(mongoPass)

# To login to Atlas: https://account.mongodb.com/account/login
client = MongoClient(f'mongodb+srv://{emongoUsername}:{emongoPass}@cluster0.95ku7.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
# Using Database
db = client['qn_sentiment']
surveys_collection = db['surveys']
names_collection = db['names']

def getUniqueName():
    pipeline = [
        { "$match": { "used": False } },
        { "$sample": { "size": 1 } }
    ]

    _name = "Unknown"
    try:
        _entry_list = list(names_collection.aggregate(pipeline))

        if _entry_list:
            _entry = _entry_list[0]
            _name = _entry['name']
            #Marking entry as used
            _entry['used']=True
            names_collection.replace_one({"_id":_entry['_id']},_entry)
            
    except Exception as e:
        print("Unable to fetch unique name due to:", e)

    return _name

def submitAnswers(answers):
    #print("Submitting the results:")
    #print(answers)

    name = getUniqueName()
    print(name,"->",answers)

    # Trying to insert a single document
    doc = {"answers":answers, "name":name, "company":COMPANY}
    surveys_collection.insert_one(doc)
    return name

# Now the main APP

if 'page' not in st.session_state:
    st.session_state.page = 0
    page = 0
else:
    page = st.session_state.page


if 'answers' not in st.session_state:
    answers = []
    st.session_state.answers = answers

#print("Page:",page)

# Replace articles: 1,6

if page < TOTAL_COUNT:

    [text,tag]=showAnalysis(page)

    with st.sidebar:
        st.write(f"Article {page+1} of {TOTAL_COUNT}:")
        st.text_input(f'Company:', tag, disabled=True)
        selected_tone = st.radio("Tone",('Positive', 'Neutral', 'Negative'))
        st.button("Next", on_click=recordAndNext, args=(selected_tone,))
        #recordAnswer(selected_tone)
        #gotoNextPage()

        

    st.markdown(text, unsafe_allow_html=True)
else:
    name = submitAnswers(st.session_state.answers)
    st.write("All Done! Thanks for participating!")
    st.text_input(f'Name:', name, disabled=True)
    st.write("To keep results confidential we don't need to know your name. A unique name however was assigned, so you may write it down to know how well you did later :-)")
    st.write(f'')
    st.write("You can close this page now!")
