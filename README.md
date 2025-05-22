# Workshop 003: Happiness Score Prediction with Kafka Streaming

This project focuses on building a regression model to predict the **Happiness Score** of countries based on socioeconomic indicators. It includes a complete **ETL**, **feature engineering**, **model training**, and **Kafka-based real-time streaming** pipeline with PostgreSQL storage.

## Objective

To process happiness survey data (2015–2019), build a machine learning model for predicting happiness scores, and deploy a real-time prediction pipeline using Kafka and a PostgreSQL database.

---

## Project Structure

├── data/
│ ├── raw/ # CSVs from 2015–2019
│ └── processed/ # Cleaned and merged datasets
├── model/
│ ├── trained_stacking_model.pkl
│ ├── imputer.pkl
│ ├── target_encoder.pkl
│ └── xgb_model.json
├── kafka/
│ ├── kafka_producer.py
│ └── kafka_consumer.py
├── notebooks/
│ ├── 01_eda.ipynb
│ ├── 02_modeling.ipynb
│ └── 03_streaming_pipeline.ipynb
├── .env
├── requirements.txt
├── docker-compose.yml
└── README.md
---

## Dataset Description

The project merges 5 datasets (2015–2019), each containing indicators such as:

- `Economy (GDP per Capita)`
- `Health (Life Expectancy)`
- `Family`
- `Freedom`
- `Trust (Government Corruption)`
- `Generosity`
- `Country`
- `Happiness Score` (target)

Missing and duplicate columns were cleaned, and schemas were harmonized.

---

## Modeling Pipeline

1. **Data Cleaning & Preprocessing**
   - Drop sparse columns (e.g., confidence intervals)
   - Impute missing values (mean for numeric)
   - Encode country with `TargetEncoder`

2. **Modeling**
   - Base models: Linear, Ridge, Lasso, KNN, RF, XGBoost
   - Final model: `StackingRegressor` with RF, XGBoost, and KNN
   - Meta-learner: Ridge (α = 10.0)

3. **Best Performance**
R² = 0.9640
MAE = 0.1543
MSE = 0.0449


---

##  Streaming Pipeline

###  Producer
- Reads `X_test.csv` + `y_test.csv`
- Sends one row every 0.5s via Kafka topic `happiness_test`

### Consumer
- Loads model + encoders
- Applies preprocessing
- Predicts score with XGBoost
- Stores results in PostgreSQL

###  Database Table: `predictions`
```sql
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
timestamp TIMESTAMP
 Docker Setup
Start all services:
```
# Run the Pipeline

## Requirements
Install required Python packages (Python 3.10+):

```bash
pip install -r requirements.txt
```

## Create a .env file:

```bash
DB_NAME=happines_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=5432
```
## create manually in postgres the database: 
```sql
CREATE DATABASE happines_db;
```

To start all services, run:

```bash
docker compose up --build
```
This will launch the following components:

- Zookeeper  
- Kafka  
- PostgreSQL  
- Producer  
- Consumer











