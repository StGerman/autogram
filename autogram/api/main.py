# Description: This file contains the code for the /alive endpoint.

from datetime import datetime
from fastapi import FastAPI

app = FastAPI()

@app.get("/alive")
def check_alive():
    """
    Check if the API is alive and return the current date and time.
    """
    return {"status": "alive", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.root_path("/api")
def check_root():
    """
    Check the root path of the API.
    """
    return {"message": "Welcome to the API root path."}
