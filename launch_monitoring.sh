#!/bin/bash
HOME_MONITORING_DIR='/home/homemonitor/home_monitoring'
CONFIG_FILE='config/test_configuration.yaml'
PYTHON_POETRY='/home/homemonitor/.cache/pypoetry/virtualenvs/home-monitoring-Oq8m6lkM-py3.9/bin/python'

cd $HOME_MONITORING_DIR
$PYTHON_POETRY $HOME_MONITORING_DIR/home_monitoring/launch_monitoring.py $HOME_MONITORING_DIR/$CONFIG_FILE