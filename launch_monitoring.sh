#!/bin/bash
HOME_MONITORING_DIR='/home/pi/home_monitoring'
CONFIG_FILE='config/pi_configuration.yaml'
PYTHON_POETRY='/home/pi/.cache/pypoetry/virtualenvs/home-monitoring-P-zH2Pw7-py3.9/bin/python'

cd $HOME_MONITORING_DIR
$PYTHON_POETRY $HOME_MONITORING_DIR/home_monitoring/launch_monitoring.py $HOME_MONITORING_DIR/$CONFIG_FILE