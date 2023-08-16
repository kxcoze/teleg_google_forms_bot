#!/bin/bash

celery --app src.worker.celery worker --concurrency=1 --loglevel=INFO --beat