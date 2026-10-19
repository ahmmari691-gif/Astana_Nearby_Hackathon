#!/bin/zsh
cd -- "${0:A:h}"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Нужен Python 3. Установите его с https://www.python.org/downloads/macos/'
else
  python3 app.py
fi
printf '\nНажмите Enter, чтобы закрыть окно. '
read -r
