import json

events = []
with open('tmp_test/test_payroll_journey_reaches_approval_executes_mock_and_exposes_ai_log0/events.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        events.append(json.loads(line))

for e in events:
    if "intent" in str(e):
        print(e.get("event_code", e.get("event")), e.get("output_summary"))
