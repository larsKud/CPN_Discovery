### Setup:
Create venv
```Bash
python3 -m venv .venv
```

Activate venv (linux)
```Bash
source .venv/bin/activate
```

### Run Tests
```Bash
pytest .
```

### Start Frontend App
Set Python Path
```Bash
export PYTHONPATH="${PYTHONPATH}:/home/user/Documents/GitHub/CPN_Discovery/"
```
Start App
```Bash
streamlit run Frontend/main.py
```

Run main.py in Frontend folder

or use the a launch.json entry