import streamlit as st
import pickle
import pandas as pd
import streamlit.components.v1 as components
import html
import urllib.parse
import json
import requests
import time
import re
from groq import Groq
from utils.recommender import recommend_movies

# -------------------------------------------------------------------------
# 0. API CONFIGURATION
# -------------------------------------------------------------------------
# ⚠️ PASTE YOUR KEYS HERE
GROQ_API_KEY = "Your GROQ_API_KEY"
TMDB_API_KEY = "Your TMDB_API_KEY"

# Initialize Groq
client = Groq(api_key=GROQ_API_KEY)

# -------------------------------------------------------------------------
# 1. PAGE CONFIG
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="CineMatch | Premium AI",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------------
# 2. SESSION STATE
# -------------------------------------------------------------------------
if "booted" not in st.session_state:
    st.session_state.booted = False


# -------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# -------------------------------------------------------------------------

def style_ai_response(text):
    """Highlights keywords in RED."""
    keywords = [
        "horror", "scary", "terrifying", "spooky", "creepy", "thriller",
        "suspense", "ghost", "blood", "demon", "kill", "death", "nightmare",
        "chilling", "dark", "evil", "haunted", "fear", "love", "romance", "romantic"
    ]
    for word in keywords:
        pattern = re.compile(f"\\b({word})\\b", re.IGNORECASE)
        text = pattern.sub(r":red[**\1**]", text)
    return text


def fetch_tmdb_data(movie_title, ai_overview=None):
    """Fetches Poster, Rating, and Trailer from TMDB."""
    data = {
        "poster": "https://via.placeholder.com/300x450?text=No+Poster",
        "rating": "N/A",
        "overview": ai_overview if ai_overview else "No details available.",
        "trailer": f"https://www.youtube.com/results?search_query={urllib.parse.quote(movie_title)}+trailer"
    }

    try:
        search_url = "https://api.themoviedb.org/3/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": movie_title, "page": 1, "include_adult": "false"}
        response = requests.get(search_url, params=params, timeout=3)
        results = response.json().get("results", [])

        if results:
            top_result = results[0]
            movie_id = top_result["id"]

            if top_result.get("poster_path"):
                data["poster"] = f"https://image.tmdb.org/t/p/w500{top_result['poster_path']}"
            if top_result.get("vote_average"):
                data["rating"] = round(top_result.get("vote_average"), 1)

            tmdb_overview = top_result.get("overview", "")
            if len(tmdb_overview) > 20:
                data["overview"] = tmdb_overview

            video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
            vid_response = requests.get(video_url, params={"api_key": TMDB_API_KEY}, timeout=3)
            vid_data = vid_response.json().get("results", [])
            for vid in vid_data:
                if vid["site"] == "YouTube" and vid["type"] == "Trailer":
                    data["trailer"] = f"https://www.youtube.com/watch?v={vid['key']}"
                    break
    except Exception as e:
        print(f"TMDB Error: {e}")

    return data


def get_ai_recommendation(user_query):
    system_prompt = """
    You are Jarvis, a sophisticated AI movie concierge.
    1. Answer the user's question with personality.
    2. Suggest 5-8 specific movies relevant to the query.
    3. You MUST return the response in strict JSON format with two keys:
       - "response_text": Your conversational answer.
       - "recommendations": A list of objects, where each object has:
            - "title": Exact movie title.
            - "overview": A 1-sentence engaging plot summary.
    4. Do not output markdown blocks, just raw JSON.
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_query}],
            temperature=0.7, max_tokens=800, response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {"response_text": f"Error: {str(e)}", "recommendations": []}


def render_movie_cards(movie_data_list):
    cards_html = ""
    for mov in movie_data_list:
        title = html.escape(str(mov['title']))
        poster = mov['poster']
        rating = mov.get('rating', 'N/A')
        overview = html.escape(str(mov.get('overview', '')))[:110] + "..."
        trailer_link = mov.get('trailer', '#')
        if trailer_link == '#' or not trailer_link:
            trailer_link = f"https://www.youtube.com/results?search_query={urllib.parse.quote(mov['title'])}+trailer"
        imdb_link = f"https://www.imdb.com/find?q={urllib.parse.quote(mov['title'])}"

        cards_html += f"""
        <div class="flip-card">
          <div class="flip-card-inner">
            <div class="flip-card-front"><img src="{poster}" alt="Poster"></div>
            <div class="flip-card-back">
              <div class="title">{title}</div>
              <div class="meta">⭐ {rating}</div>
              <div class="desc">{overview}</div>
              <div class="btn-group">
                  <a href="{trailer_link}" target="_blank" class="btn btn-trailer">▶ Trailer</a>
                  <a href="{imdb_link}" target="_blank" class="btn btn-imdb">IMDb</a>
              </div>
            </div>
          </div>
        </div>
        """
    return f"""
    <!DOCTYPE html><html><head>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; background: transparent; font-family: 'Poppins', sans-serif; }}
        .scroll-container {{ display: flex; align-items: center; overflow-x: auto; padding: 30px 20px; gap: 20px; }}
        ::-webkit-scrollbar {{ height: 0px; background: transparent; }}
        .flip-card {{ background-color: transparent; width: 190px; height: 285px; perspective: 1000px; flex: 0 0 auto; cursor: pointer; }}
        .scroll-container:hover .flip-card {{ opacity: 0.4; filter: blur(2px); transform: scale(0.95); transition: 0.4s; }}
        .scroll-container .flip-card:hover {{ opacity: 1; filter: blur(0px); transform: scale(1.25); z-index: 100; margin: 0 35px; box-shadow: 0 30px 60px rgba(0,0,0,0.9); }}
        .flip-card-inner {{ position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d; border-radius: 10px; }}
        .flip-card:hover .flip-card-inner {{ transform: rotateY(180deg); }}
        .flip-card-front, .flip-card-back {{ position: absolute; width: 100%; height: 100%; -webkit-backface-visibility: hidden; backface-visibility: hidden; border-radius: 10px; overflow: hidden; }}
        .flip-card-front img {{ width: 100%; height: 100%; object-fit: cover; }}
        .flip-card-back {{ background: rgba(15, 15, 15, 0.96); color: white; transform: rotateY(180deg); padding: 15px; display: flex; flex-direction: column; border: 1px solid rgba(255,255,255,0.1); text-align: left; }}
        .title {{ font-family: 'Bebas Neue'; font-size: 20px; margin-bottom: 5px; line-height: 1; }}
        .meta {{ font-size: 12px; color: #E50914; font-weight: 700; margin-bottom: 8px; }}
        .desc {{ font-size: 10px; color: #ccc; line-height: 1.4; margin-bottom: auto; }}
        .btn-group {{ display: flex; gap: 8px; margin-top: 10px; width: 100%; }}
        .btn {{ flex: 1; padding: 8px 0; font-size: 10px; font-weight: 700; border-radius: 4px; text-decoration: none; text-align: center; text-transform: uppercase; transition: 0.2s; }}
        .btn-trailer {{ background: #E50914; color: white; }}
        .btn-trailer:hover {{ background: #ff1f2c; }}
        .btn-imdb {{ background: #f5c518; color: black; font-weight: 800; }}
        .btn-imdb:hover {{ background: #e2b616; }}
    </style></head><body><div class="scroll-container">{cards_html}</div></body></html>
    """


# -------------------------------------------------------------------------
# 4. PREMIUM CSS
# -------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Poppins:wght@300;400;600&display=swap');

    /* GLOBAL RESET */
    .stApp { background-color: #050505; color: #ffffff; font-family: 'Poppins', sans-serif; }

    /* HEADER & SIDEBAR */
    header { visibility: visible !important; background-color: transparent !important; }
    #MainMenu, footer { visibility: hidden; }
    section[data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #222; }

    /* SIDEBAR TEXT FIX */
    [data-testid="stSidebar"] label { color: #ffffff !important; font-size: 14px !important; font-weight: 600 !important; }
    [data-testid="stSidebar"] .stMarkdown p { color: #cccccc !important; }

    /* INPUTS */
    input[type="text"] {
        background-color: #1a1a1a !important; 
        color: #ffffff !important;           
        caret-color: #E50914 !important;    
        border: 1px solid #333 !important;
    }
    textarea[data-testid="stChatInputTextArea"] {
        background-color: #1a1a1a !important; 
        color: #ffffff !important;           
        caret-color: #E50914 !important;    
    }
    div[data-testid="stChatMessageContent"] { color: #ffffff !important; }
    div[data-testid="stChatMessageContent"] p { color: #ffffff !important; }

    /* DROPDOWNS */
    div[data-baseweb="select"] > div {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333 !important;
    }
    div[data-baseweb="menu"] { background-color: #1a1a1a !important; }
    div[data-baseweb="option"] { color: #ffffff !important; }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #111; border-radius: 8px; color: #888; font-family: 'Bebas Neue'; font-size: 1.2rem; border: 1px solid #333; }
    .stTabs [aria-selected="true"] { background-color: #E50914 !important; color: white !important; border: none; }

    /* BUTTONS */
    .stButton > button { background: linear-gradient(135deg, #E50914 0%, #B81D24 100%); color: white; border: none; padding: 0.6rem 2rem; border-radius: 6px; font-family: 'Poppins'; font-weight: 600; text-transform: uppercase; }
    .hero-glow { position: absolute; top: -50px; left: 50%; transform: translateX(-50%); width: 90%; height: 300px; background: radial-gradient(circle, rgba(229,9,20,0.12) 0%, rgba(0,0,0,0) 70%); z-index: -1; pointer-events: none; }

    .stChatMessage { background-color: #111; border: 1px solid #333; border-radius: 10px; margin-bottom: 10px; }
    [data-testid="stChatMessageAvatarUser"] { background-color: #E50914; }
    [data-testid="stChatMessageAvatarAssistant"] { background-color: #333; }

    /* BOOT ANIMATION */
    @keyframes fadeOut { 0% { opacity: 1; } 100% { opacity: 0; visibility: hidden; } }
    @keyframes zoomLogo { 0% { transform: scale(0.8); opacity: 0; } 50% { opacity: 1; } 100% { transform: scale(1.2); opacity: 1; } }
    .boot-screen {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #000; z-index: 99999;
        display: flex; justify-content: center; align-items: center; flex-direction: column;
        animation: fadeOut 0.5s ease-out 3s forwards;
    }
    .boot-logo {
        font-family: 'Bebas Neue'; font-size: 6rem; color: #E50914; letter-spacing: 5px;
        animation: zoomLogo 2.5s ease-out forwards;
        text-shadow: 0 0 20px rgba(229, 9, 20, 0.6);
    }
    .boot-loader {
        margin-top: 20px; width: 40px; height: 40px; 
        border: 3px solid #333; border-top: 3px solid #E50914; border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 5. BOOT SEQUENCE
# -------------------------------------------------------------------------
if not st.session_state.booted:
    st.markdown(
        """<div class="boot-screen"><div class="boot-logo">CINEMATCH</div><div class="boot-loader"></div></div>""",
        unsafe_allow_html=True)
    time.sleep(3.5)
    st.session_state.booted = True
    st.rerun()

# -------------------------------------------------------------------------
# 6. LOAD DATA
# -------------------------------------------------------------------------
try:
    with open(r"utils/movie_model.pkl", "rb") as f:
        movies, cosine_sim = pickle.load(f)
except FileNotFoundError:
    st.error("Model file not found! Please run 'preprocess.py' first.")
    st.stop()

movies = movies.reset_index(drop=True)
movies["poster_url"] = movies["poster_url"].fillna("")
all_genres = sorted(list(set([g.title() for sublist in movies['genres_list'] for g in sublist if g])))

# -------------------------------------------------------------------------
# 7. MAIN UI
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        "<h1 style='color:#E50914; font-family:Bebas Neue; text-align:center; font-size:3rem; margin:0;'>CINEMATCH</h1>",
        unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🔍 Filters")
    lang_map = {"English": "en", "Hindi": "hi"}
    selected_langs = st.multiselect("Language", list(lang_map.keys()), ["English", "Hindi"])
    target_langs = [lang_map[l] for l in selected_langs]
    selected_genres = st.multiselect("Genre", all_genres, [])
    target_genres = [g.lower() for g in selected_genres]

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("💡 **Tip:** Ask Jarvis about regional cinema (e.g., 'Best Marathi rom-coms').")

st.markdown('<div class="hero-glow"></div>', unsafe_allow_html=True)
tab_home, tab_jarvis = st.tabs(["🎬 DISCOVER MOVIES", "🤖 CHAT WITH JARVIS"])

# --- TAB 1: DISCOVER ---
with tab_home:
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        # ✅ Reverted to Dropdown (Local Dataset Only)
        selected_movie_name = st.selectbox("Search", movies["title"].sort_values().values, index=None,
                                           placeholder="Search for a movie...", label_visibility="collapsed")
    with col_btn:
        run_search = st.button("SEARCH")

    if run_search or True:
        st.markdown("<br>", unsafe_allow_html=True)
        if selected_movie_name:
            st.markdown(
                f"<h1 style='font-size:3rem;'>Because you liked <span style='color:#E50914'>{selected_movie_name}</span></h1>",
                unsafe_allow_html=True)
        else:
            header_text = f"Top Rated {' & '.join(selected_genres[:2])}" if selected_genres else "Top Global Picks"
            st.markdown(f"<h1 style='font-size:3rem;'>{header_text}</h1>", unsafe_allow_html=True)

        recs = recommend_movies(movies, cosine_sim, title=selected_movie_name, target_languages=target_langs,
                                target_genres=target_genres, top_n=12)
        if recs.empty:
            st.warning("No movies found. Adjust filters.")
        else:
            movie_data = []
            for _, row in recs.iterrows():
                trailer_link = f"https://www.youtube.com/results?search_query={urllib.parse.quote(row['title'])}+trailer"
                movie_data.append({
                    "title": row["title"],
                    "poster": row["poster_url"] if str(row["poster_url"]).startswith(
                        "http") else "https://via.placeholder.com/300x450",
                    "rating": round(row["vote_average"], 1),
                    "overview": row["overview"],
                    "trailer": trailer_link
                })
            components.html(render_movie_cards(movie_data), height=400, scrolling=False)

# --- TAB 2: JARVIS ---
with tab_jarvis:
    st.markdown("<h1 style='font-size:3rem;'>Ask <span style='color:#E50914;'>Jarvis</span></h1>",
                unsafe_allow_html=True)
    st.markdown("<p style='color:#aaa;'>Your AI Movie Concierge. Ask for recommendations, plots, or hidden gems.</p>",
                unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi, I'm Jarvis. How can I help you?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "html_content" in message:
                components.html(message["html_content"], height=380)

    if prompt := st.chat_input("Ask Jarvis (e.g., 'Best Marathi movies?')..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Jarvis is thinking..."):
                ai_data = get_ai_recommendation(prompt)
                response_text = ai_data.get("response_text", "I couldn't process that.")
                recommendations_list = ai_data.get("recommendations", [])

                formatted_response = style_ai_response(response_text)

                if "error" in response_text.lower():
                    st.error(response_text)
                else:
                    st.markdown(formatted_response)

                movie_cards_data = []
                if recommendations_list:
                    for item in recommendations_list:
                        raw_title = item.get("title", "").strip()
                        ai_overview = item.get("overview", "No overview generated.")

                        match = movies[movies['title'].str.contains(raw_title, case=False, regex=False)]
                        if not match.empty:
                            row = match.iloc[0]
                            title, poster, rating, overview = row["title"], row["poster_url"] if str(
                                row["poster_url"]).startswith("http") else "https://via.placeholder.com/300x450", round(
                                row["vote_average"], 1), row["overview"]
                            trailer = f"https://www.youtube.com/results?search_query={urllib.parse.quote(title)}+trailer"
                        else:
                            title, overview = raw_title, ai_overview
                            tmdb_data = fetch_tmdb_data(raw_title, ai_overview)
                            poster, rating, trailer = tmdb_data["poster"], tmdb_data["rating"], tmdb_data["trailer"]
                        movie_cards_data.append(
                            {"title": title, "poster": poster, "rating": rating, "overview": overview,
                             "trailer": trailer})

                    html_cards = render_movie_cards(movie_cards_data)
                    components.html(html_cards, height=380)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": formatted_response, "html_content": html_cards})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": formatted_response})