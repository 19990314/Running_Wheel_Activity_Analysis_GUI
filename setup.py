from setuptools import setup

APP = ['main.py']
OPTIONS = {
    'argv_emulation': True,
    'includes': ['tkinter', 'matplotlib', 'pandas', 'xlrd', 'openpyxl'],
    'excludes': ['matplotlib.backends._backend_tk'],  # often causes recursion
    'optimize': 1,
    'plist': {
        'CFBundleName': 'Mouse Dashboard',
        'CFBundleShortVersionString': '1.0',
        'CFBundleIdentifier': 'com.example.mousedash',
    }
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)