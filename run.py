import uvicorn

if __name__ == "__main__":
    # Import settings here to avoid circular imports
    try:
        from app.config import settings
        
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.log_level.lower()
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Make sure you have:")
        print("1. Created a .env file with OPENAI_API_KEY")
        print("2. Installed all requirements: pip install -r requirements.txt")
        print("3. Created the data/ directory with CSV files")
        
        # Fallback - start with basic settings
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )