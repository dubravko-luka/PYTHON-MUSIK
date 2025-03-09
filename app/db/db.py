from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root'
    app.config['MYSQL_DB'] = 'musik'
    app.config['MYSQL_HOST'] = '127.0.0.1'
    app.config['MYSQL_PORT'] = 3307

    mysql.init_app(app)

    with app.app_context():
        cursor = mysql.connection.cursor()
        
        user_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            password VARCHAR(512)
        );
        """
        cursor.execute(user_table_query)

        music_table_query = """
        CREATE TABLE IF NOT EXISTS music (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_path VARCHAR(255) NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
        cursor.execute(music_table_query)

        favourites_table_query = """
        CREATE TABLE IF NOT EXISTS favourites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            music_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (music_id) REFERENCES music(id),
            UNIQUE KEY unique_favourite (user_id, music_id)
        );
        """
        cursor.execute(favourites_table_query)

        albums_table_query = """
        CREATE TABLE IF NOT EXISTS albums (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            user_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
        cursor.execute(albums_table_query)

        album_music_table_query = """
        CREATE TABLE IF NOT EXISTS album_music (
            album_id INT NOT NULL,
            music_id INT NOT NULL,
            PRIMARY KEY (album_id, music_id),
            FOREIGN KEY (album_id) REFERENCES albums(id),
            FOREIGN KEY (music_id) REFERENCES music(id)
        );
        """
        cursor.execute(album_music_table_query)

        friends_table_query = """
        CREATE TABLE IF NOT EXISTS friends (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            friend_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (friend_id) REFERENCES users(id)
        );
        """
        cursor.execute(friends_table_query)

        friend_requests_table_query = """
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            requester_id INT NOT NULL,
            recipient_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (requester_id) REFERENCES users(id),
            FOREIGN KEY (recipient_id) REFERENCES users(id)
        );
        """
        cursor.execute(friend_requests_table_query)

        mysql.connection.commit()
        cursor.close()