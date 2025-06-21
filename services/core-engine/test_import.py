import os

# Set required environment variables
os.environ.update({
    'DATABASE_URL': 'sqlite:///test.db',
    'REDIS_URL': 'redis://localhost:6379',
    'SECRET_KEY': 'test-key-for-development',
    'WEAVIATE_URL': 'http://localhost:8080',
    'OPENAI_API_KEY': 'test-key'
})

try:
    from app.main import app
    print("✅ Core Engine imports successfully")
    print(f"✅ App created: {type(app)}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
