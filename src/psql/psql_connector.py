import psycopg2
import click
from loguru import logger

class PsqlConnector:

	def __init__(self, dbname, commit_rate=10):

		self.dbname = dbname

		self.conn = psycopg2.connect(dbname=dbname)

		self.cur = self.conn.cursor()

		self.commit_rate = commit_rate
		self.uncommited_insert = 0

	def select_all_table(self, table): 

		self.cur.execute(f'SELECT * FROM {table}')

		return self.cur.fetchall()

	def insert_into_table(self, table, values_dict, verbose=1):

		if verbose:
			logger.info(f'Inserting line into table: {table}, values: {values_dict}')

		self.cur.execute(f"INSERT into {table} ({','.join(values_dict.keys())}) values {*values_dict.values(),}")

		logger.info('Insert successful.')

		self.uncommited_insert += 1

		if self.uncommited_insert >= self.commit_rate:
			logger.info('Commiting inserts.')
			self.commit()
			self.uncommited_insert = 0

	def delete_content(self, table):
		confirm_delete = click.prompt(f'Are you sure that you want to delete the content of table "{table}" in database "{self.dbname}" ? ',
									  type=click.Choice(['y', 'n']),
									  default='n', 
									  show_choices=True)
		if confirm_delete == 'y':
			print(f'Deleting content from table "{table}" in database "{self.dbname}".')

			self.cur.execute(f'DELETE FROM {table}')
		else: 
			print('Delete aborted.')

	def commit(self):
		self.conn.commit()

	def close(self):
		self.cur.close()
		self.conn.close()

	def commit_and_close(self):
		self.commit()
		self.close()