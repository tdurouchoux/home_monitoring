from loguru import logger
import time
import sys
import click
import os

from threading import Timer

from openweather_api import *

HOME_DIRECTORY = os.path.expanduser('~')
PSQL_DIRECTORY = os.path.join(HOME_DIRECTORY, 'psql')
sys.path.append(PSQL_DIRECTORY)

from psql_connector import PsqlConnector


def query_weather_loop(currentWeatherApi: CurrentWeatherApi,
						psqlConnector: PsqlConnector,
						remaining_loop: int,
						period: int) -> None:
	'''Recursive loop querying and recording sensor data.'''

	if remaining_loop:

		timer = Timer(period,
					  query_weather_loop,
					  [currentWeatherApi,
					   psqlConnector,
					   (remaining_loop-1 if remaining_loop > 0 else remaining_loop),
					   period])
		timer.start()
	else:
		end_logging(psqlConnector)

	weather_info = currentWeatherApi.query_api()
	logger.info(f'querried date: {weather_info["date"]}')

	psqlConnector.insert_into_table('openweather', weather_info)

def end_logging(psqlConnector: PsqlConnector) -> None:
	'''End script and close psql connector''' 

	logger.info('Ending openweather querrying.')

	psqlConnector.commit_and_close()

	sys.exit()

@click.command()
@click.argument('period', default=60)
@click.option('--number_loops', default=-1, help='Number of loops, defaults to -1 which signifies infinite amount of loop.')
def main(number_loops: int, period: int) -> None:

	openweather_directory = os.path.join(HOME_DIRECTORY, 'openweather')
	log_directory = os.path.join(openweather_directory, 'log')

	starting_time = time.strftime('%d_%m_%H_%M')
	log_file = os.path.join(log_directory, f'openweather_log_{starting_time}.log')
	logger.add(log_file, enqueue=True)
	
	logger.info(f'Starting openweather querrying script.')

	currentWeatherApi = CurrentWeatherApi('Paris,FR')

	psqlConnector = PsqlConnector('sensorhub', commit_rate=2)

	query_weather_loop(currentWeatherApi, psqlConnector, number_loops, period)

if __name__ == '__main__':
	main()
