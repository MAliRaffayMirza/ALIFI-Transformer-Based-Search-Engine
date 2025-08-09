from flask import Flask, send_file, request, session, redirect
import html
from datetime import date
import sqlite3
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
import torch
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

app=Flask(__name__)
app.secret_key="AliRaffay"

@app.route("/logo")
def logoimg():
	return send_file("html/static/logo.PNG", mimetype="image/png")

@app.route("/fav")
def fav():
	return send_file("html/static/fav.PNG", mimetype="image/png")





@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi - Search Accross The Internet!</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      background-color: #e6f2ff;
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    .top-bar {
      display: flex;
      justify-content: flex-end;
      padding: 15px 25px;
      font-size: 18px;
      gap: 20px;
    }

    .top-bar a {
      text-decoration: none;
      color: #0000cc;
    }

    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .main img {
      max-width: 90%;
      width: 400px;
      height: auto;
    }

    .search-box {
      display: flex;
      width: 100%;
      max-width: 700px;
      margin-top: 40px;
    }

    .search-box input[type="text"] {
      flex: 1;
      padding: 15px 20px;
      font-size: 18px;
      border: 3px solid #13008c;
      border-right: none;
      border-top-left-radius: 25px;
      border-bottom-left-radius: 25px;
      outline: none;
    }

    .search-box input[type="submit"] {
      padding: 0 20px;
      font-size: 24px;
      border: 3px solid #a10202;
      border-left: none;
      background-color: white;
      border-top-right-radius: 25px;
      border-bottom-right-radius: 25px;
      cursor: pointer;
    }

    @media (max-width: 600px) {
      .top-bar {
        font-size: 16px;
        flex-direction: column;
        align-items: center;
        gap: 10px;
      }

      .search-box input[type="text"] {
        font-size: 16px;
        padding: 12px 15px;
      }

      .search-box input[type="submit"] {
        font-size: 20px;
        padding: 0 15px;
      }
    }
  </style>
</head>
<body>

  <div class="top-bar">
    <a href="/search-console">Index Your Website!</a>
    <a href="#">Chat Onsite</a>
  </div>

  <div class="main">
    <img src="/logo" alt="AliFi Logo">
    <form method="POST" action="/search" class="search-box">
      <input type="text" name="query" placeholder="Search Accross Web">
      <input type="submit" value="🔍">
    </form>
  </div>

</body>
</html>
"""



@app.route("/search", methods=["GET"])
def rou():
	return redirect("/")


@app.route("/search", methods=["POST"])
def search():
    titlelist = []
    htmll=""
    with open("ads.txt", "r", encoding="utf-8") as file:
      info = file.readlines()
    for singlead in info:
      ad = singlead.strip().split("^")
      htmll+="""<table class="result-table">
  <tr>
    <td
>      <a href='"""+ad[0]+"""' class="result-title"
         onmouseover="this.style.textDecoration='underline';" 
         onmouseout="this.style.textDecoration='none';">"""+ad[1]+"""</a>
         
      <div class="result-link">
        <b style="color: green;">Sponsored</b> · """+ad[0]+"""</div>
      
      <div class="result-meta">"""+ad[2]+"""</div>
    </td>
  </tr>
</table>"""
    query = request.form.get("query")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embed = model.encode(query, convert_to_tensor=True)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
INSERT INTO searches (keyword, count)
VALUES (?, 1)
ON CONFLICT(keyword)
DO UPDATE SET count = count + 1;
""", (query.lower(),))
    cursor.execute("SELECT title, link, meta FROM urls WHERE status = ?", ("live",))
    allsearch = cursor.fetchall()
    cursor.execute("SELECT title FROM urls WHERE status = ?", ("live",))
    alltitles = cursor.fetchall()

    for (title,) in alltitles:
        titlelist.append(title)

    titles_embeded = model.encode(titlelist, convert_to_tensor=True)
    match_score = util.cos_sim(query_embed, titles_embeded)[0]
    threshold = 0.6
    filtered_indices = [i for i, score in enumerate(match_score) if score >= threshold]
    sorted_scores = sorted(filtered_indices, key=lambda i: match_score[i], reverse=True)
    top10_indices = sorted_scores[:min(10, len(sorted_scores))]

    for i in top10_indices:
        title, link, meta = allsearch[i]
        htmll += f"""
<table class="result-table">
  <tr>
    <td>
      <a href="{link}" 
         class="result-title"
         onmouseover="this.style.textDecoration='underline';" 
         onmouseout="this.style.textDecoration='none';">{title}</a>
         
      <div class="result-link">{link}</div>
      
      <div class="result-meta">
        {meta}
        <form method="POST" action="/report" style="display:inline; background-color:white; font-size:20px;">
          <input type="hidden" name="url" value="{link}" style="background-color:white; font-size:12px; border:0.5px dotted red;">
          <button type="submit" class="report-btn" style="background-color:white; font-size:12px; border:0.5px dotted red;"><b>Report</b></button>
        </form>
      </div>
      
    </td>
  </tr>
</table>"""
    conn.commit()
    conn.close()

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{query.title()} - AliFI Search</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <style>
    body {{
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      word-wrap: break-word;
      overflow-wrap: break-word;
    }}

    .top-links {{
      font-size: 18px;
      margin-top: 10px;
      margin-right: 20px;
      display: flex;
      justify-content: flex-end;
      gap: 20px;
      flex-wrap: wrap;
    }}

    .top-links a {{
      color: black;
      text-decoration: none;
    }}

    .search-bar-container {{
      width: 100%;
      border: 1px solid #bfbbbb;
      border-top: none;
      border-right: none;
      border-left: none;
      border-bottom-left-radius: 25px;
      border-bottom-right-radius: 25px;
      margin-top: 10px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      padding: 10px 2%;
      box-sizing: border-box;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      gap: 10px;
    }}

    .search-bar-container img {{
      height: 60px;
      width: auto;
    }}

    form {{
      display: flex;
      width: 85%;
      max-width: 100%;
      flex-wrap: nowrap;
    }}

    input[type="text"] {{
      width: 100%;
      border-top-left-radius: 25px;
      background-color: white;
      border: 3px solid #13008c;
      border-right: none;
      border-bottom-left-radius: 25px;
      font-size: 18px;
      height: 50px;
      padding-left: 20px;
      padding-right: 20px;
      box-sizing: border-box;
    }}

    input[type="submit"] {{
      width: 70px;
      height: 50px;
      background-color: white;
      border: 3px solid #a10202;
      border-top-right-radius: 25px;
      border-bottom-right-radius: 25px;
      font-size: 28px;
      cursor: pointer;
    }}

    .result-header {{
      min-width: 96%;
      margin: 20px auto 0 auto;
      background-color: #f7f7f7;
      padding: 15px 20px;
      font-size: 15px;
      box-sizing: border-box;
      word-break: break-word;
    }}

    .result-table {{
      width: 100%;
      padding-left: 25px;
      padding-top: 15px;
      box-sizing: border-box;
    }}

    .result-title {{
      font-size: 19px;
      font-weight: bold;
      text-decoration: none;
      color: #1a0dab;
      display: block;
      margin-bottom: 4px;
      word-break: break-word;
    }}

    .result-link {{
      font-size: 14px;
      color: green;
      margin-bottom: 4px;
      word-break: break-word;
    }}

    .result-meta {{
      font-size: 14px;
      color: #545454;
      word-break: break-word;
    }}

    .results-container {{
      width: 100%;
      min-height: 320px;
      padding: 25px 10px 20px 10px;
      background-color: white;
      box-sizing: border-box;
    }}

    .footer {{
      width: 100%;
      background-color: #f7f7f7;
      border-top: 2px dashed black;
      border-bottom: 2px dashed black;
      margin-top: 30px;
      padding: 20px 10px;
      text-align: center;
      font-size: 14px;
      box-sizing: border-box;
    }}

    .footer a {{
      text-decoration: none;
      color: black;
      word-break: break-word;
    }}

    /* RESPONSIVE CHANGES */
    @media (max-width: 768px) {{
      .top-links {{
        justify-content: center;
        font-size: 16px;
        margin: 10px 0;
        padding: 0 10px;
      }}

      .search-bar-container {{
        flex-direction: column;
        align-items: center;
        gap: 15px;
      }}

      form {{
        width: 100%;
      }}

      input[type="text"] {{
        font-size: 16px;
        height: 45px;
      }}

      input[type="submit"] {{
        font-size: 24px;
        width: 60px;
        height: 45px;
      }}

      .result-header {{
        font-size: 13px;
        text-align: center;
        padding: 10px;
      }}

      .result-title {{
        font-size: 17px;
      }}
    }}

    @media (max-width: 480px) {{
      input[type="text"] {{
        padding-left: 10px;
        padding-right: 10px;
        font-size: 15px;
      }}

      input[type="submit"] {{
        font-size: 22px;
        width: 55px;
      }}

      .result-header {{
        font-size: 12px;
      }}
    }}
  </style>
</head>
<body>

<div class="top-links">
  <a href="/search-console">Index Your Website!</a>
  <a href="#">Chat Onsite</a>
</div>

<div class="search-bar-container">
  <a href="/"><img src="/logo" alt="AliFi Logo"></a>
  <form method="POST" action="/search">
    <input type="text" name="query" value="{query.title()}" placeholder="Search Across Web">
    <input type="submit" value="🔍">
  </form>
</div>

<div class="result-header">
  Search Results: Showing you relevant results out of <b>{len(titlelist)}</b> indexed URLs
</div>

<div class="results-container">
  {htmll}
</div>

<div class="footer">
  All The Copyrights (c) are reserved (2026) by 
  <a href="https://github.com/MAliRaffayMirza/">Mirza M. Ali Raffay</a>
</div>

</body>
</html>
"""


@app.route("/adminlogin", methods=["GET"])
def adminlogin():
	return"""






<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Login - AliFi Search Across The Internet!</title>
  <link rel="icon" type="image/x-icon" href="/fav">
</head>
<body bgcolor="#e6f2ff">
<br><br><br><br>
  <center>
    <h1 style="color: #003366; font-family: Arial;">Please enter Log In details below:</h1>
    
    <div style="margin-top: 20px; margin-bottom: 30px; padding: 15px; background-color: #ffffff; width: 50%; border: 2px dashed #3399ff; border-radius: 20px; font-family: Arial; color: #003366;">
      <h3>🔐 Test Credentials</h3>
      <p><b>Username:</b> <code style="background-color: #eef; padding: 2px 8px; border-radius: 6px;">Admin</code></p>
      <p><b>Password:</b> <code style="background-color: #eef; padding: 2px 8px; border-radius: 6px;">ADMIN</code></p>
    </div>

    <form method="POST" action="/admin">
      <input name="adminusername" placeholder="Enter Username" 
        style="width:50%; height:40px; font-size:16px; border:2px solid #3399ff; background-color:white; border-radius:14px; padding:8px;">
      <br><br>
      <input name="adminpassword" type="password" placeholder="Enter Password" 
        style="width:50%; height:40px; font-size:16px; border:2px solid #3399ff; background-color:white; border-radius:14px; padding:8px;">
      <br><br>
      <input type="submit" value="Log In" 
        style="background-color:#3366cc; font-family:bahnschrift; font-size:16px; font-weight:bold; border:none; height:40px; width:50%; border-radius:40px; color:white;">
    </form>
  </center>
</body>
</html>








	"""







@app.route("/reported", methods=["POST"])
def reported():
  reason = request.form.get("reason")
  url = request.form.get("url_report")
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("""UPDATE urls
    SET reported_status = ?, reason = ?
    WHERE link = ?""",("reported", reason, url,))
  conn.commit()
  conn.close()
  return redirect("/")








@app.route("/report", methods=['POST'])
def report():
  reported_url = request.form.get("url")
  return"""

<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Report Link - AliFi - Search Across The WEB</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #efb5ff;
      font-family: Arial, sans-serif;
    }

    .report-container {
      max-width: 600px;
      width: 90%;
      background-color: white;
      border-radius: 15px;
      margin: 50px auto;
      padding: 20px;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }

    input[type="text"],
    textarea,
    input[type="submit"] {
      width: 100%;
      padding: 15px;
      margin: 10px 0;
      border-radius: 10px;
      box-sizing: border-box;
      font-size: 16px;
    }

    input[type="text"] {
      border: 2px dashed red;
      border-top: none;
      border-left: none;
      border-right: none;
    }

    textarea {
      border: 2px dashed green;
      resize: vertical;
    }

    input[type="submit"] {
      border: 2px dashed red;
      background-color: white;
      cursor: pointer;
      transition: background-color 0.3s, color 0.3s;
    }

    input[type="submit"]:hover {
      background-color: red;
      color: white;
    }

    @media screen and (max-width: 480px) {
      .report-container {
        padding: 15px;
      }

      input[type="text"],
      textarea,
      input[type="submit"] {
        font-size: 14px;
        padding: 12px;
      }
    }
  </style>
</head>
<body>

  <form action="/reported" method="POST">
    <div class="report-container">
      <input type="text" placeholder="Reported URL" value='"""+reported_url+"""' name="url_report">
      <textarea placeholder="Reason for reporting..." name="reason" rows="5"></textarea>
      <input type="submit" value="Report URL">
    </div>
  </form>

</body>
</html>

"""




@app.route("/admin", methods=['POST'])
def admin():
    username=request.form.get("adminusername")
    password=request.form.get("adminpassword")
    session["username"]= username
    session["password"]= password
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM admins")
    user_pass = cursor.fetchall()
    for (user, passw) in user_pass:
        if user == username and passw == password:
        	session["logged_in"]="true"
        	conn.close()
        	return"""


<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi Console - Search Across The Internet!</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <meta name="description" content="Submit your website URL to be indexed by the AliFi search database. Fast, easy, and efficient.">
</head>
<body style="margin:0; padding:0; font-family: Arial, sans-serif;">


<table style="width:100%; height: 100px; background-color: #faf8be; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);">
<tr>
  <td>
    <img src="/logo" width="15%" align="left">
    <h1 align="center" style="font-family: lobster; color: #e3aa00; font-size: 35px;">
      Welcome To Admin Panel!
    </h1>
  </td>
</tr>
</table>






<center>
<table style="width:90%; position: relative; top:70px;">

  <tr>
    <td style="padding-right: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/deleteuser">
        <input type="Submit" value="Delete User" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
    <td style="padding-left: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/deletelink">
        <input type="Submit" value="Delete Link" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
  </tr>

  <tr>
    <td style="padding-right: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/topsearches">
        <input type="Submit" value="Top Searches" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
    <td style="padding-left: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/addlink">
        <input type="Submit" value="Add Link" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
  </tr>

  <tr>
    <td style="padding-right: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/addadv">
        <input type="Submit" value="Add Advert." style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
    <td style="padding-left: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/totalsearches">
        <input type="Submit" value="Total Searches" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
  </tr>

  <tr>
    <td style="padding-right: 10px; padding-bottom: 10px;" width="50%" colspan=2>
      <form method="POST" action="/reviewreports">
        <input type="Submit" value="Review Reports" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
    <td></td>
  </tr>

</table>
</center>






<div style="width:99.73%; height: 70px; background-color: #f7f7f7; border: 2px dashed black; position: relative; top: 130px;">
  
<p style="position:absolute; top :30%; left: 50%; transform:translate(-50%,-50%);">All The Copyrights (c) are reserved (2026) by <a href="https://github.com/MAliRaffayMirza/">Mirza M. Ali Raffay</a></p>

</div>





</body>
</html>


	"""
    conn.close()
    return redirect("/adminlogin")



@app.route("/deletelink", methods=['POST'])
def deletelink():
    h=""
    conn = sqlite3.connect("database.db")
    cursor=conn.cursor()
    cursor.execute("""SELECT link FROM urls WHERE status=="live" """)
    links = cursor.fetchall()
    for (linkt,) in links:
      h+="""<div class="user-row">
      <div class="username">"""+linkt+"""</div>
      <form method="POST" action="/deletelinkp">
        <input type="submit" name="""+linkt+""" value="Delete URL">
      </form>
    </div>"""
    conn.commit()
    conn.close()
    return"""


<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi Console - Delete USER Admin Panel</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f6bdff;
    }

    .container {
      width: 60%;
      margin: 50px auto;
      background-color: #fff;
      padding: 30px;
      border-radius: 16px;
      box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    }

    .form-row {
      display: flex;
      gap: 20px;
      margin-bottom: 30px;
    }

    .form-row input[type="text"] {
      flex: 1;
      height: 48px;
      padding-left: 12px;
      font-size: 18px;
      border: 2px dashed royalblue;
      border-radius: 8px;
    }

    .form-row input[type="submit"] {
      width: 180px;
      background-color: maroon;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }

    .form-row input[type="submit"]:hover {
      background-color: darkred;
    }

    .user-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding: 18px 20px;
      background-color: #ffffff;
      border-radius: 12px;
      font-size: 22px;
      font-family: Calibri, sans-serif;
      box-shadow: 0 0 5px rgba(0, 0, 0, 0.05);
    }

    .username {
      flex: 1;
      text-align: center;
    }

    .user-row form input[type="submit"] {
      width: 150px;
      height: 45px;
      background-color: white;
      border: 2px solid maroon;
      border-radius: 10px;
      font-weight: bold;
      color: maroon;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .user-row form input[type="submit"]:hover {
      background-color: maroon;
      color: white;
    }
  </style>
</head>
<body>

  <div class="container">

    <form method="POST" action="/deletelinkp">
      <div class="form-row">
        <input type="text" name="dellink" placeholder="Delete By URL">
        <input type="submit" value="Delete URL">
      </div>
    </form>"""+h+"""

  </div>

</body>
</html>



"""



@app.route("/admin", methods=['GET'])
def adminget():
    status = session.get("logged_in")
    if status == "true":
    	return"""

<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi Console - Search Across The Internet!</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <meta name="description" content="Submit your website URL to be indexed by the AliFi search database. Fast, easy, and efficient.">
</head>
<body style="margin:0; padding:0; font-family: Arial, sans-serif;">


<table style="width:100%; height: 100px; background-color: #faf8be; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);">
<tr>
  <td>
    <img src="/logo" width="15%" align="left">
    <h1 align="center" style="font-family: lobster; color: #e3aa00; font-size: 35px;">
      Welcome To Admin Panel!
    </h1>
  </td>
</tr>
</table>






<center>
<table style="width:90%; position: relative; top:70px;">

  <tr>
    <td style="padding-right: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/deleteuser">
        <input type="Submit" value="Delete User" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
    <td style="padding-left: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/deletelink">
        <input type="Submit" value="Delete Link" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
  </tr>

  <tr>
    <td style="padding-right: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/topsearches">
        <input type="Submit" value="Top Searches" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
    <td style="padding-left: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/addlink">
        <input type="Submit" value="Add Link" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
  </tr>

  <tr>
    <td style="padding-right: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/addadv">
        <input type="Submit" value="Add Advert." style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
    <td style="padding-left: 10px; padding-bottom: 10px;" width="50%">
      <form method="POST" action="/totalsearches">
        <input type="Submit" value="Total Searches" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
  </tr>

  <tr>
    <td style="padding-right: 10px; padding-bottom: 10px;" width="50%" colspan=2>
      <form method="POST" action="/reviewreports">
        <input type="Submit" value="Review Reports" style="width:100%; height: 40px; background-color: white; font-size: 20px; border: 3px dashed brown;">
      </form>
    </td>
    <td></td>
  </tr>

</table>
</center>






<div style="width:99.73%; height: 70px; background-color: #f7f7f7; border: 2px dashed black; position: relative; top: 130px;">
  
<p style="position:absolute; top :30%; left: 50%; transform:translate(-50%,-50%);">All The Copyrights (c) are reserved (2026) by <a href="https://github.com/MAliRaffayMirza/">Mirza M. Ali Raffay</a></p>

</div>





</body>
</html>


    	"""
    return redirect("/adminlogin")


@app.route("/admin", methods=['GET'])
def getadmin():
	return redirect("/adminlogin")



@app.route("/search-console", methods=["GET", "POST"])
def console():
    username= session.get("username")
    password= session.get("password")
    htmll = """


<center><div style="width:80%; min-height: 200px; background-color: white; border:3px dashed maroon; position: relative; top:230px;">
  <h1 style="font-size: 20px; font-family: arial;">URL Status</h1>


<table width="100%" style="text-align:left;">"""
    con = sqlite3.connect("database.db")
    cursor = con.cursor()
    cursor.execute("SELECT link, status from urls WHERE username = ?",(username,))
    url_info = cursor.fetchall()
    for (link, statuss) in url_info:
        htmll+="""<tr><td style="padding:10px;"><a href="""+link+">"+link+"</a></td><td>"+statuss+"</td></tr>"
    htmll+="</table></div></center>"
    con.commit()
    con.close()
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users")
    user_pass = cursor.fetchall()
    for (user, passw) in user_pass:
        if user == username and passw == password:
        	conn.close()
        	return"""


<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi Console - Search Across The Internet!</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <meta name="description" content="Submit your website URL to be indexed by the AliFi search database. Fast, easy, and efficient.">
</head>
<body style="margin:0; padding:0; font-family: Arial, sans-serif;">


<table style="width:100%; height: 100px; background-color: #faf8be; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);">
<tr>
  <td>
    <img src="/logo" width="15%" align="left">
    <h1 align="center" style="font-family: lobster; color: #00ab17; font-size: 35px;">
      Submit Your Page for Indexation
    </h1>
  </td>
</tr>
</table>


  <center>
    <div style="width:80%; height: 80px; background-color: white; border-radius: 20px; border: 3px dashed red; position: relative; top: 100px;">
      <div style="width: 100%; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
        <form method="POST" action="/urlsubmission">
          <input type="text" placeholder="Enter URL here" name="URL" style="width:72%; border-right: none; border-left: none; border-top: none; border-bottom: 2px solid red; height: 40px; padding-left: 10px; margin-right: 15px;" align="left">
          <input type="submit" value="Send URL" style="width:18%; height: 40px; border-radius: 12px; background-color: #005eff; color: white; font-family: arial; font-weight: bold; border:3px solid #ffb405;" align="right">
        </form>
      </div>
    </div>
  </center>


  <ol style="padding-left: 100px; position: relative; top: 170px; font-size: 18px; line-height: 2;">
    <li>Submit your website's link.</li>
    <li>We will receive it.</li>
    <li>Our Bot will check the content against our quality standards.</li>
    <li>Your URL will be indexed in our search database</li>
  </ol>"""+htmll+"""


  <div style="width:100%; height: 65px; position: relative; top: 250px; border-right: none; border-left: none; border-bottom: none; border-top: 3px dotted maroon; background-color: #f5f5f5;">
    <p style="position:absolute; top: 30%; left: 50%; transform: translate(-50%, -50%);">
      All The Copyrights (c) are reserved (2026) by 
      <a href="https://github.com/MAliRaffayMirza/">Mirza M. Ali Raffay</a>
    </p>
  </div>

</body>
</html>


	"""
    conn.close()
    return redirect("/login")




@app.route("/login", methods=["GET"])
def login():
  session.clear()
  return"""

<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Login - AliFi Search Across The Internet!</title>
  <link rel="icon" type="image/x-icon" href="/fav">
</head>
<body bgcolor="#e6f2ff">

<table width="100%">
  <tr>
    <td align="right" style="padding: 10px;">
      <form method="GET" action="/signup" style="display:inline;">
        <input type="submit" value="Sign Up"
          style="width: 150px; height: 35px; border: 2px solid royalblue; background-color: #05038c; color: white; font-family: calibri; font-size: 16px; font-weight: bold; border-radius: 8px;">
      </form>
      <form method="GET" action="/recover-password" style="display:inline; margin-left: 10px;">
        <input type="submit" value="Recover Password"
          style="width: 180px; height: 35px; border: 2px solid royalblue; background-color: #05038c; color: white; font-family: calibri; font-size: 16px; font-weight: bold; border-radius: 8px;">
      </form>
    </td>
  </tr>
</table>

<br><br><br>

<center>
  <h1 style="color: #003366; font-family: Arial;">Please enter Log In details below:</h1>

  <div style="margin-top: 20px; margin-bottom: 30px; padding: 15px; background-color: #ffffff; width: 50%; border: 2px dashed #3399ff; border-radius: 20px; font-family: Arial; color: #003366;">
    <h3>🔐 Test Credentials</h3>
    <p><b>Username:</b> <code style="background-color: #eef; padding: 2px 8px; border-radius: 6px;">admin</code></p>
    <p><b>Password:</b> <code style="background-color: #eef; padding: 2px 8px; border-radius: 6px;">admin</code></p>
  </div>
  <form method="POST" action="/loggedin">
    <input name="username" placeholder="Enter Username" 
      style="width:50%; height:40px; font-size:16px; border:2px solid #3399ff; background-color:white; border-radius:14px; padding:8px;">
    <br><br>
    <input name="password" type="password" placeholder="Enter Password" 
      style="width:50%; height:40px; font-size:16px; border:2px solid #3399ff; background-color:white; border-radius:14px; padding:8px;">
    <br><br>
    <input type="submit" value="Log In" 
      style="background-color:#3366cc; font-family:bahnschrift; font-size:16px; font-weight:bold; border:none; height:40px; width:50%; border-radius:40px; color:white;">
  </form>
</center>

</body>
</html>

"""




@app.route("/signup")
def signup():
	max_birthdate = date.today().replace(year=date.today().year - 18)
	return"""

<head>
  <link rel="icon" type="image/x-icon" href="/fav"><title>Sign Up - AliFi Search Accross The Internet!</title></head>
	<body bgcolor="#00f7ff">
    <form method="GET" action="/login" align="right">
      <input type="submit" value="Login"
        style="width: 20%; height: 35px; border: 2px solid royalblue; background-color: #05038c; color: white; font-family: calibri; font-size: 16px; font-weight: bold; border-radius: 8px;">
    </form>
  <center>
    <h1 style="font-family: lobster; color: #05038c;">Sign Up</h1><br>

    <form method="POST" action="/signups">

      <table width="50%" border="0">
        <tr>
          <td style="border: none;">
            <input name="username" placeholder="Username"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
          <td style="border: none;">
            <input name="password" placeholder="Password" type="password"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>

      <table width="50%" border="0">
        <tr>
          <td>
            <input name="email" placeholder="Email"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>


      <table width="50%" border="0">
        <tr>
          <td>
            <input name="name" placeholder="Full Name"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>


      <table width="50%" border="0">
        <tr>
          <td>
            <input name="secq" placeholder="Security Question"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
          <td>
            <input name="seca" placeholder="Security Answer"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>


      <table width="50%" border="0">
        <tr>
          <td>
            <input name="phone" placeholder="Phone Number"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>


      <table width="50%" border="0">
        <tr>
          <td>
            <label for="birthdate" style="font-family: calibri; font-size: 16px; color: #05038c;">Birthdate:</label><br>
            <input type="date" name="birthdate" id="birthdate"
              max="""+str(max_birthdate)+""" style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>


      <input type="submit" value="Sign Up"
        style="width: 50%; height: 40px; border: 3px solid royalblue; background-color: orange; color: white; font-family: calibri; font-size: 18px; font-weight: bold; border-radius: 10px;">
    </form>
  </center>
</body>
"""





@app.route("/recover-password", methods=["GET"])
def forget():
	return"""

<head>
  <link rel="icon" type="image/x-icon" href="/fav"><title>Recover Password - AliFi Search Accross The Internet!</title></head>
  

<body bgcolor="#e6f2ff">

<table width="100%">
  <tr>
    <td align="right">
      <form method="GET" action="/signup" style="display:inline;">
        <input type="submit" value="Sign Up"
          style="width: 15%; height: 35px; border: 2px solid royalblue; background-color: #05038c; color: white; font-family: calibri; font-size: 16px; font-weight: bold; border-radius: 8px;">
      </form>
      <form method="GET" action="/login" style="display:inline;">
        <input type="submit" value="Login"
          style="width: 15%; height: 35px; border: 2px solid royalblue; background-color: #05038c; color: white; font-family: calibri; font-size: 16px; font-weight: bold; border-radius: 8px;">
      </form>
    </td>
  </tr>
</table>
  <br><br><br>
  <center>
    <h1 style="color: #003366; font-family: Arial;">Forgot Password?</h1>
    <br>
    <form method="POST" action="/recovered">
      <input name="email" placeholder="Enter Email" 
        style="width:50%; height:40px; font-size:16px; border:2px solid #3399ff; background-color:white; border-radius:14px; padding:8px;">
      <br><br>
      <input name="secq" placeholder="Enter Security Question" 
        style="width:50%; height:40px; font-size:16px; border:2px solid #3399ff; background-color:white; border-radius:14px; padding:8px;">
      <br><br>
      <input name="seca" placeholder="Enter Answer" 
        style="width:50%; height:40px; font-size:16px; border:2px solid #3399ff; background-color:white; border-radius:14px; padding:8px;">
      <br><br>
      <input name="phone" placeholder="Enter Phone Number" 
        style="width:50%; height:40px; font-size:16px; border:2px solid #3399ff; background-color:white; border-radius:14px; padding:8px;">
      <br><br>
      <input type="submit" value="Get Password" 
        style="background-color:#3366cc; font-family:bahnschrift; font-size:16px; font-weight:bold; border:none; height:40px; width:50%; border-radius:40px; color:white;">
    </form>
  </center>
</body>




	"""


@app.route("/signups", methods=["POST"])
def signups():
    symbolex = "!@#$%^&*():;',.<>/?|`~+-="
    status = "live"
    symbol = "!@#$%^&*()_-:;',.<>/?|`~+-="
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    secq = request.form.get("secq")
    seca = request.form.get("seca")
    phone = request.form.get("phone")
    name = request.form.get("name")
    birthdate = request.form.get("birthdate")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT,
            password TEXT,
            email TEXT,
            name TEXT,
            sec_question TEXT,
            sec_answer TEXT,
            phone TEXT,
            birthdate TEXT
        );
    """)

    cursor.execute("SELECT username FROM users")
    usernames = cursor.fetchall()
    for (existingusername,) in usernames:
        if existingusername == username:
            return errorpage("Username Already Exists")

    cursor.execute("SELECT email FROM users")
    emails = cursor.fetchall()
    for (existingemail,) in emails:
        if existingemail == email:
            return errorpage("Email Already Exists")

    cursor.execute("SELECT phone FROM users")
    phones = cursor.fetchall()
    for (existingphone,) in phones:
        if existingphone == phone:
            return errorpage("Phone Record Already Exists")

    if sum(char in symbolex for char in username) == 0 and len(username) >= 5 and sum(char in password for char in symbol) >= 3 and len(password) >= 10:
        cursor.execute("""
            INSERT INTO users(username, password, email, name, sec_question, sec_answer, phone, birthdate, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, password, email, name, secq, seca, phone, birthdate, status))
        conn.commit()
        conn.close()
        return errorpage("You're successfully signed up!")
    elif sum(char in symbolex for char in username) == 0 and len(username) >= 5:
        return errorpage("Use a stronger Password!")
    elif sum(char in password for char in symbol) >= 3 and len(password) >= 10:
        return errorpage("Sorry your Username contains a special character!")
    else:
        return errorpage("Both the username and password are incorrect, choose something else!")







def errorpage(errortype):

	max_birthdate = date.today().replace(year=date.today().year - 18)
	return"""

<head>
  <link rel="icon" type="image/x-icon" href="/fav"><title>Sign Up - AliFi Search Accross The Internet!</title></head>
  
	<body bgcolor="#00f7ff">
    <form method="GET" action="/login" align="right">
      <input type="submit" value="Login"
        style="width: 20%; height: 35px; border: 2px solid royalblue; background-color: #05038c; color: white; font-family: calibri; font-size: 16px; font-weight: bold; border-radius: 8px;">
    </form>
  <center>
    <h1 style="font-family: lobster; color: #05038c;">Sign Up</h1><br>
   <div style="width: 50%; border: 0.5px solid #ff8645; border-radius: 10px; background-color: #f5dacb; min-height:30px; text-align:center; padding-top:10px; text-align: center;">"""+errortype+"""</div><br>
</br>
    <form method="POST" action="/signups">

      <table width="50%" border="0">
        <tr>
          <td style="border: none;">
            <input name="username" placeholder="Username"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
          <td style="border: none;">
            <input name="password" placeholder="Password" type="password"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>

      <table width="50%" border="0">
        <tr>
          <td>
            <input name="email" placeholder="Email"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>

      <table width="50%" border="0">
        <tr>
          <td>
            <input name="name" placeholder="Full Name"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>

      <table width="50%" border="0">
        <tr>
          <td>
            <input name="secq" placeholder="Security Question"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
          <td>
            <input name="seca" placeholder="Security Answer"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>

      <table width="50%" border="0">
        <tr>
          <td>
            <input name="phone" placeholder="Phone Number"
              style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>

      <table width="50%" border="0">
        <tr>
          <td>
            <label for="birthdate" style="font-family: calibri; font-size: 16px; color: #05038c;">Birthdate:</label><br>
            <input type="date" name="birthdate" id="birthdate"
              max="""+str(max_birthdate)+""" style="width: 100%; height: 40px; padding: 10px; border: 3px solid royalblue; border-radius: 10px;">
          </td>
        </tr>
      </table>
      <br>
<input type="submit" value="Sign Up"
        style="width: 50%; height: 40px; border: 3px solid royalblue; background-color: orange; color: white; font-family: calibri; font-size: 18px; font-weight: bold; border-radius: 10px;">
    </form>
  </center>
</body>"""




@app.route("/loggedin", methods=["POST"])
def loggedin():
    username = request.form.get("username")
    password = request.form.get("password")
    session["username"]=username
    session["password"]=password  
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, status FROM users")
    user_pass = cursor.fetchall()
    for (user, passw, status) in user_pass:
        if user == username and passw == password and status == "live":
            conn.close()
            return redirect("/")
    conn.close()
    return redirect("/login")



@app.route("/recovered", methods=["POST"])
def recoveredpass():
    email= request.form.get("email")
    secq= request.form.get("secq")
    seca= request.form.get("seca")
    phone= request.form.get("phone")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email =?",(email,))
    information = cursor.fetchall()
    for (usernamee,passe,emaile,namee,secqe,secae,phonee,birthdatee) in information:
        if emaile==email and secqe==secq and secae==seca and phonee == phone:
            conn.close()
            return """<!DOCTYPE html>
<html>
<head>
<link rel="icon" type="image/x-icon" href="/fav">
<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>PASSWORD - AliFi - Search Accross The Web</title>
</head>
<body bgcolor="gold">
<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width:70%; min-height: 100px; border-radius: 30px; background-color: white;">
	<h2 align="center" style="font-family:arial;">PASSWORD:</h2>
	<center><p style="font-family: arial; font-size: 25px;">"""+passe+"""</p></center>
</div>
</body>
</html>"""
    conn.close()
    return redirect("/recover-password")







@app.route("/urlsubmission", methods=["POST"])
def urlsubmission():
    username = session.get("username")
    url = request.form.get("URL")
    status = "live"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "No title"
    desc = soup.find("meta", attrs={"name": "description"})
    description = desc["content"] if desc else "No description"
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
CREATE TABLE IF NOT EXISTS urls(link TEXT UNIQUE,title TEXT,meta TEXT,username TEXT,status TEXT)
""")
    cursor.execute("""
INSERT INTO urls(link,title,meta,username,status)
VALUES(?,?,?,?,?)""",
(url, title, description, username, status))
    conn.commit()
    conn.close()
    return redirect("/search-console")










@app.route("/urlsubmissionadmin", methods=["POST"])
def urlsubmissionadmin():
    status = session.get("logged_in")
    if status == "true":
      status = "live"
      html = requests.get(url).text
      soup = BeautifulSoup(html, "html.parser")
      title = soup.title.string if soup.title else "No title"
      desc = soup.find("meta", attrs={"name": "description"})
      description = desc["content"] if desc else "No description"
      conn = sqlite3.connect("database.db")
      cursor = conn.cursor()
      cursor.execute("""
CREATE TABLE IF NOT EXISTS urls(link TEXT UNIQUE,title TEXT,meta TEXT,username TEXT,status TEXT)
""")
      cursor.execute("""
INSERT INTO urls(link,title,meta,username,status)
VALUES(?,?,?,?,?)""",
(url, title, description, "Admin", status))
      conn.commit()
      conn.close()
    return redirect("/admin")






@app.route("/deleteuser", methods=['POST'])
def deleteuser():
    h=""
    conn = sqlite3.connect("database.db")
    cursor=conn.cursor()
    cursor.execute("""SELECT username FROM users WHERE status=="live" """)
    usernames = cursor.fetchall()
    for (usernamet,) in usernames:
	    h+="""<div class="user-row">
      <div class="username">"""+usernamet+"""</div>
      <form method="POST" action="/deleteuserp">
        <input type="submit" name="""+usernamet+""" value="Delete USER">
      </form>
    </div>"""
    conn.commit()
    conn.close()
    return"""


<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi Console - Delete USER Admin Panel</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f6bdff;
    }

    .container {
      width: 60%;
      margin: 50px auto;
      background-color: #fff;
      padding: 30px;
      border-radius: 16px;
      box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    }

    .form-row {
      display: flex;
      gap: 20px;
      margin-bottom: 30px;
    }

    .form-row input[type="text"] {
      flex: 1;
      height: 48px;
      padding-left: 12px;
      font-size: 18px;
      border: 2px dashed royalblue;
      border-radius: 8px;
    }

    .form-row input[type="submit"] {
      width: 180px;
      background-color: maroon;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }

    .form-row input[type="submit"]:hover {
      background-color: darkred;
    }

    .user-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding: 18px 20px;
      background-color: #ffffff;
      border-radius: 12px;
      font-size: 22px;
      font-family: Calibri, sans-serif;
      box-shadow: 0 0 5px rgba(0, 0, 0, 0.05);
    }

    .username {
      flex: 1;
      text-align: center;
    }

    .user-row form input[type="submit"] {
      width: 150px;
      height: 45px;
      background-color: white;
      border: 2px solid maroon;
      border-radius: 10px;
      font-weight: bold;
      color: maroon;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .user-row form input[type="submit"]:hover {
      background-color: maroon;
      color: white;
    }
  </style>
</head>
<body>

  <div class="container">
    <form method="POST" action="/deleteuserp">
      <div class="form-row">
        <input type="text" name="deluser" placeholder="Delete by USERNAME">
        <input type="submit" value="Delete USER">
      </div>
    </form>"""+h+"""

  </div>

</body>
</html>



"""
    return redirect("/adminlogin")





@app.route("/deleteuser", methods=['GET'])
def deleteusers():
    status = session.get("logged_in")
    h=""
    conn = sqlite3.connect("database.db")
    cursor=conn.cursor()
    cursor.execute("""SELECT username FROM users WHERE status=="live" """)
    usernames = cursor.fetchall()
    for (usernamet,) in usernames:
	    h+="""<div class="user-row">
      <div class="username">"""+usernamet+"""</div>
      <form method="POST" action="/deleteuserp">
        <input type="submit" name="""+usernamet+""" value="Delete USER">
      </form>
    </div>"""
    conn.commit()
    conn.close()
    if status == "true":
    	return"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi Console - Delete USER Admin Panel</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f6bdff;
    }

    .container {
      width: 60%;
      margin: 50px auto;
      background-color: #fff;
      padding: 30px;
      border-radius: 16px;
      box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    }

    .form-row {
      display: flex;
      gap: 20px;
      margin-bottom: 30px;
    }

    .form-row input[type="text"] {
      flex: 1;
      height: 48px;
      padding-left: 12px;
      font-size: 18px;
      border: 2px dashed royalblue;
      border-radius: 8px;
    }

    .form-row input[type="submit"] {
      width: 180px;
      background-color: maroon;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }

    .form-row input[type="submit"]:hover {
      background-color: darkred;
    }

    .user-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding: 18px 20px;
      background-color: #ffffff;
      border-radius: 12px;
      font-size: 22px;
      font-family: Calibri, sans-serif;
      box-shadow: 0 0 5px rgba(0, 0, 0, 0.05);
    }

    .username {
      flex: 1;
      text-align: center;
    }

    .user-row form input[type="submit"] {
      width: 150px;
      height: 45px;
      background-color: white;
      border: 2px solid maroon;
      border-radius: 10px;
      font-weight: bold;
      color: maroon;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .user-row form input[type="submit"]:hover {
      background-color: maroon;
      color: white;
    }
  </style>
</head>
<body>

  <div class="container">

    <form method="POST" action="/deleteuserp">
      <div class="form-row">
        <input type="text" name="deluser" placeholder="Delete by USERNAME">
        <input type="submit" value="Delete USER">
      </div>
    </form>"""+h+"""

  </div>

</body>
</html>


    	"""
    return redirect("/adminlogin")

@app.route("/deleteuserp", methods=["POST"])
def deleteuserp():
    username = request.form.get("deluser")
    for key in request.form.keys():
        if request.form.get(key) == "Delete USER":
            username = key
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""UPDATE users SET status ="suspended" WHERE username = ?""",(username,))
    conn.commit()
    conn.close()
    return redirect("/deleteuser")



@app.route("/deletelinkp", methods=["POST"])
def deletelinkp():
    url = request.form.get("dellink")
    for key in request.form.keys():
        if request.form.get(key) == "Delete URL":
            url = key
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""UPDATE urls SET status ="suspended" WHERE link = ?""",(url,))
    conn.commit()
    conn.close()
    return redirect("/admin")






@app.route("/deletelinkpp", methods=["POST"])
def deletelinkpp():
    url = request.form.get("dellink")
    for key in request.form.keys():
        if request.form.get(key) == "Delete URL":
            url = key
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""UPDATE urls SET status ="suspended", reported_status="deleted" WHERE link = ?""",(url,))
    conn.commit()
    conn.close()
    return redirect("/admin")



@app.route("/deletelinka", methods=["POST"])
def deletelinka():
  for key in request.form.keys():
    if request.form.get(key) == "Restore URL":
      url = key
      conn = sqlite3.connect("database.db")
      cursor = conn.cursor()
      cursor.execute("""UPDATE urls SET reported_status ="clear" WHERE link = ?""",(url,))
      conn.commit()
      conn.close()
  return redirect("/admin")














@app.route("/addlink", methods=['POST'])
def addlink():
  status = session.get("logged_in")
  if status == "true":
    return """
  <!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi Console - Search Across The Internet!</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <meta name="description" content="Submit your website URL to be indexed by the AliFi search database. Fast, easy, and efficient.">
</head>
<body style="margin:0; padding:0; font-family: Arial, sans-serif;">


<table style="width:100%; height: 100px; background-color: #faf8be; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);">
<tr>
  <td>
    <img src="/logo" width="15%" align="left">
    <h1 align="center" style="font-family: lobster; color: #00ab17; font-size: 35px;">
      Index Page, Admin!
    </h1>
  </td>
</tr>
</table>

  <center>
    <div style="width:80%; height: 80px; background-color: white; border-radius: 20px; border: 3px dashed red; position: relative; top: 100px;">
      <div style="width: 100%; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
        <form method="POST" action="/urlsubmission">
          <input type="text" placeholder="Enter URL here" name="URL" style="width:72%; border-right: none; border-left: none; border-top: none; border-bottom: 2px solid red; height: 40px; padding-left: 10px; margin-right: 15px;" align="left">
          <input type="submit" value="Send URL" style="width:18%; height: 40px; border-radius: 12px; background-color: #005eff; color: white; font-family: arial; font-weight: bold; border:3px solid #ffb405;" align="right">
        </form>
      </div>
    </div>
  </center>

  <div style="width:100%; height: 65px; position: relative; top: 250px; border-right: none; border-left: none; border-bottom: none; border-top: 3px dotted maroon; background-color: #f5f5f5;">
    <p style="position:absolute; top: 30%; left: 50%; transform: translate(-50%, -50%);">
      All The Copyrights (c) are reserved (2026) by 
      <a href="https://github.com/MAliRaffayMirza/">Mirza M. Ali Raffay</a>
    </p>
  </div>

</body>
</html>
"""








@app.route("/totalsearches", methods=['POST'])
def totalsearches():
  totalqueries = 0
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("""SELECT count FROM searches""")
  total = cursor.fetchall()
  for (count,) in total:
    totalqueries+=int(count)
  status = session.get("logged_in")
  if status == "true":
    return """<!DOCTYPE html>
<html>
<head>
<link rel="icon" type="image/x-icon" href="/fav">
  <meta charset="UTF-8">
  <title>Total Searches</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #f3f3f3;
      text-align: center;
      margin-top: 100px;
    }
    .box {
      display: inline-block;
      padding: 30px 50px;
      background-color: white;
      border: 2px dashed maroon;
      font-size: 24px;
      font-weight: bold;
      color: #333;
      border-radius: 10px;
    }
  </style>
</head>
<body>

<div class="box">
  Total Searches: &nbsp; &nbsp;"""+str(totalqueries)+"""
</div>

</body>
</html>

"""





@app.route("/reviewreports", methods=['POST'])
def reviewreports():
  status = session.get("logged_in")
  if status == "true":
    h=""
    conn = sqlite3.connect("database.db")
    cursor=conn.cursor()
    cursor.execute("""SELECT link FROM urls WHERE reported_status=="reported" """)
    links = cursor.fetchall()
    for (linkt,) in links:
      h+="""<div class="user-row">
      <div class="username">"""+linkt+"""</div>
      <form method="POST" action="/deletelinkpp">
        <input type="submit" name="""+linkt+""" value="Delete URL">
      </form> &nbsp;<form align="right" method="POST" action="/deletelinka">
        <input type="submit" name="""+linkt+""" value="Restore URL">
      </form>
    </div>"""
    conn.commit()
    conn.close()
    return"""


<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AliFi Console - Delete USER Admin Panel</title>
  <link rel="icon" type="image/x-icon" href="/fav">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f6bdff;
    }

    .container {
      width: 80%;
      margin: 50px auto;
      background-color: #fff;
      padding: 30px;
      border-radius: 16px;
      box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    }

    .form-row {
      display: flex;
      gap: 20px;
      margin-bottom: 30px;
    }

    .form-row input[type="text"] {
      flex: 1;
      height: 48px;
      padding-left: 12px;
      font-size: 18px;
      border: 2px dashed royalblue;
      border-radius: 8px;
    }

    .form-row input[type="submit"] {
      width: 180px;
      background-color: maroon;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
      transition: background-color 0.3s ease;
    }

    .form-row input[type="submit"]:hover {
      background-color: darkred;
    }

    .user-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding: 18px 20px;
      background-color: #ffffff;
      border-radius: 12px;
      font-size: 22px;
      font-family: Calibri, sans-serif;
      box-shadow: 0 0 5px rgba(0, 0, 0, 0.05);
    }

    .username {
      flex: 1;
      text-align: center;
    }

    .user-row form input[type="submit"] {
      width: 150px;
      height: 45px;
      background-color: white;
      border: 2px solid maroon;
      border-radius: 10px;
      font-weight: bold;
      color: maroon;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .user-row form input[type="submit"]:hover {
      background-color: maroon;
      color: white;
    }
  </style>
</head>
<body>

  <div class="container">
    """+h+"""

  </div>

</body>
</html>



"""
  return redirect("/adminlogin")




@app.route("/topsearches", methods=['POST'])
def topsearches():
  h="""<!DOCTYPE html>
<html>
<head>
<link rel="icon" type="image/x-icon" href="/fav">
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Report Link - AliFi - Search Across The WEB</title>
<body bgcolor="#c7fff8">


<table style="width:80%; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-family: calibri; font-size: 20px; padding: 20px; border: 3px dashed maroon; border-radius: 30px; background-color: white;"><tr><td width="70%"><b>Keyword</b></td><td width="30%"><b>Search Volume</b></td></tr>"""
  conn = sqlite3.connect("database.db")
  cursor = conn.cursor()
  cursor.execute("""SELECT * FROM searches
ORDER BY count DESC""")
  data = cursor.fetchall()
  for (keyword, count) in data:
    h+="""
<tr><td width="70%">"""+keyword+"""</td><td width="30%">"""+str(count)+"""</td></tr>
    """
  h+="""</table></body></html>"""
  return h



@app.route("/addadv", methods=["POST"])
def addadv():
    html = ""
    with open("ads.txt", "r", encoding="utf-8") as file:
        ads = file.readlines()
    
    for i in ads:
        ad = i.strip().split("^")
        title, url, meta = ad[0], ad[1], ad[2]
        
        html += f"""
        <div style="width: 80%; margin: 15px auto; padding: 20px; background-color: #f9f9f9;
                    border: 2px solid #ddd; border-left: 6px solid #4CAF50; border-radius: 12px;
                    font-family: Arial, sans-serif; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h2 style="color: #333; margin-bottom: 10px;">{title}</h2>
            <p><strong>URL:</strong> <a href="{url}" target="_blank" style="color: #1a73e8;">{url}</a></p>
            <p><strong>Meta:</strong> {meta}</p>
            <form method="POST" action="/remad" style="margin-top: 15px;">
                <input type="submit" value="Delete AD" name="{url}"
                       style="background-color: #e53935; color: white; border: none;
                              padding: 10px 20px; border-radius: 8px; font-weight: bold;
                              cursor: pointer; transition: background-color 0.3s;">
            </form>
        </div>
        """
    
    return """<!DOCTYPE html>
<html>
<head>
  
  <link rel="icon" type="image/x-icon" href="/fav">
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Manage Ads - AliFi</title>
  <style>
    body {
      background-color: #c7fff8;
      margin: 0;
      font-family: Calibri, Arial, sans-serif;
    }

    .form-container {
      width: 70%;
      margin: 30px auto;
      padding: 25px;
      background-color: white;
      border-radius: 12px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    .form-container input,
    .form-container textarea {
      width: 90%;
      height: 40px;
      background-color: white;
      border: 2px solid black;
      padding-left: 20px;
      margin-bottom: 15px;
      font-size: 16px;
    }

    .form-container textarea {
      height: 140px;
      resize: none;
      padding-top: 10px;
    }

    .form-container input[type="submit"] {
      width: 93%;
      height: 45px;
      border-radius: 6px;
      background-color: #f1f1f1;
      border: 2px dashed black;
      font-weight: bold;
      cursor: pointer;
      transition: background-color 0.3s;
    }

    .form-container input[type="submit"]:hover {
      background-color: #e0e0e0;
    }

    .ads-heading {
      text-align: center;
      color: orangered;
      margin-top: 40px;
    }

    .ad-card {
      width: 80%;
      margin: 20px auto;
      padding: 20px;
      background-color: #f9f9f9;
      border: 2px solid #ddd;
      border-left: 6px solid #4CAF50;
      border-radius: 12px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    .ad-card h2 {
      margin-bottom: 10px;
      color: #333;
    }

    .ad-card a {
      color: #1a73e8;
      text-decoration: none;
    }

    .ad-card form {
      margin-top: 15px;
    }

    .ad-card input[type="submit"] {
      background-color: #e53935;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      font-weight: bold;
      cursor: pointer;
      transition: background-color 0.3s;
    }

    .ad-card input[type="submit"]:hover {
      background-color: #c62828;
    }
  </style>
</head>
<body>
<center>
  <div class="form-container">
    <form method="POST" action="/addad">
      <input name="title" placeholder="Title of AD" required><br>
      <input name="url" placeholder="Advertisement URL" required><br>
      <textarea name="meta" placeholder="Meta Description" required></textarea><br>
      <input type="submit" value="Add Ad">
    </form>
  </div>
</center>
  <h1 class="ads-heading">Existing Advertisement(s)</h1>"""+html+"""

</body>
</html>"""




@app.route("/addad", methods=['POST'])
def addad():
  title = request.form.get("title")
  url = request.form.get("url")
  meta = request.form.get("meta")
  with open("ads.txt", "a") as file:
    file.write(title+"^"+url+"^"+meta+"\n")
  return redirect("/admin")




@app.route("/remad", methods=['POST'])
def remad():
  listss=[]
  for key in request.form.keys():
    if request.form.get(key) == "Delete AD":
      url = key
  with open("ads.txt", "r", encoding="utf-8") as file:
    allinfo = file.readlines()
  for i in allinfo:
    ad = i.strip().split("^")
    if ad[1] != url:
      listss.append(i)
  with open("ads.txt", "w", encoding="utf-8") as file:
    file.writelines(listss)
  return redirect("/admin")

if __name__ == "__main__":

	app.run(debug=True)
