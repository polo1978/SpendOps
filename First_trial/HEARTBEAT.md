# Heartbeat Checklist

Run this check silently on each heartbeat cycle. Only message the user if something needs attention.

## Checks

1. Are there any subscriptions renewing in the next 30 days with no owner assigned? If yes, alert the user.
2. Are there any budget lines where actual spend this month exceeds plan by more than 15%? If yes, alert the user.
3. Is the LM Studio server reachable at http://127.0.0.1:1234/v1/models? If not, skip analysis silently (the server may be intentionally off).

## What to say if alerting

Keep it short. One sentence per item. End with: "Reply 'run brief' to get a full analysis."

## What not to do

Do not run the full pipeline on heartbeat. Too expensive. Just check the database for the conditions above.
