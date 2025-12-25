# CineMatch-AI-Powered-Movie-Recommendation-Website
CineMatch is a premium AI-powered movie recommendation web application built using Streamlit, combining content-based recommendation, metadata filtering, and an AI movie concierge (Jarvis) to deliver rich, personalized movie discovery.

The platform allows users to:
-Discover movies similar to their favorites
-Filter recommendations by language and genre
-Explore top-rated movies without selecting a reference title
-Chat with an AI assistant for conversational movie suggestions
-View posters, ratings, trailers, and IMDb links in an interactive UI

🚀 Key Features

🎥 Content-Based Movie Recommendation Engine
🎭 Filters by Genre and Language (English, Hindi, etc.)
🤖 Jarvis AI – conversational movie concierge (LLM-powered)
🖼️ Dynamic movie cards with posters, trailers & IMDb links
⭐ Weighted similarity using cast, director, genres, keywords & overview
🔥 High-quality UI built with custom CSS & animations
🌐 External movie enrichment using TMDB API

🧠 System Overview

CineMatch uses a content-based recommendation approach enhanced with metadata-aware filtering and AI-driven interaction.
High-Level Flow
1.Movie metadata is cleaned and vectorized
2.Cosine similarity is computed on a weighted “tag soup”
3.Similar movies are ranked and filtered dynamically
4.Results are displayed in an interactive Streamlit UI
5.AI assistant provides conversational recommendations

<img width="1904" height="994" alt="Screenshot 2025-12-24 194230" src="https://github.com/user-attachments/assets/3a27f8d5-4b2e-4d95-9e45-7219ed11c643" />


🏗️ Architecture
1️. Offline Preprocessing

-Cleans and engineers features from movie metadata
-Builds a weighted text representation (“soup”)
-Computes cosine similarity
-Stores processed data + similarity matrix as a pickle file

2️. Online Recommendation Website

-Loads preprocessed model
-Provides movie discovery & AI chat interface
-Fetches posters, ratings & trailers from TMDB
-Renders results using custom HTML/CSS cards

📂 Project Structure

<img width="678" height="645" alt="image" src="https://github.com/user-attachments/assets/c2d6fbba-b358-4f9f-9c30-fbb87a81a587" />


## ▶️ How to Run the Project
1️⃣ Install Dependencies
pip install -r requirements.txt
2️⃣ Run Preprocessing 
This creates the recommendation model and similarity matrix.
python preprocess2.py
This will generate:
utils/movie_model.pkl
3️⃣ Launch the Web Application
streamlit run app2.py

🤖 Jarvis AI – Movie Concierge
CineMatch includes Jarvis, an AI-powered assistant that:
Responds conversationally to user queries
Suggests 5–8 relevant movies per query
Generates engaging plot summaries
Integrates seamlessly with the recommendation UI

The AI uses:
Groq LLM API
TMDB API for enrichment (posters, ratings, trailers)
⚠️ API keys must be added in app2.py before running.
