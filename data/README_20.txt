TRACE 20‑Event Subset
======================
Files
- trace_reduced_20.csv / .json : Deterministic 20‑sample subset for demos, unit tests, and quick iteration.
- trace_llm_20.json            : 20 prompt→completion pairs derived from the subset for Decision xApp testing.

Schema (columns)
timestamp, region_id, tower_id, agent_id, neighbors, capacity_users, connected_users, bandwidth_utilization_pct,
rsrq_db, packet_loss_pct, latency_ms, cpu_util_pct, power_voltage_v, event_type, tower_radius_km, desired_radius_km,
coverage_gap_pct, adjust_radius_action, adjust_reason, detected_error, detection_confidence, signals_used,
action_executed, action_reason, healed_now, auto, human_in_loop

Typical uses
- Quick smoke tests of ingestion/ETL and dashboards
- Deterministic unit tests in CI
- LLM prompt tuning with trace_llm_20.json
