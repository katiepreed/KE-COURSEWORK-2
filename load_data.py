import requests
import os
import json
import time

BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1"

def search_database(query, max_results):
    params = {"q": query} 

    response = requests.get(f"{BASE_URL}/search", params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    object_ids = data.get("objectIDs", [])

    if not object_ids:
        return []

    return object_ids[:max_results]

def get_object(object_id):
    response = requests.get(f"{BASE_URL}/objects/{object_id}", timeout=30)
    time.sleep(0.2) 
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def get_data(query, max_results):
    ids = search_database(query, max_results)
    objects = []

    for obj_id in ids:
        obj = get_object(obj_id)

        time.sleep(0.2)

        if obj is None:
            continue

        if obj.get("title"):
            objects.append({
                "object_id": obj.get("objectID"),
                "object_name": obj.get("objectName"),
                "title": obj.get("title"),
                "culture": obj.get("culture"),
                "medium": obj.get("medium"),
                "period": obj.get("period"),
                "begin_date": obj.get("objectBeginDate"),
                "end_date": obj.get("objectEndDate"),
                "gallery_number": obj.get("GalleryNumber"),
                "artist": obj.get("artistDisplayName"),
                "artist_nationality": obj.get("artistNationality"),
                "artist_gender": obj.get("artistGender"),
                "artist_begin_date": obj.get("artistBeginDate"),
                "geography_type": obj.get("geographyType"),
                "country": obj.get("country"),
                "city": obj.get("city"),
                "region": obj.get("region"),
            })

    return objects


"""
The way the q parameter works is that it does a broad text search across most of an object's metadata fields. 

data = get_data("painting", 20)
data = get_data("sculpture", 20)
data = get_data("ceramic", 20)
data = get_data("figurine", 20)
data = get_data("jewelry", 20)
data = get_data("scroll", 20)
data = get_data("statue", 20)
data = get_data("vase", 20)
"""
data = get_data("flower", 20)

if os.path.exists("data.json") and os.path.getsize("data.json") > 0:
    with open("data.json", "r") as f:
        existing = json.load(f)
else:
    existing = []

existing.extend(data)

with open("data.json", "w") as f:
    json.dump(existing, f, indent=2)