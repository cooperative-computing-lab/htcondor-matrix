#!/bin/sh

# Copyright (C) 2015 The University of Notre Dame
# This software is distributed under the GNU General Public License.
# See the file LICENSE for details.

# This cron job runs on your webserver, and drops condor
# status output into files in /tmp.  condor_matrix.cgi
# then reads these files and produces the matrix output.
# This roundabout method is used because the condor_status
# operations can occasionally delay, and we do not want
# to bother the central manager on every page load.

# Modify these paths as needed for your configuration:
TEMPDIR=/tmp/condor.data
CONDOR_PATH=/usr/bin

export PATH=${CONDOR_PATH}:${PATH}

# Ensure that these files will be readable by others.
umask 022

# Create the working directory.
mkdir -p $TEMPDIR
cd $TEMPDIR

# Write the data to a temporary file, then move it.
# This will prevent readers from seeing incomplete results.

condor_status -submitters -l > submitters.tmp
mv submitters.tmp submitters.txt

condor_status -l > machines.tmp
mv machines.tmp machines.txt

condor_status -format "%s\t" Name -format "%s\t" State -format "%d\t" Cpus -format "%d\t" Memory -format "%s\t" RemoteUser -format "\n" Name > states.tmp
mv states.tmp states.txt
