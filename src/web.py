from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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


class PromptRequest(BaseModel):
    command: str


@app.get("/")
async def ping():
    return "Pong"


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
            # Should not happen based on parse_and_execute_command logic
            # but good to have a fallback.
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
