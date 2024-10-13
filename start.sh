#!/bin/bash

if [ "${DEBUG}" == "1" ]; then
	echo "Starting in Debug mode"
	uvicorn main:app --host 0.0.0.0 --port 3030 --reload
else
	echo "Starting in Production mode"
	uvicorn main:app --host 0.0.0.0 --port 3030 --reload
fi
