# Social Network App
This is a social network application developed using Flask and Neo4j.
## Installation
To install the application, follow these steps:
1. Clone the repository
2. Install the required dependencies
3. Set up Neo4j:
- Install Neo4j on your system.
- Make sure a neo4j db is active and running
- Update the Neo4j URI, username, and password in the `app.py` file.
4. Run the application
- It will run on port 5002
5. End points
- GET /: Home page.
- POST /register: Register a new user.
- PUT /update_user: Update user information.
- POST /send_friend_request: Send a friend request.
- POST /accept_friend_request: Accept a friend request.
- DELETE /remove_friend: Remove a friend.
- POST /create_post: Create a new post.
- POST /like_post: Like a post.
- POST /comment_on_post: Comment on a post.
- POST /create_group: Create a new group.
- POST /join_group: Join an existing group.
- GET /recommend_friends/<username>: Get recommended friends for a user.
= GET /search_users: Search for users based on name, location, or interests.
