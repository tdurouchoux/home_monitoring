from home_monitoring.openweather.openweather_api import CurrentWeatherApi

currentWeatherApi = CurrentWeatherApi("Paris,FR")

print(currentWeatherApi.query_api())
