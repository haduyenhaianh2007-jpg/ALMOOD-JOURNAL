from dotenv import load_dotenv
import os

load_dotenv()
print("GOOGLE_API_KEY =", os.getenv("GOOGLE_API_KEY"))
print("HF_TOKEN =", os.getenv("HF_TOKEN"))
