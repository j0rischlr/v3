from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE_URL

app = FastAPI()

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def truncate_overview(text, max_lines=4, chars_per_line=100):
    """Limite le résumé à un nombre maximum de lignes"""
    if not text:
        return text

    max_chars = max_lines * chars_per_line

    # Si le texte est déjà assez court, le retourner tel quel
    if len(text) <= max_chars:
        return text

    # Tronquer et chercher le dernier point avant la limite
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')

    # Trouver la dernière ponctuation de fin de phrase
    last_punct = max(last_period, last_exclamation, last_question)

    if last_punct > max_chars * 0.7:  # Si on trouve une ponctuation après 70% du texte
        return text[:last_punct + 1]
    else:
        # Sinon, couper au dernier espace avant la limite et ajouter "..."
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return text[:last_space] + "..."
        return truncated + "..."


def get_popular_movies(page=1):
    """Récupère une liste de films populaires depuis TMDB"""
    url = f"{TMDB_BASE_URL}/movie/popular"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR",
        "page": page
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des films")

    return response.json()


def get_movie_details(movie_id):
    """Récupère les détails complets d'un film"""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des détails du film")

    return response.json()


def get_movie_credits(movie_id):
    """Récupère les crédits (acteurs) d'un film"""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des crédits du film")

    return response.json()


def get_movie_videos(movie_id):
    """Récupère les vidéos (bandes annonces) d'un film"""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None

    videos_data = response.json()

    # Chercher la première bande annonce YouTube
    for video in videos_data.get("results", []):
        if video.get("type") == "Trailer" and video.get("site") == "YouTube":
            return f"https://www.youtube.com/watch?v={video.get('key')}"

    # Si pas de trailer en français, essayer en anglais
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos"
    params["language"] = "en-US"
    response = requests.get(url, params=params)

    if response.status_code == 200:
        videos_data = response.json()
        for video in videos_data.get("results", []):
            if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                return f"https://www.youtube.com/watch?v={video.get('key')}"

    return None


@app.get("/")
async def root():
    return {"message": "API de suggestion de films aléatoires"}


@app.get("/api/random-movie")
async def get_random_movie():
    """Endpoint pour récupérer un film aléatoire avec résumé"""
    try:
        max_attempts = 20
        attempt = 0

        while attempt < max_attempts:
            # Récupérer une page aléatoire de films populaires (entre 1 et 10)
            random_page = random.randint(1, 10)
            movies_data = get_popular_movies(page=random_page)

            if not movies_data.get("results"):
                raise HTTPException(status_code=404, detail="Aucun film trouvé")

            # Sélectionner un film aléatoire dans les résultats
            random_movie = random.choice(movies_data["results"])

            # Récupérer les détails complets du film
            movie_details = get_movie_details(random_movie["id"])

            # Vérifier que le film a un résumé non vide
            overview = movie_details.get("overview", "").strip()
            if not overview:
                attempt += 1
                continue

            # Récupérer les crédits du film (acteurs)
            movie_credits = get_movie_credits(random_movie["id"])

            # Récupérer les 6 premiers acteurs principaux
            cast = movie_credits.get("cast", [])[:6]
            actors = [
                {
                    "id": actor.get("id"),
                    "name": actor.get("name"),
                    "character": actor.get("character"),
                    "profile_path": f"{TMDB_IMAGE_BASE_URL}{actor['profile_path']}" if actor.get("profile_path") else None
                }
                for actor in cast
            ]

            # Récupérer les genres du film
            genres = [genre.get("name") for genre in movie_details.get("genres", [])]

            # Récupérer l'URL de la bande annonce
            trailer_url = get_movie_videos(random_movie["id"])

            # Construire la réponse avec toutes les informations demandées
            return {
                "id": movie_details["id"],
                "title": movie_details["title"],
                "release_date": movie_details.get("release_date", "Date inconnue"),
                "runtime": movie_details.get("runtime", 0),
                "vote_average": movie_details.get("vote_average", 0),
                "vote_count": movie_details.get("vote_count", 0),
                "overview": truncate_overview(overview),
                "backdrop_path": f"{TMDB_IMAGE_BASE_URL}{movie_details['backdrop_path']}" if movie_details.get("backdrop_path") else None,
                "poster_path": f"{TMDB_IMAGE_BASE_URL}{movie_details['poster_path']}" if movie_details.get("poster_path") else None,
                "genres": genres,
                "trailer_url": trailer_url,
                "actors": actors
            }

        # Si après max_attempts on n'a pas trouvé de film avec résumé
        raise HTTPException(status_code=404, detail="Aucun film avec résumé trouvé après plusieurs tentatives")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actor/{actor_id}")
async def get_actor_details(actor_id: int):
    """Endpoint pour récupérer les détails et la filmographie d'un acteur"""
    try:
        # Récupérer les détails de l'acteur
        actor_url = f"{TMDB_BASE_URL}/person/{actor_id}"
        actor_params = {
            "api_key": TMDB_API_KEY,
            "language": "fr-FR"
        }

        actor_response = requests.get(actor_url, params=actor_params)
        if actor_response.status_code != 200:
            raise HTTPException(status_code=404, detail="Acteur non trouvé")

        actor_data = actor_response.json()

        # Récupérer les crédits de l'acteur (films)
        credits_url = f"{TMDB_BASE_URL}/person/{actor_id}/movie_credits"
        credits_params = {
            "api_key": TMDB_API_KEY,
            "language": "fr-FR"
        }

        credits_response = requests.get(credits_url, params=credits_params)
        if credits_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erreur lors de la récupération de la filmographie")

        credits_data = credits_response.json()

        # Récupérer uniquement les films où l'acteur joue (cast)
        movies = credits_data.get("cast", [])

        # Trier les films par popularité décroissante
        movies_sorted = sorted(movies, key=lambda x: x.get("popularity", 0), reverse=True)

        # Limiter à 30 films et formater les données
        filmography = [
            {
                "id": movie.get("id"),
                "title": movie.get("title"),
                "character": movie.get("character"),
                "release_date": movie.get("release_date", ""),
                "vote_average": movie.get("vote_average", 0),
                "poster_path": f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
                "backdrop_path": f"{TMDB_IMAGE_BASE_URL}{movie['backdrop_path']}" if movie.get("backdrop_path") else None,
                "overview": truncate_overview(movie.get("overview", ""))
            }
            for movie in movies_sorted[:30]
        ]

        # Retourner les informations de l'acteur et sa filmographie
        return {
            "id": actor_data["id"],
            "name": actor_data["name"],
            "biography": actor_data.get("biography", ""),
            "birthday": actor_data.get("birthday", ""),
            "place_of_birth": actor_data.get("place_of_birth", ""),
            "profile_path": f"{TMDB_IMAGE_BASE_URL}{actor_data['profile_path']}" if actor_data.get("profile_path") else None,
            "filmography": filmography
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/movie/{movie_id}")
async def get_movie_by_id(movie_id: int):
    """Endpoint pour récupérer les détails d'un film spécifique"""
    try:
        # Récupérer les détails complets du film
        movie_details = get_movie_details(movie_id)

        # Vérifier que le film a un résumé
        overview = movie_details.get("overview", "").strip()
        if not overview:
            overview = "Aucun résumé disponible"

        # Récupérer les crédits du film (acteurs)
        movie_credits = get_movie_credits(movie_id)

        # Récupérer les 6 premiers acteurs principaux
        cast = movie_credits.get("cast", [])[:6]
        actors = [
            {
                "id": actor.get("id"),
                "name": actor.get("name"),
                "character": actor.get("character"),
                "profile_path": f"{TMDB_IMAGE_BASE_URL}{actor['profile_path']}" if actor.get("profile_path") else None
            }
            for actor in cast
        ]

        # Récupérer les genres du film
        genres = [genre.get("name") for genre in movie_details.get("genres", [])]

        # Récupérer l'URL de la bande annonce
        trailer_url = get_movie_videos(movie_id)

        # Construire la réponse avec toutes les informations demandées
        return {
            "id": movie_details["id"],
            "title": movie_details["title"],
            "release_date": movie_details.get("release_date", "Date inconnue"),
            "runtime": movie_details.get("runtime", 0),
            "vote_average": movie_details.get("vote_average", 0),
            "vote_count": movie_details.get("vote_count", 0),
            "overview": truncate_overview(overview),
            "backdrop_path": f"{TMDB_IMAGE_BASE_URL}{movie_details['backdrop_path']}" if movie_details.get("backdrop_path") else None,
            "poster_path": f"{TMDB_IMAGE_BASE_URL}{movie_details['poster_path']}" if movie_details.get("poster_path") else None,
            "genres": genres,
            "trailer_url": trailer_url,
            "actors": actors
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
