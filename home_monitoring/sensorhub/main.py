from loguru import logger
import time
import sys
import click
import os

from threading import Timer

from sensor_connector import SensorConnector

HOME_DIRECTORY = os.path.expanduser('~')
PSQL_DIRECTORY = os.path.join(HOME_DIRECTORY, 'psql')
sys.path.append(PSQL_DIRECTORY)

from psql_connector import PsqlConnector


def collect_sensor_loop(sensorConnector: SensorConnector,
						psqlConnector: PsqlConnector,
						remaining_loop: int,
						period: int) -> None:
	'''Recursive loop querying and recording sensor data.'''

	if remaining_loop:

		timer = Timer(period,
					  collect_sensor_loop,
					  [sensorConnector,
					   psqlConnector,
					   (remaining_loop-1 if remaining_loop > 0 else remaining_loop),
					   period])
		timer.start()
	else:
		end_logging(psqlConnector)

	sensors_readings = sensorConnector.get_all_sensors()

	psqlConnector.insert_into_table('sensorlog', sensors_readings)

def end_logging(psqlConnector: PsqlConnector) -> None:
	'''End script and close psql connector''' 

	logger.info('Ending sensor readings.')

	psqlConnector.commit_and_close()

	sys.exit()

@click.command()
@click.argument('period', default=60)
@click.option('--number_loops', default=-1, help='Number of loops, defaults to -1 which signifies infinite amount of loop.')
def main(number_loops: int, period: int) -> None:

	sensorhub_directory = os.path.join(HOME_DIRECTORY, 'sensorhub')
	log_directory = os.path.join(sensorhub_directory, 'log')

	starting_time = time.strftime('%d_%m_%H_%M')
	log_file = os.path.join(log_directory, f'sensor_log_{starting_time}.log')
	logger.add(log_file, enqueue=True)
	
	logger.info(f'Starting sensor logging script.')

	sensorConnector = SensorConnector()

	psqlConnector = PsqlConnector('sensorhub')

	collect_sensor_loop(sensorConnector, psqlConnector, number_loops, period)

if __name__ == '__main__':
	main()
