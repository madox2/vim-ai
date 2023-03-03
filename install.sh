#!/bin/bash

if [ -n "$(which pip3)" ]; then
  pip3 install openai
  exit 0
fi

if [ -n "$(which pip)" ]; then
  pip install openai
  exit 0
fi

echo missing pip3 or pip
exit 1
