from pathlib import Path
import numpy as np
import pandas as pd

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CURATED_DIR = Path(__file__).parent.parent / "data" / "curated"

CITY_CENTER_LAT = 30.7333
CITY_CENTER_LON = 76.7794


def get_latest_processed_file():
    processed_dirs = [p for p in PROCESSED_DIR.iterdir() if p.is_dir()]
    if not processed_dirs:
        raise FileNotFoundError("No processed directories found in data/processed")
    return max(processed_dirs, key=lambda f: f.stat().st_mtime)


def clean_data(df):
    df = df.copy()
    valid_name = df["name"].notna() & (df["name"].astype(str).str.strip() != "")
    valid_lat = df["lat"].notna()
    valid_lon = df["lon"].notna()
    df = df[valid_name & valid_lat & valid_lon].copy()
    
    df["cuisine"] = df["cuisine"].fillna("unknown")
    df["cuisine"] = df["cuisine"].astype(str).str.strip().str.lower()
    df = df.drop_duplicates(subset=["name", "lat", "lon"])
    df["place"] = df["place"].fillna("unknown")
    
    return df


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def feature_engineering(df):
    R = 6371.0
    df = df.copy()
    df["customer_lat"] = CITY_CENTER_LAT
    df["customer_lon"] = CITY_CENTER_LON

    lat_rad = np.radians(df["lat"].astype(float))
    lon_rad = np.radians(df["lon"].astype(float))
    cust_lat_rad = np.radians(df["customer_lat"].astype(float))
    cust_lon_rad = np.radians(df["customer_lon"].astype(float))

    dlat = lat_rad - cust_lat_rad
    dlon = lon_rad - cust_lon_rad

    a = np.sin(dlat / 2.0)**2 + np.cos(lat_rad) * np.cos(cust_lat_rad) * np.sin(dlon / 2.0)**2
    df["distance"] = 2 * R * np.arcsin(np.sqrt(a))

    return df


def transform_data():
    processed_file = get_latest_processed_file()
    print(f"[INFO] Using latest processed file: {processed_file.name}")

    if processed_file.is_dir():
        csv_files = list(processed_file.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {processed_file}")
        df = pd.read_csv(csv_files[0])
    else:
        df = pd.read_csv(processed_file)

    df_clean = clean_data(df)

    output_clean_dir = CURATED_DIR / "orders_clean"
    output_clean_dir.mkdir(parents=True, exist_ok=True)
    output_clean = output_clean_dir / "part-00000.csv"
    df_clean.to_csv(output_clean, index=False, header=True)
    print(f"[SUCCESS] Cleaned data saved to: {output_clean}")

    df_featured = feature_engineering(df_clean)

    output_featured_dir = CURATED_DIR / "orders_featured"
    output_featured_dir.mkdir(parents=True, exist_ok=True)
    output_featured = output_featured_dir / "part-00000.csv"
    df_featured.to_csv(output_featured, index=False, header=True)
    print(f"[SUCCESS] Featured data saved to: {output_featured}")

    return df_featured


if __name__ == "__main__":
    transform_data()
