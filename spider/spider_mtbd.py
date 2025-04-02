import os
import asyncio
import aiofiles
import pandas as pd
import httpx
from parsel import Selector

# 创建输出文件夹
os.makedirs('./tjumtbd', exist_ok=True)

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
}

# 定义URL列表
url_list = [f'https://news.tju.edu.cn/mtbd.htm'] + [f'https://news.tju.edu.cn/mtbd/{987 - i + 1}.htm' for i in range(1, 987)]

# 定义URL字典和DataFrame
url_dict = {}
url_df = pd.DataFrame(columns=['url'])
url_df.index.name = 'title'

# 异步限制
coroutine = asyncio.Semaphore(5)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 获取新闻目录
async def parse_catalogs(url):
    async with coroutine:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 302:
                # 获取重定向的新 URL
                redirect_url = response.headers.get("Location")
                if redirect_url:
                    # 使用新的 URL 发起请求
                    response = await client.get(redirect_url, headers=headers)
            selector = Selector(response.text)
            print(f'正在解析: {url}')
            # 获取页面所有链接和标题
            urls = selector.css('ul.indexList li a::attr(href)').getall()
            titles = selector.css('ul.indexList li a::text').getall()

            for link, title in zip(urls, titles):
                if not link.startswith('http'):
                    # 处理相对路径，确保拼接完整的URL
                    if link.startswith('../../'):
                        link = 'https://news.tju.edu.cn' + link[5:] 
                    elif link.startswith('../'):
                        link = 'https://news.tju.edu.cn' + link[2:]  # 去掉相对路径的前缀 `../`
                    elif link.startswith('/'):
                        link = 'https://news.tju.edu.cn' + link  # 如果链接以 `/` 开头，拼接根路径
                url_dict[link] = title  # 存储到字典中

# 获取新闻详细内容
async def parse_page(url):
    async with coroutine:
        print(f"正在获取: {url}")
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10, headers=headers) as client:
                response = await client.get(url)
                selector = Selector(response.text)
                title = selector.css('title::text').get().strip()

                if "/" in title:
                    title = title.replace("/", "_")  # 处理文件名中的特殊字符
                    
                
                # 提取页面中的图片链接
                imgs = selector.css('img::attr(src)').getall()

                # 保存页面内容到本地
                async with aiofiles.open(f'./tjumtbd/{title}.html', mode='w', encoding='utf-8') as file:
                    await file.write(response.text)

                # 更新DataFrame
                url_df.loc[title] = url
        except Exception as e:
            print(f'请求失败: {url} - {e}')

# 主程序
async def main():
    # 创建任务列表
    tasks = [asyncio.create_task(parse_catalogs(url)) for url in url_list]
    await asyncio.gather(*tasks)

    # 爬取所有页面
    tasks = [asyncio.create_task(parse_page(url)) for url in url_dict.keys()]
    await asyncio.gather(*tasks)

    # 保存爬取的URL到CSV
    url_df.to_csv("./tjumtbd.csv")

if __name__ == '__main__':
    asyncio.run(main())