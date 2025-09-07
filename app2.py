import pickle
import pandas as pd
import numpy as np
import requests
import gradio as gr

# ---------------- Config ----------------
API_KEY = "d3eea56f1983a39c4290160c2fb03522"
TMDB_BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER = "https://via.placeholder.com/200x300?text=No+Image"


# ---------------- Helpers ----------------
def safe_get(url, params=None, timeout=12):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except:
        return None


def fetch_movie_details(movie_id: int):
    params = {"api_key": API_KEY, "language": "en-US",
              "append_to_response": "videos"}
    data = safe_get(f"{TMDB_BASE}/movie/{movie_id}", params=params)

    if not data:
        return {"poster": PLACEHOLDER, "title": "Unknown", "rating": 0.0, "year": "N/A", "genres": "Unknown"}

    poster_path = data.get("poster_path")
    poster_url = f"{IMG_BASE}{poster_path}" if poster_path else PLACEHOLDER

    title = data.get("title", "Unknown")
    rating = round(float(data.get("vote_average", 0.0) or 0.0), 1)
    release_date = data.get("release_date") or ""
    year = release_date.split("-")[0] if release_date else "N/A"
    genres = ", ".join([g.get("name", "")
                       for g in data.get("genres", [])]) or "Unknown"

    return {"poster": poster_url, "title": title, "rating": rating, "year": year, "genres": genres}


def top_k_indices(distances: np.ndarray, k: int = 5, self_index: int = 0):
    distances = distances.copy()
    distances[self_index] = -np.inf
    k = min(k, distances.shape[0]-1)
    if k <= 0:
        return []
    part_idx = np.argpartition(distances, -k)[-k:]
    return part_idx[np.argsort(distances[part_idx])[::-1]]


def recommend(selected_title: str, k: int = 5):
    idx_matches = movies.index[movies["title"] == selected_title].tolist()
    if not idx_matches:
        return "<p style='color:red;'>Movie not found.</p>"
    i = idx_matches[0]
    distances = similarity[i]
    rec_indices = top_k_indices(distances, k=k, self_index=i)

    recs = [fetch_movie_details(int(movies.iloc[j]["movie_id"]))
            for j in rec_indices]

    # Build HTML with posters
    html_cards = "<div style='display:flex;flex-wrap:wrap;gap:20px;'>"
    for m in recs:
        html_cards += f"""
        <div style="width:200px;text-align:center;background:#0d1b2a;color:white;
                    padding:10px;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.3);">
            <img src="{m['poster']}" alt="Poster" style="width:100%;border-radius:8px;">
            <h4 style="margin:10px 0 5px 0;">{m['title']}</h4>
            <p>⭐ {m['rating']} | 📅 {m['year']}</p>
            <p style="font-size:13px;">{m['genres']}</p>
        </div>
        """
    html_cards += "</div>"

    return html_cards


# ---------------- Data ----------------
movies_dict = pickle.load(open("movies_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))

# ---------------- Gradio UI ----------------
demo = gr.Interface(
    fn=recommend,
    inputs=gr.Dropdown(movies["title"].tolist(), label="Pick a Movie"),
    outputs=gr.HTML(),
    title="🎬 Movie Recommender System 🎥",
    description="Select a movie and see posters of similar movies."
)

if __name__ == "__main__":
    demo.launch()
