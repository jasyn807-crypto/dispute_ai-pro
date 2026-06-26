import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Turn off reload in production to avoid extra processes in resource-constrained environments
    reload = os.environ.get("ENV", "development") == "development"
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload)

