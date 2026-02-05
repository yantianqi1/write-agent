#!/bin/bash
cd /root/小说agent
find . -type f -name "*.py" -o -name "*.md" -o -name "*.yaml" -o -name "*.txt" -o -name "*.json" | grep -v __pycache__ | sort
