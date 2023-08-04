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
    selected = option_menu(None, ["Home","Youtube-Data","Report & Views"], 
                           icons=["house-door-fill","tools","card-text"],
                           default_index=2,
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
    col1.markdown("## :red[About App Vr0.1] : A Streamlit application that allows users to access and analyze data from multiple YouTube channels. ")
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

    st.markdown("#  *****************  7  *******************")

    def insert_into_channels():
        collections = mgdb.channel_details
            
        #var2 = 'Pooda'
        #sql = """INSERT INTO test (name) VALUES ('%s')""" % var2
        #mycursor.execute(sql)
        #cnxn.commit()
        #st.write(var2)
        
        # Fetch the results of the query.
        #results = mycursor.fetchall()
        
        # Print the results of the query.
        #for row in results:
        #    print(row)

        for i in collections.find({"Channel_name" : user_inp},{'_id':0}):
            #st.markdown("#   ")
            #st.markdown(i.values())
            t=tuple(i.values())
        
        st.write(t)
        sql = """INSERT INTO channel_details  VALUES('%s','%s','%s','%s','%s','%s','%s','%s')""" % t
        # st.write(sql)
        st.write('Channel_name')
        mycursor.execute(sql)
        cnxn.commit()
        return
        
    def insert_into_videos():
        collections = mgdb.video_details

        for i in collections.find({"Channel_name" : user_inp},{"_id":0}):
            t=tuple(i.values())
                
        sql = """INSERT INTO video_details VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')""" % t
        st.write(t)
        mycursor.execute(sql)
        cnxn.commit()
        return

    def insert_into_comments():
        collectionsV = mgdb.video_details
        collectionsC = mgdb.comments_details

        st.write('insert_into_comments')
            
        for vid in collectionsV.find({"Channel_name" : user_inp},{'_id' : 0}):
            for i in collectionsC.find({'Video_id': vid['Video_id']},{'_id' : 0}):
                t=tuple(i.values())
                st.write(t)
            sql = """INSERT INTO comments_details VALUES('%s','%s','%s','%s','%s','%s','%s')""" % t
            mycursor.execute(sql)
            cnxn.commit()
        return

    if st.button("Submit"):
        try:
            insert_into_channels()
            insert_into_videos()
            insert_into_comments()
            st.success("Transformation to MSSQL Successful!!!")
        except OSError as err:
            st.error("OS error:", err)
        except ValueError:
            st.error("OS error:", err)
        except Exception as err:
            st.error("Unexpected", err)

# VIEW PAGE
if selected == "Report & Views":
    
    st.write("## :orange[Select any question to get Insights]")
    questions = st.selectbox('Questions',
    ['Click the question that you would like to query',
    '1. What are the names of all the videos and their corresponding channels?',
    '2. Which channels have the most number of videos, and how many videos do they have?',
    '3. What are the top 10 most viewed videos and their respective channels?',
    '4. How many comments were made on each video, and what are their corresponding video names?',
    '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
    '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
    '7. What is the total number of views for each channel, and what are their corresponding channel names?',
    '8. What are the names of all the channels that have published videos in the year 2022?',
    '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
    '10. Which videos have the highest number of comments, and what are their corresponding channel names?'])
    
    if questions == '1. What are the names of all the videos and their corresponding channels?':
        mycursor.execute("""SELECT title AS Video_Title, channel_name AS Channel_Name FROM video_details ORDER BY channel_name""")
        columns = [column[0] for column in mycursor.description]
        results = cursor.fetchall()
        df = pd.DataFrame(results, columns=columns)
        st.write(df)
        
    elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, total_videos AS Total_Videos
                            FROM channel_details
                            ORDER BY total_videos DESC""")
        df = pd.DataFrame(mycursor.fetchall())
        st.write(df)
        st.write("### :green[Number of videos in each channel :]")
        fig = px.bar(df,
                     x=mycursor.column_names[0],
                     y=mycursor.column_names[1],
                     orientation='v',
                     color=mycursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)
        
    elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, title AS Video_Title, views AS Views 
                            FROM video_details
                            ORDER BY views DESC
                            LIMIT 10""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Top 10 most viewed videos :]")
        fig = px.bar(df,
                     x=mycursor.column_names[2],
                     y=mycursor.column_names[1],
                     orientation='h',
                     color=mycursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)
        
    elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
        mycursor.execute("""SELECT a.video_id AS Video_id, a.title AS Video_Title, b.Total_Comments
                            FROM video_details AS a
                            LEFT JOIN (SELECT video_id,COUNT(comment_id) AS Total_Comments
                            FROM comments_details GROUP BY video_id) AS b
                            ON a.video_id = b.video_id
                            ORDER BY b.Total_Comments DESC""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
          
    elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name,title AS Title,likes AS Likes_Count 
                            FROM video_details
                            ORDER BY likes DESC
                            LIMIT 10""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Top 10 most liked videos :]")
        fig = px.bar(df,
                     x=mycursor.column_names[2],
                     y=mycursor.column_names[1],
                     orientation='h',
                     color=mycursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)
        
    elif questions == '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
        mycursor.execute("""SELECT title AS Title, likes AS Likes_Count
                            FROM video_details
                            ORDER BY likes DESC""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
         
    elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name, views AS Views
                            FROM channel_details
                            ORDER BY views DESC""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Channels vs Views :]")
        fig = px.bar(df,
                     x=mycursor.column_names[0],
                     y=mycursor.column_names[1],
                     orientation='v',
                     color=mycursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)
        
    elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
        mycursor.execute("""SELECT channel_name AS Channel_Name
                            FROM video_details
                            WHERE published_date LIKE '2022%'
                            GROUP BY channel_name
                            ORDER BY channel_name""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
        
    elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name, 
                        SUM(duration_sec) / COUNT(*) AS average_duration
                        FROM (
                            SELECT channel_name, 
                            CASE
                                WHEN duration REGEXP '^PT[0-9]+H[0-9]+M[0-9]+S$' THEN 
                                TIME_TO_SEC(CONCAT(
                                SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'H', 1), 'T', -1), ':',
                            SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'M', 1), 'H', -1), ':',
                            SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'S', 1), 'M', -1)
                            ))
                                WHEN duration REGEXP '^PT[0-9]+M[0-9]+S$' THEN 
                                TIME_TO_SEC(CONCAT(
                                '0:', SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'M', 1), 'T', -1), ':',
                                SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'S', 1), 'M', -1)
                            ))
                                WHEN duration REGEXP '^PT[0-9]+S$' THEN 
                                TIME_TO_SEC(CONCAT('0:0:', SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'S', 1), 'T', -1)))
                                END AS duration_sec
                        FROM video_details
                        ) AS subquery
                        GROUP BY channel_name""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names
                          )
        st.write(df)
        st.write("### :green[Average video duration for channels :]")
        

        
    elif questions == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name AS Channel_Name,video_id AS Video_ID,comments AS Comments
                            FROM video_details
                            ORDER BY comments DESC
                            LIMIT 10""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Videos with most comments :]")
        fig = px.bar(df,
                     x=mycursor.column_names[1],
                     y=mycursor.column_names[2],
                     orientation='v',
                     color=mycursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)
