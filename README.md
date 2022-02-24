# julo-mini-wallet
Created by Muhammad Abyan Rizqo

This repo is part of JULO Backend Test.

Python verison used is ```3.8.10```

## Initialize and run
To initialize database and run the server. We can use this command:

```
python3 -m venv .venv
source /home/rizqo/project/julo/julo-mini-wallet/.venv/bin/activate 
pip install -r requirements.txt 
python3 api/migrate.py
python3 api/run.py
```

If you want to run in port 80, please make sure there are no other service running in the same port. Default port by app is 80.

If you want to setup ```.env``` you can make make it and copy values from ```env.example```. But it's not necessary since default value is provided in the app.

## Documentation
Documentattion is provided by JULO Team, here is the link https://documenter.getpostman.com/view/8411283/SVfMSqA3?version=latest.
