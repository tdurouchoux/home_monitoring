import click

from psql_connector import PsqlConnector

@click.command()
@click.option('--database', type=str, help='Database to target.')
@click.option('--table', type=str, help='Table where to delete content.')
def main(database, table):

	psqlConnector = PsqlConnector(database)

	psqlConnector.delete_content(table)

	psqlConnector.commit_and_close()

if __name__ == '__main__':
	main()