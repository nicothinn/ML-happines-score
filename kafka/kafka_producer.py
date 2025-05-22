import pandas as pd
import json
from kafka import KafkaProducer
import time

X_test = pd.read_csv("data/processed/X_test.csv")
y_test = pd.read_csv("data/processed/y_test.csv")

X_test["Happiness Score"] = y_test

producer = KafkaProducer(
    bootstrap_servers="kafka-test:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

for i, row in X_test.iterrows():
    message = row.to_dict()
    producer.send("happiness_test", value=message)
    print(f"Enviado: {message}")
    time.sleep(0.5)  

producer.flush()
producer.close()
