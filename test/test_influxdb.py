
import influxdb_client as idb
from influxdb_client.client.write_api import SYNCHRONOUS


client = idb.InfluxDBClient(url="http://localhost:8086")

write_api = client.write_api()
_point1 = idb.Point("my_measurement").tag("location", "Paris").field("temperature", 25.3).field("humidity", 57)

write_api.write(bucket='test/autogen', org='my-org', record=_point1)

query_api = client.query_api()

print(query_api.query('''from(bucket: "test/autogen")
							|> range(start: -1h)
							|> filter(fn: (r) => r._field == "humidity" )''').to_json())

client.close()