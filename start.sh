#!/bin/sh
# if virtualenvwrapper.sh is in your PATH (i.e. installed with pip)
source 'which virtualenvwrapper.sh'
#source /path/to/virtualenvwrapper.sh # if it's not in your PATH
workon $1
python $2
deactivate