#!/bin/bash

if [ -z "$(which pip)" ]; then
  echo pip not found
  exit 1
fi

echo installing deps using pip
pip install openai
