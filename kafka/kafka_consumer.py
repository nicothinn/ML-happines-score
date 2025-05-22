import sys
import os
from dotenv import load_dotenv

print("Starting kafka_consumer.py...")

# Load environment variables from .env
load_dotenv(dotenv_path=".env")

# Access .env variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

try:
    import json
    import pandas as pd
    import xgboost as xgb
    from kafka import KafkaConsumer
    import psycopg2
    import joblib
except Exception as e:
    print("Error importing modules:", e)
    sys.exit(1)

try:
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id SERIAL PRIMARY KEY,
        economy FLOAT,
        health FLOAT,
        family FLOAT,
        freedom FLOAT,
        trust FLOAT,
        generosity FLOAT,
        country_enc FLOAT,
        country_name TEXT,
        predicted_score FLOAT,
        real_score FLOAT,
        error FLOAT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    print("Connected to PostgreSQL and verified table.")
except Exception as e:
    print("Error during connection or table creation:", e)
    sys.exit(1)

try:
    print("Loading model and transformers...")
    booster = xgb.Booster()
    booster.load_model("model/xgb_model.json")
    imputer = joblib.load("model/imputer.pkl")
    encoder = joblib.load("model/target_encoder.pkl")
    print("Model and transformers loaded.")
except Exception as e:
    print("Error loading models:", e)
    sys.exit(1)

try:
    print("Connecting to Kafka...")
    consumer = KafkaConsumer(
        "happiness_test",
        bootstrap_servers="kafka-test:9092",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="happiness_group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )
    print("Connected to Kafka. Waiting for messages...")
except Exception as e:
    print("Error connecting to Kafka:", e)
    sys.exit(1)

for message in consumer:
    try:
        data = message.value
        print("Message received:", data)

        if "Happiness Score" not in data:
            print("'Happiness Score' missing. Skipping message.")
            continue

        real_score = float(data.pop("Happiness Score"))
        country_name = data["Country"]
        df = pd.DataFrame([data])

        numeric_cols = [
            "Economy (GDP per Capita)",
            "Health (Life Expectancy)",
            "Family",
            "Freedom",
            "Trust (Government Corruption)",
            "Generosity"
        ]
        df[numeric_cols] = imputer.transform(df[numeric_cols])
        df["Country_enc"] = encoder.transform(df["Country"])
        df = df.drop(columns=["Country"])

        X_input = df[numeric_cols + ["Country_enc"]]
        dmatrix = xgb.DMatrix(X_input)
        predicted_score = float(booster.predict(dmatrix)[0])
        error = float(predicted_score - real_score)

        print(f"Prediction: {predicted_score:.4f} | Real: {real_score:.4f} | Error: {error:.4f}")

        cursor.execute("""
            INSERT INTO predictions (
                economy, health, family, freedom, trust, generosity, 
                country_enc, country_name, predicted_score, real_score, error
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            float(data["Economy (GDP per Capita)"]),
            float(data["Health (Life Expectancy)"]),
            float(data["Family"]),
            float(data["Freedom"]),
            float(data["Trust (Government Corruption)"]),
            float(data["Generosity"]),
            float(df["Country_enc"].iloc[0]),
            country_name,
            predicted_score,
            real_score,
            error
        ))
        conn.commit()
        print("Record inserted into PostgreSQL.")

    except Exception as e:
        print("Error processing message:", e)
