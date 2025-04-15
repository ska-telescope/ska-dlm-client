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
# NOTE: Public keys must end in "pub" and private keys must end in "priv".
#       Each of the keys must have daq, pst or sdp in their name.
#
action=$1
dir=$2

if [ -d $dir ]; then
    cd $dir
    for filename in `ls -1 *pub`; do
        if [ $action == "add" ]; then
            kubectl create secret generic $filename --from-file=$filename
        elif [ $action == "rm" ]; then
            kubectl delete secret $filename
        fi
    done
    if [ $action == "add" ]; then
        daq=`ls -1 *daq*priv|head -1`
        pst=`ls -1 *pst*priv|head -1`
        sdp=`ls -1 *sdp*priv|head -1`
        kubectl create secret generic ssh-priv --from-file=daq=$daq --from-file=pst=$pst --from-file=sdp=$sdp
    elif [ $action == "rm" ]; then
        kubectl delete secret ssh-priv
    fi
fi
