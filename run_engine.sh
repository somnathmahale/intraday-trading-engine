#!/bin/bash
cd /Users/somnathmahale/projects/intraday_trading
source venv/bin/activate
python engine_v3.py >> engine.log 2>&1
