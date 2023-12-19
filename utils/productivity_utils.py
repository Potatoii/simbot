import ast
import datetime
import math
import re
from typing import Union

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from matplotlib.font_manager import FontProperties

from decorators import sim_client, httpx_client
from sim_request import SimClient


def draw_production_relations_chart(retail_info_list: list):
    for item in retail_info_list:
        item["date"] = datetime.datetime.strptime(item["date"], "%Y-%m-%d")
    # 创建新的图形和子图
    font = FontProperties(fname="msyh.ttc", size=14)
    fig, ax1 = plt.subplots(figsize=(20, 5))
    # 获取数据的最小和最大日期
    min_date = min(item["date"] for item in retail_info_list)
    max_date = max(item["date"] for item in retail_info_list)
    # 设置x轴的范围
    ax1.set_xlim([mdates.date2num(min_date), mdates.date2num(max_date)])
    # 设置x轴为日期
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.xaxis.set_major_locator(mdates.DayLocator())  # 添加这行代码设置x轴的主要刻度为每天
    plt.xticks(rotation=45)
    # 绘制平均价格
    ax1.plot([item["date"] for item in retail_info_list], [item["averagePrice"] for item in retail_info_list],
             color="tab:blue")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("平均价格", color="tab:blue", fontproperties=font)
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    # 创建一个共享x轴的新的y轴
    ax2 = ax1.twinx()
    # 绘制需求
    ax2.plot([item["date"] for item in retail_info_list], [item["demand"] for item in retail_info_list],
             color="tab:red")
    ax2.set_ylabel("需求", color="tab:red", fontproperties=font)
    ax2.tick_params(axis="y", labelcolor="tab:red")
    # 添加浅色的辅助线
    ax1.grid(True, color="gray", linestyle="--", linewidth=0.5)
    fig.tight_layout()
    plt.show()


@sim_client
async def get_my_company(*, simclient: SimClient = None):
    url = "https://www.simcompanies.com/api/v2/companies/me/"
    response = await simclient.get(url)
    company_info = response.json()
    print(company_info)
    temporals = company_info["temporals"]
    print(temporals)


@sim_client
async def get_productivity(item_id: Union[int, str], *, simclient: SimClient = None):
    wiki_url = f"https://www.simcompanies.com/api/v4/zh/0/encyclopedia/resources/{1}/{item_id}/"
    # wiki_url = f"https://www.simcompanies.com/api/v4/zh/0/encyclopedia/resources/2/{item_id}/"
    response = await simclient.get(wiki_url)
    item_info = response.json()
    produced_an_hour = item_info["producedAnHour"]
    retail_info_list: list[dict] = item_info["retailData"]
    retail_info_list = [retail_info for retail_info in retail_info_list]
    # draw_production_relations_chart(retail_info_list)
    print(produced_an_hour * 2 * 1.01 * 3 * 24 / 12)
    print(item_info)


@sim_client
async def get_executives():
    executives_url = "https://www.simcompanies.com/api/v2/companies/me/executives/"


def count_out_hour_profit(sellprice, saturation, retail_modeling, quality, sellBonus, building_wages, adminRate, courcCost):
    time2sellPerUnit = math.pow(sellprice * retail_modeling['xMultiplier'] + (retail_modeling['xOffsetBase'] + (max(-.38, saturation - .24 * quality) - .5) / retail_modeling['marketSaturationDiv']), retail_modeling['power']) * retail_modeling['yMultiplier'] + retail_modeling['yOffset']
    time2sellPerUnit = round(time2sellPerUnit, 2)
    unitsSoldPerHour = 3600 / time2sellPerUnit / (1 - sellBonus / 100)
    unitsSoldPerHour = round(unitsSoldPerHour, 2)
    print(unitsSoldPerHour)
    revenuesPerHour = unitsSoldPerHour * sellprice
    revenuesPerHour = round(revenuesPerHour, 2)
    cost = courcCost * unitsSoldPerHour + building_wages + (building_wages * adminRate / 100)
    return revenuesPerHour - cost


@httpx_client
async def get_encyclopedia_item(*, client=None):
    url = "https://www.simcompanies.com/zh/encyclopedia/0/resource/56/"
    response = await client.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    script_tags = soup.find_all("script", {"type": "module"})
    js_url = script_tags[0].attrs.get("src")
    print(js_url)
    js = await client.get(js_url)
    r1_match = re.findall("r1=(.*?);", js.text)
    print(r1_match[0])
    variable_match = re.findall(f"{r1_match[0]}=(.*?);", js.text)
    last_comma = variable_match[0].rfind(",")
    second_last_comma = variable_match[0].rfind(",", 0, last_comma)
    variable = variable_match[0][:second_last_comma]
    # variable: str = variable_match[0].split(",1:")[0] + "}}"
    variable = re.sub(r"(\w+):", r"'\1':", variable)
    python_dict = ast.literal_eval(variable)
    print(python_dict)
    print(python_dict["0"]["1"]["56"])  # realmId, economyState, resourceDetails
    retail_model = python_dict["0"]["1"]["56"]
    price = count_out_hour_profit(5200, 1.1960499259160826, retail_model, 2, 7, 222.79, 11.41, 3859)
    print(price)


if __name__ == "__main__":
    import asyncio

    asyncio.run(get_my_company())
    # asyncio.run(get_productivity(56))
    # asyncio.run(get_encyclopedia_item())
