#!/bin/zsh
cd -- "${0:A:h}"
python3 collect_2gis.py
printf '\nНажмите Enter, чтобы закрыть окно. '
read -r
