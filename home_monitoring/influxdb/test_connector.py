from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector
import time
from datetime import datetime

connector = InfluxDBConnector("test", "admin", "dashmaster")


# for i in range(5):

#     print("Writing measure with value :", i)


#     connector.write_measure(
#         "test_measure",
#         {"input": i},
#         measure_tags={"location": "test_time"},
#         time=datetime.utcnow(),
#     )

#     time.sleep(20)

data_points = []
time_points = []

for i in range(5):
    print("Storing point with value : ", i)

    data_points.append({"input": i})
    time_points.append(datetime.utcnow())

    time.sleep(5)


print("Writing stored points")


connector.write_batch_measures(
    "test_measure", data_points, time_points, measure_tags={"location": "test_time"}
)
