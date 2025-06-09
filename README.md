# KeysightXSeries

## Directory structure

```text
└── KeysightXSeries/
    ├── .gitignore
    ├── pyproject.toml
    ├── README.md
    ├── LICENSE.txt
    ├── CITATION.cff
    ├── naqs_devices/ # note: must be same as in the parent naqs_devices repo to be in the same namespace
    │   └── KeysightXSeries/
    │       ├── __init__.py
    │       ├── register_classes.py
    │       ├── labscript_devices.py
    │       ├── blacs_tabs.py
    │       ├── blacs_workers.py
    │       └── runviewer_parsers.py
    └── docs/
        └── KeysightXSeries.rst
```

## Models tested with

* `DSOX1204G`
