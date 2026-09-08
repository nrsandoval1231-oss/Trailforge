# Trailforge Campaign 001

The local mechanics campaign ran 10,000 seeded synthetic scenarios with the
`KEYWORD` control and `BASELINE_A`.

- Status: PASS
- Seed: 12
- Invariant failures: 0 for both policies
- Throughput: approximately 7,651 runs/second on the development machine
- Result boundary: this validates mechanics and reproducibility only; it does
  not establish real-world forecasting accuracy.
- Full-family regression: 40/40 registered templates executed through both
  policies with zero invariant failures.
- CLI integration: all 10 declared modes returned machine-readable `PASS`.
