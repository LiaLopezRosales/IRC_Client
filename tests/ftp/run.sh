#!/bin/bash

python3 tests/ftp/tester.py

if [[ $? -ne 0 ]]; then
  exit 1
fi