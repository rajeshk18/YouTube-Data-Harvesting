import os

import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
import pymongo
import plotly.express as px
from streamlit_option_menu import option_menu
from googleapiclient.discovery import build
from PIL import Image

# SETTING PAGE CONFIG TO WIDE MODE AND ADDING A TITLE AND FAVICON
# icon = Image.open("https://raw.githubusercontent.com/rajeshk18/YouTube-Data-Harvesting/main/ylogo32.png")
st.set_page_config(layout="wide", page_title="Youtube Harvesting | By Rajesh", page_icon=":youtube:", menu_items={'About': """# Demo Project *"""})


# MongoDB connection
myclient = pymongo.MongoClient("mongodb+srv://arajeshkanna82:r5HSCqyWVxkSQukW@youtubedb.weh8pk8.mongodb.net/?retryWrites=true&w=majority")
mydb = myclient["youtubedatabase"]
mycol = mydb["Channel_Name"]
mydict = {
        "Channel_Name": "Example Channel",
        "Channel_Id": "UC1234567890",
        "Subscription_Count": 10000,
        "Channel_Views": 1000000,
        "Channel_Description": "This is an example channel.",
        "Playlist_Id": "PL1234567890"
}

# CREATING OPTION MENU
with st.sidebar:
    selected = option_menu(None, ["Home","Youtube-Data","Views"], 
                           icons=["house-door-fill","tools","card-text"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "15px", "text-align": "centre", "margin": "0px", 
                                                "--hover-color": "#C80101"},
                                   "icon": {"font-size": "15px"},
                                   "container" : {"max-width": "2000px"},
                                   "nav-link-selected": {"background-color": "#C80101"}})

# BUILDING CONNECTION WITH YOUTUBE API
api_key = "AIzaSyCkglXpsoXo7QjsLDBAL8mzCfX4YZzpdtg"
# api_key = "AIzaSyBngTKuDhqqY33i14-jedg0OauDPqXBQp8"
youtube = build('youtube','v3',developerKey=api_key)

# Store data in MongoDB
def post_channel_detail(channel_detail):
    id = mycol.insert_one(mydict)
    print(id.inserted_id)


# GET CHANNEL DETAILS
def get_channel_detail(channel_id):
    ch_data = []
    response = youtube.channels().list(part = 'snippet,contentDetails,statistics', id= channel_id).execute()

    for i in range(len(response['items'])):
        data = dict(Channel_id = channel_id[i],
                    Channel_name = response['items'][i]['snippet']['title'],
                    Playlist_id = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'],
                    Subscribers = response['items'][i]['statistics']['subscriberCount'],
                    Views = response['items'][i]['statistics']['viewCount'],
                    Total_videos = response['items'][i]['statistics']['videoCount'],
                    Description = response['items'][i]['snippet']['description'],
                    Country = response['items'][i]['snippet'].get('country')
                    )
        ch_data.append(data)
    return ch_data

if selected == "Home":
    col1,col2 = st.columns(2,gap= 'medium')
    col1.markdown("## :blue[Domain] : Social Media")
    col1.markdown("## :blue[Technologies] : Python, Streamlit, MongoDB, Youtube API, Microsoft Sql Server, ")
    col1.markdown("## :blue[Goal] : A Streamlit application that allows users to access and analyze data from multiple YouTube channels. ")
    col2.markdown("#   ")
    col2.markdown("#   ")
    col2.markdown("#   ")
    col2.image("https://raw.githubusercontent.com/rajeshk18/YouTube-Data-Harvesting/main/ylogo526.png")

if selected == "Youtube-Data":
    # st.markdown("#    ")
    # st.write("Please give the Channel ID :")
    # channel_id = st.text_input("Hint : Channel_id")
    # channel_detail = get_channel_detail("UCduIoIMfD8tT3KoU0-zBRgQ")
    #channel_detail = get_channel_detail(channel_id)
    # st.write(f'#### Extracted data from :green["{ch_details[0]["Channel_name"]}"] channel')
    # st.table(ch_details)

    tab1,tab2 = st.tabs(["$\huge EXTRACT $", "$\huge TRANSFORM $"])
    
    # EXTRACT TAB
    with tab1:
        st.markdown("#    ")
        st.write("### Enter the YouTube Channel_ID :")
        ch_id = st.text_input("Hint : Channel Id").split(',')

        if ch_id and st.button("Extract Data"):
            ch_details = get_channel_details(ch_id)
            st.write(f'#### Extracted data from :green["{ch_details[0]["Channel_name"]}"] channel')
            st.table(ch_details)

        if st.button("Upload to MongoDB"):
            with st.spinner('Please Wait for it...'):
                ch_details = get_channel_details(ch_id)
                v_ids = get_channel_videos(ch_id)
                vid_details = get_video_details(v_ids)
                
                def comments():
                    com_d = []
                    for i in v_ids:
                        com_d+= get_comments_details(i)
                    return com_d
                comm_details = comments()

                collections1 = db.channel_details
                collections1.insert_many(ch_details)

                collections2 = db.video_details
                collections2.insert_many(vid_details)

                collections3 = db.comments_details
                collections3.insert_many(comm_details)
                st.success("Upload to MogoDB successful !!")
      
    # TRANSFORM TAB
    with tab2:     
        st.markdown("#   ")
        st.markdown("### Select a channel to begin Transformation to SQL")
        
        ch_names = channel_names()
        user_inp = st.selectbox("Select channel",options= ch_names)
        
        def insert_into_channels():
                collections = db.channel_details
                query = """INSERT INTO channels VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"""
                
                for i in collections.find({"Channel_name" : user_inp},{'_id':0}):
                    mycursor.execute(query,tuple(i.values()))
                    mydb.commit()
                
        def insert_into_videos():
            collectionss = db.video_details
            query1 = """INSERT INTO videos VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

            for i in collectionss.find({"Channel_name" : user_inp},{"_id":0}):
                t=tuple(i.values())
                mycursor.execute(query1,t)
                mydb.commit()

        def insert_into_comments():
            collections1 = db.video_details
            collections2 = db.comments_details
            query2 = """INSERT INTO comments VALUES(%s,%s,%s,%s,%s,%s,%s)"""

            for vid in collections1.find({"Channel_name" : user_inp},{'_id' : 0}):
                for i in collections2.find({'Video_id': vid['Video_id']},{'_id' : 0}):
                    t=tuple(i.values())
                    mycursor.execute(query2,t)
                    mydb.commit()

        if st.button("Submit"):
            try:
                
                insert_into_channels()
                insert_into_videos()
                insert_into_comments()
                st.success("Transformation to MySQL Successful!!!")
            except:
                st.error("Channel details already transformed!!")
