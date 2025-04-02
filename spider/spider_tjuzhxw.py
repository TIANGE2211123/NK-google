import os
import asyncio
import aiofiles
import pandas as pd
import httpx
from parsel import Selector

url_list = [f'https://news.tju.edu.cn/zhxw/{i}.htm' for i in range(1, 1087)]
url_dict = {}
url_df = pd.DataFrame(columns=['url'])
url_df.index.name = 'title'

# 解析目录页面的协程函数，提取所有链接和标题
async def parse_catalogs_page(url, semaphore):
    async with semaphore:  # 使用信号量限制并发
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            print(url)  # 打印当前请求的 URL
            if response.status_code == 302:
                redirect_url = response.headers.get("Location")
                if redirect_url:
                    response = await client.get(redirect_url)
            selector = Selector(response.text)
            ## print(response.text)
            url_dict.update(zip(selector.css('a::attr(href)').getall(), selector.css('a::text').getall()))


# 解析网页内容并保存为 HTML 文件的协程函数
async def parse_page(url, semaphore):
    async with semaphore:  # 使用信号量限制并发
        print("正在获取..." + str(url))  # 打印正在获取的 URL
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10,
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                                            "Referer": "https://news.nankai.edu.cn/",
                                        }) as client:
                if url.startswith('http') or url.startswith('https'):
                    response = await client.get(url)
                    selector = Selector(response.text)
                    title = selector.css('title::text').get()
                    if "/" in title:
                        title = title.replace("/", "_")
                    async with aiofiles.open(f'./tju_zhxw/{title}.html', mode='w', encoding='utf-8') as file:
                        await file.write(response.text)
                    url_df.loc[title] = url  # 插入到 DataFrame 中
        except Exception as e:
            print(f'{e}: {url}')

# 主函数入口，创建文件夹并调度所有任务
async def main():
    if not os.path.exists('./tju_zhxw'):
        os.mkdir('./tju_zhxw')

    # 在主函数中创建信号量
    semaphore = asyncio.Semaphore(5)

    # 创建并发任务列表，用于解析目录页面
    tasks = [asyncio.create_task(parse_catalogs_page(url, semaphore)) for url in url_list]
    await asyncio.gather(*tasks)

    # 创建并发任务列表，用于解析各个详情页面并保存 HTML 文件
    tasks = [asyncio.create_task(parse_page(url, semaphore)) for url in url_dict.keys()]
    await asyncio.gather(*tasks)

    # 将 DataFrame 写入到 CSV 文件
    url_df.to_csv("./tju_zhxw.csv")

# 主程序入口
if __name__ == '__main__':
    asyncio.run(main())