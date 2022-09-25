#!/bin/bash
source /usr/local/bin/virtualenvwrapper.sh
workon $1
python $2
deactivate