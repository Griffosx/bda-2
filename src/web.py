import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.roll_simulation import (
    DiceParsingError,
    DiceResult,
    DiceRollStats,
    parse_and_execute_command,
)

app = FastAPI(
    title="Dice API",
    description="API for Dice",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define the path to the static directory where frontend build output will be placed
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")

# Only mount static files if the directory exists (for development mode)
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


class PromptRequest(BaseModel):
    command: str


@app.get("/")
async def serve_frontend():
    """Serves the main frontend application."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        # This helps during local development if static files aren't built/copied yet
        # In production (Docker), this file should always exist if the build succeeded.
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)


@app.post("/prompt")
async def handle_prompt(request: PromptRequest):
    """
    Accepts a dice command string, executes it, and returns the result.

    Handles commands like 'roll 1d6' or 'stats 10 2d8+1'.
    """
    try:
        result = parse_and_execute_command(request.command)

        if isinstance(result, DiceResult):
            # Convert DiceResult to a dict for consistent JSON output
            response_data = {
                "type": "roll",
                "data": {
                    "individual_values": result.individual_values,
                    "modifier": result.modifier,
                    "total": result.total,
                },
            }
        elif isinstance(result, DiceRollStats):
            # Convert DiceRollStats to a dict
            response_data = {
                "type": "stats",
                "data": {
                    "count": result.count,
                    "minimum": result.minimum,
                    "maximum": result.maximum,
                    "mean": result.mean,
                    "median": result.median,
                    "std_dev": result.std_dev,
                    "bins": result.bins,
                },
            }
        else:
            # Should not happen but good to have a fallback.
            raise HTTPException(
                status_code=500, detail="Internal server error: Unexpected result type"
            )

        return response_data

    except (ValueError, DiceParsingError) as e:
        # Catch parsing errors or invalid command errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch unexpected errors
        # Log the error here in a real application
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
