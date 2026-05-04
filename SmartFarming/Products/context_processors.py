"""
Inject ``weather_banner`` into every template context.

Open-Meteo is fetched at most once per process every 30 minutes (LocMem cache TTL).
Slow networks/timeouts yield ``{}`` — templates treat missing temps as “unavailable”.
"""

from django.core.cache import cache

from integrations.weather import fetch_nairobi_weather


def weather_banner(_request):
    data = cache.get("weather_nairobi_v1")
    if data is None:
        data = fetch_nairobi_weather()
        cache.set("weather_nairobi_v1", data, 1800)
    return {"weather_banner": data or {}}
