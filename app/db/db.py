from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root'
    app.config['MYSQL_DB'] = 'musik'
    app.config['MYSQL_HOST'] = 'localhost'

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

        mysql.connection.commit()
        cursor.close()