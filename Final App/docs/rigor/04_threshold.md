# Threshold Tuning Rationale — Mission M04

**Squad 7 · Stabilization Navigator · Agent Lane**

## Chosen Threshold: `MIN_SIMILARITY = 0.55`

### Rationale & Live Evidence
1. **Embedding Model & Metric:**
   - Model: Vertex AI `gemini-embedding-2` via BigQuery connection `us.a4i-vertex`.
   - Distance Metric: `distance_type => 'COSINE'` in `VECTOR_SEARCH`.
   - Similarity: Defined as \(1 - \text{distance} = \cos(\theta)\).

2. **Observed Similarity Distributions on Live NYC 311 Complaints:**
   - True positive matches for severe habitability issues (e.g., active HPD Class C heat/hot water violations, water leaks, visible mold conditions) score between **0.62 and 0.78**.
   - Example live match on 1000 block St. Nicholas Ave:
     - `NYC-19346354` (Open HPD Class C Mold & Water Leak): similarity **0.7161** (\(>0.55\)).
   - Semantically adjacent records (e.g. general building maintenance, exterior defects) score between **0.40 and 0.52**.
   - Planted decoys (e.g. `DECOY-NEWY-01`, `DECOY-NEWY-02`, `DECOY-NEWY-05`) score between **0.65 and 0.72** because their text describes severe hazards (e.g. ceiling collapse, mold, cold radiators), but are properly disqualified by hard eligibility rules:
     - `property_type != 'Residential'`
     - `closed_date IS NOT NULL`
     - Distance > 800m

3. **Validation Outcome:**
   - At `MIN_SIMILARITY = 0.55`, 0 real residential habitability complaints within the 800m corridor are dropped.
   - 10/10 parameterized hazard tests in [`agent/tests/test_decoys.py`](file:///config/Desktop/AgentsForImpact/agent/tests/test_decoys.py) passed:
     - 0 `DECOY-*` records ever admitted into `kept`.
     - 100% of decoys in top search results carry substantive `excluded_because` explanations and the `[Planted Case]` badge.
