from dotenv import load_dotenv
import os
import base64
import requests
import json
import scipy

load_dotenv()

tokenURL = "https://accounts.spotify.com/api/token"
clientID = os.getenv("clientID")
clientSecret = os.getenv("clientSecret")

def getToken(tokenURL : str, clientID : str, clientSecret : str) -> str :
    authString = clientID + ':' + clientSecret
    authBytes = authString.encode("utf-8")
    authBase64 = str(base64.b64encode(authBytes), "utf-8")
    headers = {
        "Authorization" : "basic " + authBase64,
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type" : "client_credentials"
    }
    
    r = requests.post(url=tokenURL, headers=headers, data=data)
    json_result = json.loads(r.content)
    print(f"Status Code : {r.status_code}")
    print(f"Expires in : {json_result["expires_in"]} secs")
    
    token = json_result["access_token"]
    return token

def generate_auth_header(token : str) -> dict :
    return {"Authorization" : "Bearer " + token}

def get_data(authtoken : str, search_type : str, search_param : str = None ) -> dict :
    '''
    token : str -> auth token
    search_type : str -> object type from [artists, tracks, albums, genres, categories]
    search_param : str -> object ID/URI 
    '''
    base_URL = "https://api.spotify.com/v1/"
    query_URL = base_URL + search_type + '/' + search_param
    header = generate_auth_header(authtoken)
    
    r = requests.get(url=query_URL, headers=header)
    json_result = json.loads(r.content)
    print(f"Status Code : {r.status_code}")
    
    return json_result
    
    
token = getToken(tokenURL, clientID, clientSecret)
print(f"Token : {token}")
result = get_data(token, "artists", "4xRYI6VqpkE3UwrDrAZL8L")
print(result)
