import requests
import time
from tabulate import tabulate  # Import tabulate

API_KEY = "9855691bd5526928ce2d62fec27145d2"

# Movies to compare against
TARGET_MOVIES = {
    "Inception": 27205,
    "The Dark Knight": 155,
    "Interstellar": 157336
}

# Function to fetch movie details
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&append_to_response=credits,keywords"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return {
            "title": data.get("title"),
            "genres": {genre["name"] for genre in data.get("genres", [])},
            "director": next((crew["name"] for crew in data["credits"]["crew"] if crew["job"] == "Director"), "Unknown"),
            "keywords": {keyword["name"] for keyword in data.get("keywords", {}).get("keywords", [])},
        }
    else:
        print(f" Error fetching movie ID {movie_id}: {response.status_code}")
        return None

# Fetch top-rated movies (limit to 50 pages = 1000 movies)
def fetch_top_movies(pages=50):
    all_movies = []
    for page in range(1, pages + 1):
        url = f"https://api.themoviedb.org/3/movie/top_rated?api_key={API_KEY}&page={page}"
        response = requests.get(url)
        if response.status_code == 200:
            all_movies.extend(response.json()["results"])
        else:
            print(" Error fetching movies:", response.status_code)
            break
    return all_movies


# Fetch details for the target movies
detailed_movies = [fetch_movie_details(movie_id) for movie_id in TARGET_MOVIES.values()]
detailed_movies = [movie for movie in detailed_movies if movie] 

# Fetch top movies (limit to 1000)
top_movies = fetch_top_movies()
print(f" Fetched {len(top_movies)} movies")

# Fetch details for top 1000 movies (to speed up execution)
detailed_movies = []
for movie in top_movies[:1000]:
    details = fetch_movie_details(movie["id"])
    if details:
        detailed_movies.append(details)
    time.sleep(0.2)  

print(f" Fetched details for {len(detailed_movies)} movies")

# Fetch details for the target movies
target_movie_details = {name: fetch_movie_details(movie_id) for name, movie_id in TARGET_MOVIES.items()}

# Function to compute Jaccard Similarity
def jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0  
    return len(set1 & set2) / len(set1 | set2)

# Compute similarity for each target movie
for target_name, target_details in target_movie_details.items():
    if not target_details:
        continue 

    similarity_scores = []
    for movie in detailed_movies:
        if movie["title"] == target_details["title"]:
            continue  

        score = jaccard_similarity(target_details["genres"], movie["genres"]) * 0.6 + \
                jaccard_similarity(target_details["keywords"], movie["keywords"]) * 0.3 + \
                (1 if target_details["director"] == movie["director"] else 0) * 0.1  

        similarity_scores.append((movie["title"], score))

    # Sort movies by similarity score
    similar_movies = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

    # Print results in a table format
    print(f"\nTop 10 Movies Similar to {target_name}:")
    
    # Prepare data for the table
    table_data = [(title, f"{score:.2f}") for title, score in similar_movies[:10]]
    
    # Print table using tabulate
    print(tabulate(table_data, headers=["Movie Title", "Similarity Score"], tablefmt="grid"))
