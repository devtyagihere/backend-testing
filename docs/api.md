# 📡 SAIL Freight Forecasting API Reference

## Base URL
`/api/v1`

---

## Endpoints

### 1. System Health
* **`GET /api/v1/health`**
* Returns service status and engine version.

### 2. Port & Constraint Registry
* **`GET /api/v1/ports/indian`**
  * Returns list of all 7 Indian East Coast Ports (Paradip, Vizag, Gangavaram, Dhamra, Gopalpur, Haldia, Sagar-Sandheads) with max draft, LOA, beam, and handling rates.
* **`GET /api/v1/ports/origin`**
  * Returns major loading origin ports (Australia, Indonesia, Mozambique, Russia, USA).

### 3. Vessel Registry
* **`GET /api/v1/vessels`**
  * Returns bulk carrier classes (Handysize, Handymax, Supramax, Ultramax, Panamax, Kamsarmax, Capesize, Newcastlemax).

### 4. Decision Optimizer
* **`POST /api/v1/optimize`**
  * **Payload:**
    ```json
    {
      "parcel_tonnage_mt": 75000,
      "commodity": "Coking Coal",
      "origin_port_id": "AUHPT",
      "dest_port_id": "INPRT",
      "laycan_days_ahead": 21,
      "risk_tolerance": "BALANCED",
      "holding_cost_usd_per_day": 2500.0
    }
    ```
  * **Response:** Recommendation (`WAIT` or `BOOK_NOW`), optimal booking day, confidence %, expected savings in USD and %, vessel matches, voyage cost breakdown, and risk assessment.

### 5. Historical Backtest
* **`POST /api/v1/backtest?period_days=365&origin_port_id=AUHPT&dest_port_id=INPRT&parcel_size_mt=75000`**
  * Returns 12-month backtest simulation comparing model timing vs naive spot booking.

### 6. Official SIH Minimum Demo
* **`GET /api/v1/demo/75k-coal-australia-paradip`**
  * Runs the official 75,000 MT coal parcel demo from Australia to Paradip.
