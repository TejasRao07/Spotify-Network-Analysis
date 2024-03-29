from API import SpotifyAPI
import requests
import networkx as nx
from collections import Counter


def batch(nodes : list, batch_size : int) -> list :
    '''nodes : list of all track object IDs from a network
    batch_size() : Size of each batch, maxsize = 50 
    '''
    batches = []
    batch_size = batch_size if batch_size < 50 else 50      #force size to 50
    for i in range(0, len(nodes), batch_size) :
        batches.append(','.join(nodes[i : i + batch_size]))
    return batches

def node_batch(G : nx.graph, batch_size : int, type : str = "tracks") -> list :
    '''Takes a graph as input, extracts object ID from URIs and creates batches
    to be used for batch API query. Batches are comma separated object IDs
    G : graph -> Input graph
    type : str -> tracks/artist/albums/playlists -> creates batch based on object type
    type = "{object}" will create a batch based on {object} URIs 
    '''
    nodeList = []
    if(type == "tracks") :
        for node in G.nodes(data = False) :
            nodeList.append(node.split(":")[-1])
    elif(type == "artists") :
        for node, attrs in G.nodes(data = True) :
            for attr, val in attrs.items() :
                if(attr == "Artist URI") :
                    nodeList.append(val.split(":")[-1])
    elif(type == "albums") :
        for node, attrs in G.nodes(data = True) :
            for attr, val in attrs.items() :
                if(attr == "Album URI") :
                    nodeList.append(val.split(":")[-1])
    elif(type == "playlists") :
        for node, attrs in G.nodes(data = True) :
            for attr, val in attrs.items() :
                if(attr == "Playlist URI") :
                    nodeList.append(val.split(":")[-1])
        
    trackBatch = batch(nodeList, batch_size)
    
    return trackBatch

def get_track_details(batches : list, api_object, token : str) -> dict :
    '''
    Take a batch as input and query the 'tracks' endpoint to get details
    token : str -> Oauth token
    return : dict with details for all tracks in the batch
    '''
    if(len(batches) == 0) :
        return None
    
    details = []
    for batch in batches :
        try:
            query = "ids=" + batch
            data = api_object.get_data(token, 'tracks', query, batch=True)
            details.append(data)
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Handle HTTP errors
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")  # Handle connection errors
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")  # Handle timeout errors
        except ValueError as json_err:
            print(f"JSON decode error: {json_err}")  # Handle JSON parsing errors
        except Exception as err:
            print(f"An unexpected error occurred: {err}")  # Handle other unexpected errors

    return details

def update_track_attributes(G : nx.Graph, track_details : dict) -> None :
    track_details_dict = {}
    for details in track_details :
        for track in details['tracks'] :
            new_dict = {
                track["uri"]: {
                    "popularity": track["popularity"],
                    "duration_ms": track["duration_ms"],
                    "arist_URI" : track['artists'][0]['uri']
                }
            }
            track_details_dict.update(new_dict)
    nx.set_node_attributes(G, track_details_dict)
    return
         

def get_audio_features(batches : list, api_object, token : str) -> dict :
    '''
    Take a batch as input and query the 'tracks' endpoint to get audio features
    token : str -> Oauth token
    return : dict with audio features for all tracks in the batch
    '''
    if(len(batches) == 0) :
        return None
    
    features = []
    for batch in batches :
        try:
            query = "ids=" + batch
            data = api_object.get_data(token, 'audio-features', query, batch=True)
            features.append(data)
        except Exception as err:
            print(f"An unexpected error occurred: {err}")  # Handle other unexpected errors

    return features

def update_audio_attributes(G : nx.Graph, audio_features : dict) -> None :
    audio_features_dict = {}
    # List of keys to include in the value dictionary.
    keys_to_include = ["acousticness", "danceability", "duration_ms", "energy",
                    "instrumentalness", "key", "liveness", "loudness", "mode",
                    "speechiness", "tempo", "time_signature", "valence"]
    for features in audio_features :
        for feature in features['audio_features'] :
            new_dict = {
                feature['uri'] : {key : feature[key] for key in keys_to_include}
            }
            audio_features_dict.update(new_dict)
            
    nx.set_node_attributes(G, audio_features_dict)
    
    return

def get_artist_details(batches : list, api_object, token : str) -> dict :
    '''
    Take a batch as input and query the 'artists' endpoint to get genre and other artist details
    token : str -> Oauth token
    return : dict with audio features for all tracks in the batch
    '''
    if(len(batches) == 0) :
        return None
    
    features = []
    for batch in batches :
        try:
            query = "ids=" + batch
            data = api_object.get_data(token, 'artists', query, batch=True)
            features.append(data)
        except Exception as err:
            print(f"An unexpected error occurred: {err}")  # Handle other unexpected errors

    return features

def update_artist_details(G : nx.Graph, artist_details : dict, top_genres : list) -> None :
    artist_details_dict = {}
    for artists in artist_details :
        for artist in artists['artists'] :
            new_dict = {
                artist["uri"]: {
                    "artist_popularity": artist["popularity"],
                    "genres": artist["genres"]
                }
            }
            artist_details_dict.update(new_dict)
    
    for node, attrs in G.nodes(data=True) :
        for artist_uri in list(artist_details_dict) :
            if(artist_uri == G.nodes[node]["Artist URI"]) :
                cleanedGenres = clean_genres(artist_details_dict[artist_uri]["genres"], top_genres)
                artist_details_dict[node] = artist_details_dict[artist_uri]
                artist_details_dict[node]["genres"] = list(cleanedGenres)
                
    nx.set_node_attributes(G, artist_details_dict)
    
    return

def clean_genres(track_genres : list, all_genres : list) -> list :
    cleanedGenre = set()
    for track_genre in track_genres :
        for genre in all_genres :
            if(genre.lower() in track_genre.lower()) :
                cleanedGenre.add(genre)
                
    return cleanedGenre

def get_all_genres(artist_details : list) -> dict :
    genres_list = []
    allowed_genres = ['Hip Hop', 'Pop', 'Rock', 'Country', 'Rap', 'EDM', 'Indie', 'R&B', 'Trap', 'Electro', 'Mellow']
    for artists in artist_details :
        for artist in artists['artists'] :
            genres_list.extend(artist['genres'])

    for i in range(0, len(genres_list)) :
        for genre in allowed_genres :
            if(genre.lower() in genres_list[i].lower()) :
                genres_list[i] = genre
    
    all_genres = Counter(genres_list)
    
        
    return all_genres
         