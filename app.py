from flask import Flask, request, jsonify
from neo4j import GraphDatabase

app = Flask(__name__)

class SocialNetworkApp:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def register_user(self, name, age, location, interests):
        with self.driver.session() as session:
            session.execute_write(self._create_user, name, age, location, interests)

    @staticmethod
    def _create_user(tx, name, age, location, interests):
        tx.run("CREATE (u:User {name: $name, age: $age, location: $location, interests: $interests})",
               name=name, age=age, location=location, interests=interests)

    def update_user_info(self, name, age=None, location=None, interests=None):
        with self.driver.session() as session:
            session.execute_write(self._update_user, name, age, location, interests)

    @staticmethod
    def _update_user(tx, name, age, location, interests):
        query = "MATCH (u:User {name: $name}) SET "
        params = {"name": name}
        if age:
            query += "u.age = $age, "
            params["age"] = age
        if location:
            query += "u.location = $location, "
            params["location"] = location
        if interests:
            query += "u.interests = $interests, "
            params["interests"] = interests
        query = query.rstrip(", ")
        tx.run(query, **params)

    def send_friend_request(self, from_user, to_user):
        with self.driver.session() as session:
            session.execute_write(self._send_friend_request, from_user, to_user)

    @staticmethod
    def _send_friend_request(tx, from_user, to_user):
        query = (
            "MATCH (from:User {name: $from_user}), (to:User {name: $to_user}) "
            "MERGE (from)-[:OUTGOING_REQUEST]->(to)"
        )
        tx.run(query, from_user=from_user, to_user=to_user)

    def accept_friend_request(self, from_user, to_user):
        with self.driver.session() as session:
            session.execute_write(self._accept_friend_request, from_user, to_user)

    @staticmethod
    def _accept_friend_request(tx, from_user, to_user):
        query = (
            "MATCH (from:User {name: $from_user})-[r:OUTGOING_REQUEST]->(to:User {name: $to_user}) "
            "CREATE (from)-[:FRIENDS_WITH {since: date()}]->(to) "
            "CREATE (to)-[:FRIENDS_WITH {since: date()}]->(from) "
            "DELETE r"
        )
        tx.run(query, from_user=from_user, to_user=to_user)

    def remove_friend(self, user1, user2):
        with self.driver.session() as session:
            session.execute_write(self._delete_friendship, user1, user2)

    @staticmethod
    def _delete_friendship(tx, user1, user2):
        tx.run("MATCH (u1:User {name: $user1})-[f:FRIENDS_WITH]-(u2:User {name: $user2}) DELETE f",
               user1=user1, user2=user2)

    def create_post(self, user, content):
        with self.driver.session() as session:
            session.execute_write(self._create_post, user, content)

    @staticmethod
    def _create_post(tx, user, content):
        tx.run("MATCH (u:User {name: $user}) "
               "CREATE (p:Post {content: $content, timestamp: datetime()})-[:POSTED_BY]->(u)",
               user=user, content=content)

    def like_post(self, user, post_content):
        with self.driver.session() as session:
            session.execute_write(self._like_post, user, post_content)

    @staticmethod
    def _like_post(tx, user, post_content):
        tx.run("MATCH (u:User {name: $user}), (p:Post {content: $post_content}) "
               "MERGE (u)-[:LIKES]->(p)",
               user=user, post_content=post_content)

    def comment_on_post(self, user, post_content, comment_text):
        with self.driver.session() as session:
            session.execute_write(self._comment_on_post, user, post_content, comment_text)

    @staticmethod
    def _comment_on_post(tx, user, post_content, comment_text):
        tx.run("MATCH (u:User {name: $user}), (p:Post {content: $post_content}) "
               "CREATE (u)-[:COMMENTED_ON {text: $comment_text}]->(p)",
               user=user, post_content=post_content, comment_text=comment_text)

    def create_group(self, name, description):
        with self.driver.session() as session:
            session.execute_write(self._create_group, name, description)

    @staticmethod
    def _create_group(tx, name, description):
        tx.run("CREATE (group:Group {name: $name, description: $description})",
               name=name, description=description)

    def join_group(self, user, group_name):
        with self.driver.session() as session:
            session.execute_write(self._join_group, user, group_name)

    @staticmethod
    def _join_group(tx, user, group_name):
        tx.run("MATCH (u:User {name: $user}), (g:Group {name: $group_name}) "
               "MERGE (u)-[:JOIN {since: date()}]->(g)",
               user=user, group_name=group_name)
        
    def recommend_friends(self, user):
        with self.driver.session() as session:
            result = session.execute_read(self._recommend_friends, user)
            return [record["recommended_friend"] for record in result]

    @staticmethod
    def _recommend_friends(tx, user):
        query = """
        MATCH (u:User {name: $user})-[:FRIENDS_WITH]->(friend)-[:FRIENDS_WITH]->(recommended_friend)
        WHERE NOT (u)-[:FRIENDS_WITH]->(recommended_friend) AND u <> recommended_friend
        RETURN DISTINCT recommended_friend.name AS recommended_friend
        """
        result = tx.run(query, user=user)
        return result

    def search_users(self, name=None, location=None, interests=None):
        with self.driver.session() as session:
            result = session.execute_read(self._search_users, name, location, interests)
            return [record["user"] for record in result]

    @staticmethod
    def _search_users(tx, name, location, interests):
        query = "MATCH (u:User) WHERE "
        conditions = []
        params = {}
        if name:
            conditions.append("u.name CONTAINS $name")
            params["name"] = name
        if location:
            conditions.append("u.location = $location")
            params["location"] = location
        if interests:
            conditions.append("ANY(interest IN u.interests WHERE interest IN $interests)")
            params["interests"] = interests
        query += " AND ".join(conditions)
        return tx.run(query, **params)    


# Initialize the SocialNetworkApp
app_soc_net = SocialNetworkApp("bolt://localhost:7687", "neo4j", "12345678")

@app.route("/")
def home():
    return jsonify({"message": "Hello, Welcome to the Social Network API"})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    app_soc_net.register_user(data['name'], data['age'], data['location'], data['interests'])
    return jsonify({"message": "User registered successfully"}), 201


@app.route('/update', methods=['PUT'])
def update():
    data = request.get_json()
    app_soc_net.update_user_info(data['name'], data.get('age'), data.get('location'), data.get('interests'))
    return jsonify({"message": "User info updated successfully"}), 200


@app.route('/send_friend_request', methods=['POST'])
def send_friend_request():
    data = request.get_json()
    app_soc_net.send_friend_request(data['from_user'], data['to_user'])
    return jsonify({"message": "Friend request sent"}), 200


@app.route('/accept_friend_request', methods=['POST'])
def accept_friend_request():
    data = request.get_json()
    app_soc_net.accept_friend_request(data['from_user'], data['to_user'])
    return jsonify({"message": "Friend request accepted"}), 200


@app.route('/remove_friend', methods=['DELETE'])
def remove_friend():
    data = request.get_json()
    app_soc_net.remove_friend(data['user1'], data['user2'])
    return jsonify({"message": "Friend removed"}), 200


@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.get_json()
    app_soc_net.create_post(data['user'], data['content'])
    return jsonify({"message": "Post created"}), 201


@app.route('/like_post', methods=['POST'])
def like_post():
    data = request.get_json()
    app_soc_net.like_post(data['user'], data['post_content'])
    return jsonify({"message": "Post liked"}), 200


@app.route('/comment_on_post', methods=['POST'])
def comment_on_post():
    data = request.get_json()
    app_soc_net.comment_on_post(data['user'], data['post_content'], data['comment_text'])
    return jsonify({"message": "Comment added"}), 200


@app.route('/create_group', methods=['POST'])
def create_group():
    data = request.get_json()
    app_soc_net.create_group(data['name'], data['description'])
    return jsonify({"message": "Group created"}), 201


@app.route('/join_group', methods=['POST'])
def join_group():
    data = request.get_json()
    app_soc_net.join_group(data['user'], data['group_name'])
    return jsonify({"message": "Joined group"}), 200

@app.route('/recommend_friends', methods=['GET'])
def recommend_friends():
    user = request.args.get('user')
    recommended_friends = app_soc_net.recommend_friends(user)
    return jsonify({"recommended_friends": recommended_friends})

@app.route('/search_users', methods=['GET'])
def search_users():
    name = request.args.get('name')
    location = request.args.get('location')
    interests = request.args.getlist('interests')
    search_results = app_soc_net.search_users(name, location, interests)
    return jsonify({"search_results": search_results})


if __name__ == '__main__':
    app.run(debug=True, port=5002)
    app_soc_net.close()