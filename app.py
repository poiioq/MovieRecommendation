import streamlit as st
import pickle
import requests
import pandas as pd
import gzip
from recommendation_functions import get_top_movies, get_movies_by_genre, improved_recommend_movies, recommend_movies,hybrid

# Load data and models
with gzip.open('model/moviesByGenres_df.pkl.gz', 'rb') as f_in:
    moviesByGenres_df = pickle.load(f_in)

with gzip.open('model/merge_movies.pkl.gz', 'rb') as f_in:
    merge_movies = pickle.load(f_in)

with gzip.open('model/hybrid_movies.pkl.gz', 'rb') as f_in:
    hybrid_movies = pickle.load(f_in)

with gzip.open('model/svd.pkl.gz', 'rb') as f_in:
    svd = pickle.load(f_in)

moviesByGenres_df = pd.DataFrame(moviesByGenres_df)
merge_movies = pd.DataFrame(merge_movies)
hybrid_movies = pd.DataFrame(hybrid_movies)

# Function to fetch movie poster
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzNzgzNzM5N2ZkOGFjMmE4YjRhNDIyNDdjOWU5ZmYwMiIsIm5iZiI6MTcyMjI3Njc3NC4wNjUzNjksInN1YiI6IjY2ODcxYmVhYTEzNTI0MmVkOTI2NWZiZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.bMu5FhhAhpMljjV4jKxdSdvR-3A-ezZMVgCXX6DXfmE"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        poster_path = data.get('poster_path', '')
        if poster_path:
            full_path = f"https://image.tmdb.org/t/p/w500/{poster_path}"
            return full_path
        else:
            return "Poster not found"
    else:
        return f"API request failed with status code {response.status_code}"

#Function to display recommended movies
def show_recommend(movies):
    recommended_movie_names = []
    recommended_movie_posters = []

    for _,row in movies.iterrows():
        if 'id' in row:
            movie_id = row['id']
        else:
            continue  # Skip this row if 'id' is not found
        title = row['title']
        post_url = fetch_poster(movie_id)
        recommended_movie_names.append(title)
        recommended_movie_posters.append(post_url)

    # Display the movies in rows and columns
    cols = st.columns(2)
    for i in range(0, 10, 2):
        with cols[0]:
            if i < 10:
                st.markdown(f"<h4 style='text-align: left;color:SlateBlue'>{recommended_movie_names[i]}</h4>",
                            unsafe_allow_html=True)
                st.image(recommended_movie_posters[i], width=300)
        with cols[1]:
            if i + 1 < 10:
                st.markdown(f"<h4 style='text-align: left;color:SlateBlue'>{recommended_movie_names[i+1]}</h4>",
                            unsafe_allow_html=True)
                st.image(recommended_movie_posters[i + 1], width=300)

def show_movie(title, movies_df):
    if title in movies_df['title'].values:
        movie_id = movies_df.loc[movies_df['title'] == title]['id'].values[0]
        post_url = fetch_poster(movie_id)
        if post_url:
            st.markdown(f"<h2 style='text-align: left;color:SlateBlue'>{title}</h2>", unsafe_allow_html=True)
            st.image(post_url, width=300)
        else:
            st.write("Poster not found")
    else:
        st.write("Movie title not found")

# Streamlit App
st.markdown(f"<h1>Movie Recommender System</h1>",unsafe_allow_html=True)

# Initialize session state for user_id if it does not exist
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# Simple login system
user_id = st.text_input("Enter your user ID", "")
if st.button("Login"):
    st.session_state['user_id'] = user_id

# Search bar and genre tags
search_query = st.text_input("Search for a movie")
genres = ['','Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Drama',
          'Family', 'Fantasy', 'Horror', 'Mystery', 'Romance',
          'Science Fiction', 'Thriller', 'War', 'Western']
selected_genre = st.selectbox("Select Genre", genres, index=0)


# Determine which recommendation engine to use
# Content Based Recommendations
if st.session_state['user_id'] is None and search_query:
    search_query = search_query.strip()
    show_movie(search_query, merge_movies)
    st.markdown(f"<h3>Similar movies as <span style='color:SlateBlue'>{search_query}</span>--Content Based Recommendations"
                , unsafe_allow_html=True)
    recommend_movies = improved_recommend_movies(search_query, movie_df=merge_movies)
    recommend_movies = pd.DataFrame(recommend_movies)
    show_recommend(recommend_movies)
    search_query = ""
    st.session_state['user_id'] = None

# Hybrid Recommendations
elif st.session_state['user_id'] is not None and search_query:
    search_query = search_query.strip()
    show_movie(search_query, merge_movies)
    current_user_id = int(st.session_state['user_id'])
    st.markdown(f"<h3>Recommend for user{current_user_id} -- Hybrid Recommendations</h3>", unsafe_allow_html=True)
    recommend_movies = hybrid(current_user_id, search_query, hybrid_movies, svd)
    recommend_movies = pd.DataFrame(recommend_movies)
    show_recommend(recommend_movies)
    search_query = ""
    st.session_state['user_id'] = None

elif selected_genre != '':
    st.subheader(f"#{selected_genre}")
    genre_movies = get_movies_by_genre(selected_genre, moviesByGenres_df)
    show_recommend(genre_movies)
    selected_genre = ''
else:
    st.subheader("Top Movies Recommendations")
    top_movies = get_top_movies(moviesByGenres_df)
    show_recommend(top_movies)



