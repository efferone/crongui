# crongui

attempt at making a GUI crontab editor. originally to help colleagues who weren't so used to cron.

copied over my from Gitea now that it is mostly working.

# Install

adjust the below to suit your version of Python.


- Requirments:
python3
python3-tk
python3-setuptools

```python3 setup.py install```

or if you prefer pip

```pip install git+https://github.com/efferone/crongui.git```

then run it with:
```crongui```

or just use the wrapper script to start the application without installing (in beta):
```./crongui-wrapper.sh```

Please feel free to make improvments, in a dev environment you might want to use

```pip install -e .```

