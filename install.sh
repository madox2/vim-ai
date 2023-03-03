#!/bin/bash

if [ -z "$(which pip3)" ]; then
  echo pip3 not found
  exit 1
fi

echo installing deps using pip3
pip3 install openai
