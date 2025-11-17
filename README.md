Movies API – Flask, MongoDB Atlas & Neo4j

Ce projet propose une API permettant d’explorer des films provenant de MongoDB Atlas et du Neo4j Sandbox (Movies Dataset).
L'API permet de lister, rechercher et mettre à jour des films, ainsi que d’obtenir des informations croisées entre les deux bases.

Requirements

Le projet nécessite les dépendances suivantes :

Flask==3.0.0
uvicorn[standard]==0.32.0
pymongo==4.6.1
neo4j==5.16.0
python-dotenv==1.0.0


Installer les dépendances via :

pip install -r requirements.txt

Installation
1. Cloner le projet
   git clone <url-du-projet>
   cd <nom-du-dossier>

2. Créer un environnement virtuel
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows

3. Installer les dépendances
   pip install -r requirements.txt

Configuration (.env)

modifier le fichier .env à la racine du projet contenant :

MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGO_DB=sample_mflix

NEO4J_URI=bolt://<IP_Adress>:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>


Remplacer les valeurs par celles de votre environnement MongoDB Atlas et Neo4j Sandbox.

Lancer le serveur
python app.py


Le serveur sera accessible à l’adresse :

http://localhost:5000

Endpoints disponibles
1. Lister tous les films (MongoDB)
   GET /movies?page=1&limit=20

2. Rechercher un film par nom ou acteur
   GET /movies/search?name=Inception
   GET /movies/search?actor=Tom%20Hanks

3. Mettre à jour les informations d’un film
   PUT /movies/<movie_name>

4. Obtenir les films communs entre MongoDB et Neo4j
   GET /movies/common

5. Liste des utilisateurs ayant noté un film (Neo4j)
   GET /movies/<movie_name>/users

6. Obtenir les informations d’un utilisateur et les films qu’il a notés
   GET /users/<user_name>

7. Health Check
   GET /health