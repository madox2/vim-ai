#!/bin/bash

if [ -n "$(which pip)" ]; then
  echo installing deps using pip
  pip install "openai>=0.27"
  exit 0
fi

if [ -n "$(which pip3)" ]; then
  echo installing deps using pip3
  pip3 install "openai>=0.27"
  exit 0
fi

echo pip or pip3 not found
exit 1
