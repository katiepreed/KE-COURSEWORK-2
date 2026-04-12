import requests
import os
import json
import time

BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1"

def get_department_mapping():
    response = requests.get(f"{BASE_URL}/departments", timeout=30)
    response.raise_for_status()
    data = response.json()
    return {dept["displayName"]: dept["departmentId"] for dept in data.get("departments", [])}

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


def get_data(query, max_results, deptartments):
    ids = search_database(query, max_results)
    objects = []

    for obj_id in ids:
        obj = get_object(obj_id)

        time.sleep(0.2)

        if obj is None:
            continue

        raw_tags = obj.get("tags") or []
        tag_names = [t.get("term") for t in raw_tags if t.get("term")]

        dept_name = obj.get("department", "")
        dept_id = deptartments.get(dept_name)

        if obj.get("title"):
            objects.append({
                "object_id": obj.get("objectID"),
                "object_name": obj.get("objectName"),
                "title": obj.get("title"),
                "object_date": obj.get("objectDate"),
                "culture": obj.get("culture"),
                "medium": obj.get("medium"),
                "classification": obj.get("classification"),
                "period": obj.get("period"),
                "begin_date": obj.get("objectBeginDate"),
                "end_date": obj.get("objectEndDate"),
                "department": dept_name,
                "department_id": dept_id,
                "repository": obj.get("repository"),
                "gallery_number": obj.get("GalleryNumber"),
                "artist": obj.get("artistDisplayName"),
                "artist_nationality": obj.get("artistNationality"),
                "artist_gender": obj.get("artistGender"),
                "artist_begin_date": obj.get("artistBeginDate"),
                "artist_end_date": obj.get("artistEndDate"),
                "geography_type": obj.get("geographyType"),
                "country": obj.get("country"),
                "city": obj.get("city"),
                "region": obj.get("region"),
                "tags": tag_names,
            })

    return objects



"""
keywords = ["painting", "sculpture", "ceramic", "figurine", "jewelry", "scroll", "statue", "vase", "cat", "dog", "horse", "myth", "allegory", "flower", "tree", "plant", "god", "biblical", "van gogh", "monet"]

departments = get_department_mapping()

# query each of the words in the keywords list 
data = get_data("monet", 20, departments)

if os.path.exists("data.json") and os.path.getsize("data.json") > 0:
    with open("data.json", "r") as f:
        existing = json.load(f)
else:
    existing = []

existing.extend(data)

with open("data.json", "w") as f:
    json.dump(existing, f, indent=2)
"""