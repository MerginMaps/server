#!/bin/bash
# make sure all files created by gunicorn (mergin server) have proper permissions
umask 0027

# We store a base config in config.py and override things as needed 
# using the environment variable GUNICORN_CMD_ARGS.

/bin/bash -c "celery beat -A src.celery --loglevel=info &"
/bin/bash -c "celery worker -A src.run_celery.celery --loglevel=info &"
/bin/bash -c "gunicorn --config config.py mergin:application"

