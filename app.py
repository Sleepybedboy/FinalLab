from flask import Flask, request, jsonify
from pymongo import MongoClient
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB = os.getenv('MONGO_DB')
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
movies_collection = mongo_db['movies']

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@app.route('/movies', methods=['GET'])
def list_all_movies():
    """Liste tous les films depuis MongoDB"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit

        projection = {
            'title': 1,
            'year': 1,
            'genres': 1,
            'directors': 1,
            'cast': 1,
            'plot': 1,
            'imdb.rating': 1,
            '_id': 0
        }

        movies = list(movies_collection.find({}, projection).skip(skip).limit(limit))
        total = movies_collection.count_documents({})

        return jsonify({
            'success': True,
            'page': page,
            'limit': limit,
            'total': total,
            'count': len(movies),
            'movies': movies
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/health', methods=['GET'])
def health_check():
    """Vérifie la connexion aux bases de données"""
    mongo_status = False
    neo4j_status = False
    mongo_error = None
    neo4j_error = None

    try:
        mongo_client.server_info()
        mongo_status = True
    except Exception as e:
        mongo_error = str(e)

    try:
        with neo4j_driver.session() as session:
            session.run("RETURN 1")
        neo4j_status = True
    except Exception as e:
        neo4j_error = str(e)

    return jsonify({
        'mongodb': {
            'status': 'connected' if mongo_status else 'disconnected',
            'error': mongo_error
        },
        'neo4j': {
            'status': 'connected' if neo4j_status else 'disconnected',
            'error': neo4j_error
        },
        'status': 'healthy' if (mongo_status and neo4j_status) else 'degraded'
    }), 200 if (mongo_status and neo4j_status) else 503

@app.route('/movies/common', methods=['GET'])
def get_common_movies():
    """Retourne le nombre de films communs entre MongoDB et Neo4j"""
    try:
        # Récupérer les titres depuis MongoDB
        mongo_movies = movies_collection.find({}, {'title': 1, '_id': 0}).limit(1000)
        mongo_titles = set(movie['title'] for movie in mongo_movies if 'title' in movie)

        # Récupérer les titres depuis Neo4j
        with neo4j_driver.session() as session:
            result = session.run("MATCH (m:Movie) RETURN m.title as title")
            neo4j_titles = set(record['title'] for record in result if record['title'])

        # Films communs
        common_movies = mongo_titles.intersection(neo4j_titles)

        return jsonify({
            'success': True,
            'mongodb_count': len(mongo_titles),
            'neo4j_count': len(neo4j_titles),
            'common_count': len(common_movies),
            'common_movies': sorted(list(common_movies))
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/movies/<movie_name>/users', methods=['GET'])
def list_users_who_rated_movie(movie_name):
    """Liste les utilisateurs qui ont noté un film"""
    try:
        with neo4j_driver.session() as session:
            query = """
            MATCH (p:Person)-[r:REVIEWED]->(m:Movie)
            WHERE m.title =~ $movie_name
            RETURN m.title as movie_title,
                   collect({
                       name: p.name,
                       rating: r.rating,
                       summary: r.summary
                   }) as users
            """
            result = session.run(query, movie_name=f'(?i).*{movie_name}.*')

            record = result.single()

            if not record or not record['movie_title']:
                return jsonify({
                    'success': False,
                    'error': 'Film non trouvé dans Neo4j'
                }), 404

            # Filtrer les utilisateurs qui ont effectivement reviewé
            users = [u for u in record['users'] if u['name'] is not None]

            return jsonify({
                'success': True,
                'movie': record['movie_title'],
                'users_count': len(users),
                'users': users
            }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)