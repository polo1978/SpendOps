# Local Tools and Environment

## Key paths

- Workspace: ~/.openclaw/workspace/ (or wherever you set it during onboarding)
- Database: ./spendops.db (relative to workspace root)
- Outputs folder: ./outputs/ (relative to workspace root — create it if missing)
- Skills folder: ./skills/ (relative to workspace root)
- Scripts folder: ./scripts/ (relative to workspace root)

## Python

- Python 3.10+ required. Check with: python3 --version
- Dependencies: pip install sqlite3 (usually built-in)
- The calc_forecast.py script lives at: ./scripts/calc_forecast.py

## LM Studio

- Must be running before any AI analysis is requested.
- Server endpoint: http://127.0.0.1:1234/v1
- Model loaded: qwen2.5 (or whichever Qwen variant you downloaded)
- Check it is running: curl http://127.0.0.1:1234/v1/models

## Node / OpenClaw

- Gateway runs on port 18789 by default.
- Config file: ~/.openclaw/openclaw.json
- Restart gateway: openclaw gateway restart

## Windows note

- OpenClaw runs inside WSL2 on Windows. All paths above are WSL2 paths.
- Your Windows files live at /mnt/c/... inside WSL2.
- LM Studio runs on Windows natively. From WSL2, reach it at http://172.x.x.x:1234 (your WSL2 host IP) or http://host.docker.internal:1234 depending on your setup. If localhost does not work, check your WSL2 host IP with: cat /etc/resolv.conf | grep nameserver
