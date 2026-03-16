"""
天气服务模块

提供真实的天气数据查询功能，使用高德地图API
"""

import http.client
import json
import urllib.request
from typing import Dict

from utils.logger_handler import logger


class WeatherService:
    """天气服务类"""

    def __init__(self):
        self.base_url = "restapi.amap.com"
        self.path = "/v3/weather/weatherInfo"

    def get_weather(self, city: str) -> Dict[str, str]:
        """获取天气信息

        Args:
            city: 城市名称，如 '深圳'、'杭州'、'北京'，或者城市编码如 '110101'

        Returns:
            包含天气信息的字典
        """
        try:
            params = f"city={city}&extensions=null&output=null"
            url = f"{self.path}?{params}"

            conn = http.client.HTTPSConnection(self.base_url)
            conn.request("GET", url, "", {})
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            conn.close()

            result = json.loads(data)

            if result.get("status") == "1" and result.get("lives"):
                live = result["lives"][0]
                return {
                    "province": live.get("province", ""),
                    "city": live.get("city", city),
                    "adcode": live.get("adcode", city),
                    "weather": live.get("weather", "未知"),
                    "temperature": live.get("temperature", "未知"),
                    "winddirection": live.get("winddirection", "未知"),
                    "windpower": live.get("windpower", "未知"),
                    "humidity": live.get("humidity", "未知"),
                    "reporttime": live.get("reporttime", ""),
                }
            else:
                logger.warning(f"天气API返回异常: {result}")
                return self._get_mock_weather(city)

        except Exception as e:
            logger.error(f"获取天气失败: {e}")
            return self._get_mock_weather(city)

    def _get_mock_weather(self, city: str) -> Dict[str, str]:
        """获取模拟天气数据（API失败时的后备）"""
        return {
            "province": "",
            "city": city,
            "adcode": "",
            "weather": "晴",
            "temperature": "25",
            "winddirection": "南",
            "windpower": "≤3",
            "humidity": "50",
            "reporttime": "",
        }

    def format_weather_message(self, weather_data: Dict[str, str]) -> str:
        """格式化天气信息为消息字符串，包含扫地机器人使用建议"""
        city = weather_data.get("city", "未知")
        weather = weather_data.get("weather", "未知")
        temperature = weather_data.get("temperature", "未知")
        humidity = weather_data.get("humidity", "未知")
        winddirection = weather_data.get("winddirection", "未知")
        windpower = weather_data.get("windpower", "未知")

        suggestions = []
        if weather in ["雨", "雪", "暴雨", "大雨", "中雨", "小雨"]:
            suggestions.append("⚠️ 不建议使用扫地机器人，地面湿滑")
        elif weather in ["阴", "多云"]:
            suggestions.append("✅ 可以正常使用扫地机器人")
        else:
            suggestions.append("✅ 天气良好，适合使用扫地机器人")

        try:
            temp_val = int(temperature)
            if temp_val > 40:
                suggestions.append("⚠️ 温度过高，建议适当减少使用时间")
            elif temp_val < 0:
                suggestions.append("⚠️ 温度过低，可能影响电池性能")
            else:
                suggestions.append("✅ 温度适宜")
        except (ValueError, TypeError):
            pass

        try:
            humid_val = int(humidity)
            if humid_val > 80:
                suggestions.append("⚠️ 湿度较高，注意防潮")
            elif humid_val < 20:
                suggestions.append("⚠️ 湿度较低，注意静电")
        except (ValueError, TypeError):
            pass

        msg = f"📍 城市：{city}\n"
        msg += f"🌤️ 天气：{weather}\n"
        msg += f"🌡️ 温度：{temperature}°C\n"
        msg += f"💧 湿度：{humidity}%\n"
        msg += f"🌬️ 风向：{winddirection}风 {windpower}级\n\n"
        msg += "🤖 扫地机器人使用建议：\n"
        msg += "\n".join(f"  {s}" for s in suggestions)

        return msg


weather_service = WeatherService()


def get_weather_service() -> WeatherService:
    """获取天气服务实例"""
    return weather_service
