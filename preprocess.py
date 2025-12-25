import pandas as pd
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ------------------------------------------------------------------
# 1. Load Data
# ------------------------------------------------------------------
# Update path if necessary
df = pd.read_csv(r"C:\Users\sanke\OneDrive\Desktop\PythonProject\PythonProject\movie_recommendation_website\data\movie_db_READY_FOR_RECOMMENDER.csv", encoding='latin-1')

cols = ["title", "overview", "genres", "keywords", "cast", "director",
        "vote_average", "vote_count", "original_language", "poster_url"]

df = df[cols].fillna("")
df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce").fillna(0)

# ------------------------------------------------------------------
# 2. Robust Cleaning Functions
# ------------------------------------------------------------------
def clean_genre_list(x):
    if not x: return []
    x = str(x).lower().replace("|", ",")
    return [i.strip() for i in x.split(",") if i.strip()]

def clean_id(x):
    """'Paresh Rawal' -> 'pareshrawal'"""
    if not x: return ""
    return str(x).lower().replace(" ", "").replace(",", " ").replace("|", " ")

def clean_text(x):
    """Simple text cleaner"""
    return str(x).lower().replace("|", " ").replace(",", " ")

# ------------------------------------------------------------------
# 3. Create Tag Soup (UPDATED)
# ------------------------------------------------------------------
# 🟢 CRITICAL FIX: Added 'title' to the soup so "Thor" matches "Thor"
df["soup"] = (
    (df["title"].apply(clean_text) + " ") * 2 +           # Title (Weight x2)
    (df["genres"].apply(clean_text) + " ") * 4 +          # Genres
    (df["cast"].apply(clean_id) + " ") * 5 +              # Cast (High Weight)
    (df["director"].apply(clean_id) + " ") * 5 +          # Director
    (df["keywords"].apply(clean_text) + " ") * 3 +
    (df["overview"].apply(clean_text) + " ")
)

# ------------------------------------------------------------------
# 4. Vectorization
# ------------------------------------------------------------------
print("Vectorizing data...")
cv = CountVectorizer(max_features=5000, stop_words="english")
vectors = cv.fit_transform(df["soup"]).toarray()
cosine_sim = cosine_similarity(vectors)

# ------------------------------------------------------------------
# 5. Save Model Data
# ------------------------------------------------------------------
df["genres_list"] = df["genres"].apply(clean_genre_list)
df["director_clean"] = df["director"].apply(clean_id)
df["cast_list"] = df["cast"].apply(lambda x: [clean_id(n) for n in str(x).replace("|", ",").split(",")])

final_data = df[[
    "title", "poster_url", "original_language",
    "vote_average", "vote_count","overview",
    "genres_list", "director_clean", "cast_list"
]]

with open(r"C:\Users\sanke\OneDrive\Desktop\PythonProject\PythonProject\movie_recommendation_website\utils\movie_model.pkl", "wb") as f:
    pickle.dump((final_data, cosine_sim), f)

print("✅ Preprocessing Done! Model updated with Title matching.")
