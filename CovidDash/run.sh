#!/bin/bash
source venv/bin/activate
if [ "$1" == "s3" ]; then
  export S3_ROLE=#enter the S3 role to assume
  export S3_BUCKET=#enter the S3 bucket to be used for ins/outs
fi
export STORAGE="$1"
python get_data.py
python dashboard.py
