import datetime
import json
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


def get_latest_raw_file():
    raw_files = list(RAW_DIR.glob("*.json"))
    if not raw_files:
        raise FileNotFoundError("No raw JSON files found in data/raw")
    
    raw_file = max(raw_files, key=lambda f: f.stat().st_mtime)
    print(f"[INFO] Using latest raw file: {raw_file.name}")
    return raw_file


def parse_json_to_dataframe(raw_file):
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    data_rows = []
    for orders in raw_data["data"]["elements"]:
        tags = orders.get("tags") or {}
        data_rows.append(
            {
                "order_id": orders.get("id"),
                "name": tags.get("name"),
                "amenity": tags.get("amenity"),
                "cuisine": tags.get("cuisine"),
                "place": tags.get("addr:city"),
                "order_type": orders.get("type"),
                "lat": orders.get("lat"),
                "lon": orders.get("lon"),
            }
        )
    
    columns = ["order_id", "name", "amenity", "cuisine", "place", "order_type", "lat", "lon"]
    df = pd.DataFrame(data_rows, columns=columns)
    df["order_id"] = pd.to_numeric(df["order_id"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df


def json_to_csv():
    raw_file = get_latest_raw_file()
    orders_df = parse_json_to_dataframe(raw_file)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = PROCESSED_DIR / f"orders_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "part-00000.csv"
    
    orders_df.to_csv(output_file, index=False, header=True)
    print(f"[SUCCESS] Processed orders saved to {output_file}")

    return orders_df


if __name__ == "__main__":
    json_to_csv()
