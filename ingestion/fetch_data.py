import requests
import datetime as dt
import json
import time
from pathlib import Path

# query for overpass to get api for project api getting from link is large string that why calling query like this

API_URL = "https://overpass-api.de/api/interpreter"

OVERPASS_QUERY = (
    "[out:json][timeout:25];"
    "area[\"name\"=\"Chandigarh\"][admin_level=6]->.searchArea;"
    "("
    "node[\"amenity\"=\"restaurant\"](area.searchArea);"
    "node[\"amenity\"=\"fast_food\"](area.searchArea);"
    "node[\"amenity\"=\"cafe\"](area.searchArea);"
    ");"
    "out body;"
)

HEADERS = {
    "User-Agent": "FoodDeliveryPipeline/1.0 (contact@fooddeliverypipeline.org)",
    "Accept": "application/json"
}

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"


def fetch_data():
    """
    Fetch data from Overpass API with basic retry logic.
    This helps handle transient 5xx / timeout errors from the public API.
    """
    max_retries = 3
    backoff_seconds = 5

    # Fetched Data with retries
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                API_URL,
                data={"data": OVERPASS_QUERY},
                headers=HEADERS,
                timeout=60
            )
            response.raise_for_status()
            api_data = response.json()
            break
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            if attempt == max_retries:
                # Re-raise after final attempt so the pipeline can fail loudly
                raise
            print(
                f"[WARN] Overpass API request failed (attempt {attempt}/{max_retries}): {e}. "
                f"Retrying in {backoff_seconds} seconds..."
            )
            time.sleep(backoff_seconds)

    # metadata
    raw_payload = {
        "metadata": {
            "source": "overpass_turbo",
            "endpoint": API_URL,
            "ingestion_timestamp": dt.datetime.now(dt.timezone.utc).isoformat()
        },
        "data": api_data
    }

    #  saving data to files
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"orders_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    file_path = RAW_DIR / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Raw data saved to: {file_path}")
    return raw_payload
