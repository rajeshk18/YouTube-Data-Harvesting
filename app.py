import os

import pyodbc
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
mgclient = pymongo.MongoClient("mongodb+srv://arajeshkanna82:r5HSCqyWVxkSQukW@youtubedb.weh8pk8.mongodb.net/?retryWrites=true&w=majority")
mgdb = mgclient["youtubedatabase"]
mgcol = mgdb["Channel_Name"]
mgdict = {
        "Channel_Name": "Example Channel",
        "Channel_Id": "UC1234567890",
        "Subscription_Count": 10000,
        "Channel_Views": 1000000,
        "Channel_Description": "This is an example channel.",
        "Playlist_Id": "PL1234567890"
}

# MSSQL Connection
cnxn_str = ("Driver={SQL Server Native Client 11.0};"
            "Server=DESKTOP-A8FK5E5\SQLEXPRESS;"
            "Database=youtube;"
            "Trusted_Connection=yes;")
cnxn = pyodbc.connect(cnxn_str)
mycursor = cnxn.cursor()

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
    return  id.inserted_id


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

# FUNCTION TO GET VIDEO IDS
def get_channel_videos(channel_id):
    video_ids = []
    # get Uploads playlist id
    res = youtube.channels().list(id=channel_id, 
                                  part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    
    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id, 
                                           part='snippet', 
                                           maxResults=50,
                                           pageToken=next_page_token).execute()
        
        for i in range(len(res['items'])):
            video_ids.append(res['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = res.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_ids


# FUNCTION TO GET VIDEO DETAILS
def get_video_details(v_ids):
    video_stats = []
    
    for i in range(0, len(v_ids), 50):
        response = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(v_ids[i:i+50])).execute()
        for video in response['items']:
            video_details = dict(Channel_name = video['snippet']['channelTitle'],
                                Channel_id = video['snippet']['channelId'],
                                Video_id = video['id'],
                                Title = video['snippet']['title'],
                                Tags = video['snippet'].get('tags'),
                                Thumbnail = video['snippet']['thumbnails']['default']['url'],
                                Description = video['snippet']['description'],
                                Published_date = video['snippet']['publishedAt'],
                                Duration = video['contentDetails']['duration'],
                                Views = video['statistics']['viewCount'],
                                Likes = video['statistics'].get('likeCount'),
                                Comments = video['statistics'].get('commentCount'),
                                Favorite_count = video['statistics']['favoriteCount'],
                                Definition = video['contentDetails']['definition'],
                                Caption_status = video['contentDetails']['caption']
                               )
            video_stats.append(video_details)
    return video_stats


# FUNCTION TO GET COMMENT DETAILS
def get_comments_details(v_id):
    comment_data = []
    try:
        next_page_token = None
        while True:
            response = youtube.commentThreads().list(part="snippet,replies",
                                                    videoId=v_id,
                                                    maxResults=100,
                                                    pageToken=next_page_token).execute()
            for cmt in response['items']:
                data = dict(Comment_id = cmt['id'],
                            Video_id = cmt['snippet']['videoId'],
                            Comment_text = cmt['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_author = cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_posted_date = cmt['snippet']['topLevelComment']['snippet']['publishedAt'],
                            Like_count = cmt['snippet']['topLevelComment']['snippet']['likeCount'],
                            Reply_count = cmt['snippet']['totalReplyCount']
                           )
                comment_data.append(data)
            next_page_token = response.get('nextPageToken')
            if next_page_token is None:
                break
    except:
        pass
    return comment_data


# FUNCTION TO GET CHANNEL NAMES FROM MONGODB
def channel_names():   
    ch_name = []
    for i in mgdb.channel_details.find():
        ch_name.append(i['Channel_name'])
    return ch_name
        
if selected == "Home":
    col1,col2 = st.columns(2,gap= 'medium')
    col1.markdown("## :red[About App] : A Streamlit application that allows users to access and analyze data from multiple YouTube channels. ")
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
   
    # EXTRACT TAB
    st.markdown("#    ")
    st.write("### Enter the YouTube Channel Id :")
    ch_id = st.text_input("Hint : Channel Id").split(',')

    if ch_id and st.button("Extract Data"):
        ch_details = get_channel_detail(ch_id)
        st.write(f'#### Extracted data from :green["{ch_details[0]["Channel_name"]}"] channel')
        st.table(ch_details)

    if st.button("Upload to MongoDB"):
        with st.spinner('Please Wait for it...'):
            ch_details = get_channel_detail(ch_id)
            v_ids = get_channel_videos(ch_id)
            vid_details = get_video_details(v_ids)
        
            def comments():
                com_d = []
                for i in v_ids:
                    com_d+= get_comments_details(i)
                return com_d
            comm_details = comments()

            collections1 = mgdb.channel_details
            collections1.insert_many(ch_details)

            collections2 = mgdb.video_details
            collections2.insert_many(vid_details)

            collections3 = mgdb.comments_details
            collections3.insert_many(comm_details)
            st.success("Upload to MogoDB successful !!")


    st.markdown("""---""")
    st.markdown("#   ")
    st.markdown("### Select a channel to begin Transformation to SQL")

    ch_names = channel_names()
    user_inp = st.selectbox("Select channel",options= ch_names)

    def insert_into_channels():
        collections = mgdb.channel_details
        st.markdown("### Channel_details-1")
        # strSql = """INSERT INTO channel_details VALUES('%s','%s','%s','%s','%s','%s','%s','%s')"""
        strSql = """INSERT INTO test VALUES('rajesh')"""
        mycursor.execute(strSql)
        cnxn.commit()
            
        #for i in collections.find({"Channel_name" : user_inp},{'_id':0}):
        #    st.markdown(i.values())
        #    mycursor.execute(strSql,tuple(i.values()))
        #    cnxn.commit()
        
    def insert_into_videos():
        collectionss = mgdb.video_details
        strSql = """INSERT INTO video_details VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        for i in collectionss.find({"Channel_name" : user_inp},{"_id":0}):
            t=tuple(i.values())
            mycursor.execute(strSql,t)
            cnxn.commit()

    def insert_into_comments():
        collections1 = mgdb.video_details
        collections2 = mgdb.comments_details
        strSql = """INSERT INTO comments_details VALUES(%s,%s,%s,%s,%s,%s,%s)"""

        for vid in collections1.find({"Channel_name" : user_inp},{'_id' : 0}):
            for i in collections2.find({'Video_id': vid['Video_id']},{'_id' : 0}):
                t=tuple(i.values())
                mycursor.execute(strSql,t)
                cnxn.commit()

    if st.button("Submit"):
        try:
            insert_into_channels()
            "insert_into_videos()
            "insert_into_comments()
            st.success("Transformation to MSSQL Successful!!!")
        except OSError as err:
            st.error("OS error:", err)
        except ValueError:
            st.error("OS error:", err)
        except Exception as err:
            st.error("Unexpected", err)
