#!/bin/sh
# start environment for python program
source `which virtualenvwrapper.sh`
workon $1
python $2
deactivate