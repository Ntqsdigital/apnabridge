import pymysql

def init_db():
    try:
        connection = pymysql.connect(
            host="localhost",       # change if needed
            user="root",            # your MySQL username
            password="Parlapalli@56",            # your MySQL password
            database="apnabridge",  # your database name
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Database connected successfully!")
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None






