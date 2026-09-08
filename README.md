# Trailforge
#
Trailforge is Athena's research-only Procurement Arena: a deterministic
environment for testing evidence-trail policies. It has no scraper, customer
outreach, bid autofill, submission, broker, or execution authority.

## Check
`$env:PYTHONPATH="src"; python -m pytest -q`

Run a comparison with:

`$env:PYTHONPATH="src"; python -m athena_procurement_arena compare --count 1000 --seed 21`

Historical fixtures are deliberately `UNVERIFIED` until point-in-time
availability is independently established.
