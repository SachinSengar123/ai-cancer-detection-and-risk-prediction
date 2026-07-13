import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS cancer_app")
        print("✅ Database 'cancer_app' created successfully")
        
        cursor.close()
        conn.close()
        
        print("🎉 Database setup completed!")
        print("📝 Now run: python app.py")
        
    except mysql.connector.Error as e:
        print(f"❌ Database setup failed: {e}")
        print("💡 Make sure MySQL is running and credentials are correct")

if _name_ == '_main_':
    setup_database()