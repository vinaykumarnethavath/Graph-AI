import uvicorn
import os
from backend.api.app import app

if __name__ == "__main__":
    # Get port from environment variable for cloud deployment
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "backend.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=False if os.environ.get("PORT") else True,
        log_level="info"
    )
