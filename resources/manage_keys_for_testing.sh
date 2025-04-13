#!/bin/bash
#
# For testing purposes this script will add or remove keys to secrets in k8s.
# This is NOT for ITF or Prod who have their own management system, just for
# one off dev testing!
#
# First parameter must be "add" or "rm" to add or remove keys.
# Second parameter is the directory containing the pub/private key pairs. The
# file name will become the secret key name. This will need to match the value
# used in the helm charts.
#
action=$1
dir=$2

if [ -d $dir ]; then
    cd $dir
    for filename in `ls -1`; do
        if [ $action == "add" ]; then
            kubectl create secret generic $filename --from-file=$filename
        elif [ $action == "rm" ]; then
            kubectl delete secret $filename
        fi
    done
fi
