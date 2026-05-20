#!/bin/bash
apt-get update && apt-get install -y wget cabextract
wget -qO /usr/local/bin/winetricks https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
chmod +x /usr/local/bin/winetricks
winetricks -q ucrtbase
wine python -m pip install pyside6 pandas pyinstaller
wine pyinstaller dashboard.spec
