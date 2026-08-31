# ⚓ SAIL Freight Decision-Support System Architecture
### SIH26006: Intelligent Freight Forecasting & Vessel Chartering

## 1. System Design Principles

1. **Deterministic Physical Gatekeeping**: Vessel-port matching uses exact physical constraints (Draft, LOA, Beam, Under-Keel Clearance) verified against published Indian Port Handbooks.
2. **Economic Voyage Conversion**: Licensed Baltic Sub-indices (BCI, BPI, BSI, BHSI) are mapped to dollar-per-metric-ton voyage freight using daily Time Charter Equivalent (TCE), VLSFO bunker fuel consumption, steaming distances, and port handling charges.
3. **Risk-Adjusted Decision Timing**: The "Wait or Book" optimizer balances expected freight price decreases against holding/inventory carrying costs and plant stockout penalties.
4. **Transparent Confidence Modeling**: Every forecast produces 80% and 95% confidence intervals based on time-scaled volatility diffusion.

---

## 2. Mathematical Formulation

### A. Dynamic Arrival Draft Calculation
$$\text{Arrival Draft } (d_{\text{arr}}) = d_{\text{light}} + (d_{\text{design}} - d_{\text{light}}) \cdot \sqrt{\min\left(1.0, \frac{\text{Cargo Tonnage}}{\text{Vessel Capacity}}\right)}$$

### B. Voyage Freight Rate Formulation
$$\text{Freight Rate (\$/MT)} = \frac{(T_{\text{sea}} + T_{\text{port}}) \cdot \text{TCE}_{\text{daily}} + (T_{\text{sea}} \cdot F_{\text{sea}} \cdot P_{\text{VLSFO}} + T_{\text{port}} \cdot F_{\text{port}} \cdot P_{\text{MGO}}) + D_{\text{port}} + D_{\text{canal}} + L_{\text{lighterage}}}{\text{Parcel Tonnage}}$$

Where:
- $T_{\text{sea}} = \frac{\text{Distance (NM)}}{\text{Speed (Knots)} \cdot 24} \cdot 1.05$ (Includes 5% sea margin)
- $T_{\text{port}} = \frac{\text{Tonnage}}{\text{Loading Rate}} + \frac{\text{Tonnage}}{\text{Discharge Rate}} + \text{Waiting Days}$
- $F_{\text{sea}}, F_{\text{port}}$ = Fuel consumption per day (MT/day)
- $P_{\text{VLSFO}}, P_{\text{MGO}}$ = Bunker fuel prices ($/MT)
- $D_{\text{port}}, D_{\text{canal}}, L_{\text{lighterage}}$ = Port dues, canal charges, and lightering fees.

### C. "Wait vs Book" Net Cost Optimization
For candidate lock-in day $t \in [0, T_{\text{max}}]$:
$$\text{Net Cost}(t) = \left( \hat{R}(t) \cdot \text{Tonnage} \right) + (t \cdot C_{\text{holding}} \cdot \gamma_{\text{risk}})$$
$$\text{Optimal Day } t^* = \arg\min_{t} \text{Net Cost}(t)$$

If $\text{Net Cost}(0) - \text{Net Cost}(t^*) > \text{Threshold}$, issue **`WAIT TO BOOK`**, else **`BOOK NOW`**.
