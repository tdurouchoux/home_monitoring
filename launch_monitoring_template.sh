#!/bin/bash
HOME_MONITORING_DIR='/home/<user directory>/home_monitoring'
CONFIG_FILE='config/<config file>.yaml'
PYTHON_POETRY='<python exec>'

cd $HOME_MONITORING_DIR
$PYTHON_POETRY $HOME_MONITORING_DIR/home_monitoring/launch_monitoring.py $HOME_MONITORING_DIR/$CONFIG_FILE