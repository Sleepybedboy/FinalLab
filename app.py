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

@app.route('/movies/search', methods=['GET'])
def list_specific_movie():
    """Recherche un film par nom OU par acteur"""
    movie_name = request.args.get('name')
    actor_name = request.args.get('actor')

    if not movie_name and not actor_name:
        return jsonify({
            'success': False,
            'error': 'Paramètre "name" ou "actor" requis'
        }), 400

    try:
        query = {}
        if movie_name:
            query['title'] = {'$regex': movie_name, '$options': 'i'}
        if actor_name:
            query['cast'] = {'$regex': actor_name, '$options': 'i'}

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

        movies = list(movies_collection.find(query, projection).limit(50))

        return jsonify({
            'success': True,
            'count': len(movies),
            'movies': movies
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/movies/<movie_name>', methods=['PUT'])
def update_movie_info(movie_name):
    """Met à jour les informations d'un film"""
    try:
        update_data = request.get_json()

        if not update_data:
            return jsonify({
                'success': False,
                'error': 'Données de mise à jour requises'
            }), 400

        # Supprimer _id s'il est présent
        update_data.pop('_id', None)

        result = movies_collection.update_one(
            {'title': {'$regex': f'^{movie_name}$', '$options': 'i'}},
            {'$set': update_data}
        )

        if result.matched_count == 0:
            return jsonify({
                'success': False,
                'error': 'Film non trouvé'
            }), 404

        return jsonify({
            'success': True,
            'message': f'Film "{movie_name}" mis à jour',
            'modified_count': result.modified_count
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)