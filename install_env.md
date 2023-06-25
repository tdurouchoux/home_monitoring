
# Install influxdb 1.8
curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
echo "deb https://repos.influxdata.com/debian stretch stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
apt update
apt install influxdb
systemctl enable influxdb.service

# Install python 3.9 

# Install poetry
python3.9 -m pip install -U pip
python3.9 -m pip install cryptography==2.9.2
python3.9 -m pip install poetry

> better with pipx 

# Install env
poetry install

# Setup influxdb

> enter influxdb console : influx

1. Create database : 
CREATE DATABASE <name>
2. [Create an admin user](https://docs.influxdata.com/influxdb/v1.8/administration/authentication_and_authorization/#admin-users) : 
CREATE USER admin WITH PASSWORD '<password>' WITH ALL PRIVILEGES
3. Create an other user for monitoring : 
CREATE USER <username> WITH PASSWORD '<password>'
4. Grant rights for not admin user :  
GRANT [READ,WRITE,ALL] ON <database_name> TO <username>
5. Setup authentification :  
set auth-enabled to "true" in /etc/influxdb/influxdb.conf
set flux-enabled to "true" in /etc/influxdb/influxdb.conf
6. Restart influxdb : 
systemctl restart influxdb