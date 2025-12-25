import pandas as pd
import numpy as np


def recommend_movies(df, cosine_sim, title=None, target_languages=None, target_genres=None, top_n=10):
    # ---------------------------------------------------------
    # SCENARIO 1: EXPLORATION MODE (No Movie Selected)
    # ---------------------------------------------------------
    if not title:
        filtered_df = df.copy()
        if target_languages:
            filtered_df = filtered_df[filtered_df["original_language"].isin(target_languages)]

        if target_genres:
            def has_genre(movie_genres):
                return not set(movie_genres).isdisjoint(set(target_genres))

            filtered_df = filtered_df[filtered_df["genres_list"].apply(has_genre)]

        if not filtered_df.empty:
            m = filtered_df["vote_count"].quantile(0.70)
            q_movies = filtered_df[filtered_df["vote_count"] >= m].copy()
            if q_movies.empty: q_movies = filtered_df.copy()
            q_movies = q_movies.sort_values("vote_average", ascending=False)
            return q_movies.head(top_n)
        return pd.DataFrame()

    # ---------------------------------------------------------
    # SCENARIO 2: RECOMMENDATION MODE (Movie Selected)
    # ---------------------------------------------------------
    if title not in df["title"].values:
        return pd.DataFrame()

    # Get Source Movie Details
    idx = df[df["title"] == title].index[0]

    # Validation: Ensure index is valid
    if isinstance(idx, pd.Index): idx = idx[0]

    source_genres = set(df.loc[idx, "genres_list"])
    source_cast = set(df.loc[idx, "cast_list"])
    source_director = df.loc[idx, "director_clean"]
    source_lang = df.loc[idx, "original_language"]

    # Language Logic: If no preference, stick to source language
    if not target_languages:
        allowed_langs = [source_lang, "en"] if source_lang != "en" else ["en"]
    else:
        allowed_langs = target_languages

    # Get Candidates
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n * 5]  # Look at top candidates

    candidates = []

    for i, sim in sim_scores:
        row = df.iloc[i]

        # 1. Language Filter
        if row["original_language"] not in allowed_langs:
            continue

        row_genres = set(row["genres_list"])

        # 2. Genre Filter (Only if user selected specific genres in sidebar)
        if target_genres:
            if not row_genres.intersection(set(target_genres)):
                continue

        # 🟢 REMOVED BAD "COMEDY" LOGIC HERE
        # We now rely purely on the improved 'soup' similarity

        # 3. Scoring Boosts
        score = sim

        # Director Boost
        if row["director_clean"] == source_director and source_director:
            score += 0.10

        # Cast Boost
        target_cast = set(row["cast_list"])
        shared_actors = source_cast.intersection(target_cast)
        if len(shared_actors) > 0:
            score += 0.10

        candidates.append((i, score))

    # Sort final candidates by score
    candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    top_indices = [x[0] for x in candidates[:top_n]]

    return df.iloc[top_indices]