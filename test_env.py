from dotenv import load_dotenv
import os

load_dotenv()

print("APP_NAME:", os.getenv("APP_NAME"))
print("ENV:", os.getenv("ENV"))
print("SECRET_KEY:", os.getenv("SECRET_KEY")[:20] + "..." if os.getenv("SECRET_KEY") else "Not set")
print("GROQ_API_KEY:", "Set" if os.getenv("GROQ_API_KEY") else "Not set")