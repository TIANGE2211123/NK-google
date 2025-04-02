import pandas as pd
import math
import networkx as nx
import os
from parsel import Selector
from urllib.parse import urljoin

# 读取第一个数据集
df = pd.read_csv("../spider/nku_allinfo.csv", encoding='utf-8', index_col="title")
path = "../spider/nku"
files = os.listdir(path)

# 存储一个网页链接到一个列表的映射，列表中的元素为链接对应HTML文档中可以跳转到的链接
url_dict = {}

# 记录已处理的文件
processed_files = "processed_files.txt"
if os.path.exists(processed_files):
    with open(processed_files, 'r') as pf:
        processed = set(line.strip() for line in pf)
else:
    processed = set()

# 处理文件并构建 url_dict
with open(processed_files, 'a', encoding='utf-8') as pf:
    for file in files:
        if file in processed:
            print(f"File '{file}' already processed. Skipping...")
            continue

        title = str(file).split(".html")[0]

        if title not in df.index:
            print(f"Skipping '{title}': Not found in CSV index.")
            continue

        url = df.loc[title, 'url']
        if isinstance(url, pd.Series):
            print(f"Duplicate entry found for '{title}', using the first URL.")
            url = url.iloc[0]

        try:
            with open(os.path.join(path, file), 'r', encoding='utf-8-sig') as f:
                text = f.read()
                selector = Selector(text)
                url_list = selector.css('a::attr(href)').getall()
                url_dict[url] = url_list

            pf.write(file + "\n")
            pf.flush()
        except FileNotFoundError:
            print(f"File '{file}' not found. Skipping...")
            continue

# 输出结果
for key, value in url_dict.items():
    print(f"Key: {key}\nValue: {value}")

# 计算pageRank
def get_page_rank():
    digraph = nx.DiGraph()
    for url, url_list in url_dict.items():
        for url2 in url_list:
            if url2 in df.url.values:
                digraph.add_edge(url, url2)

    pagerank = nx.pagerank(digraph, alpha=0.85)
    page_rank_df = pd.Series(pagerank, name='page_rank')
    page_rank_df = page_rank_df.apply(lambda x: math.log(x * 10000, 10) + 1)
    page_rank_df.to_csv("./page_rank.csv", encoding='utf-8-sig')

get_page_rank()

# 查看排名靠前的一些网页
page_rank = pd.read_csv("page_rank.csv", encoding='utf-8')
print(page_rank.sort_values(by='page_rank', ascending=False).head(10))

# 处理第二个数据集
processed_files = "processed_files_tju.txt"
path = "../spider/tju"
files = os.listdir(path)
url_dict1 = {}
df1 = pd.read_csv("../spider/tju_allinfo.csv", encoding='utf-8', index_col="title")

if os.path.exists(processed_files):
    with open(processed_files, 'r', encoding='utf-8') as pf:
        processed = set(line.strip() for line in pf)
else:
    processed = set()

with open(processed_files, 'a', encoding='utf-8') as pf:
    for file in files:
        if file in processed:
            print(f"File '{file}' already processed. Skipping...")
            continue

        title = str(file).split(".html")[0]

        if title not in df1.index:
            print(f"Skipping '{title}': Not found in CSV index.")
            continue

        url = df1.loc[title, 'url']
        if isinstance(url, pd.Series):
            print(f"Duplicate entry found for '{title}', using the first URL.")
            url = url.iloc[0]

        try:
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                text = f.read()
                selector = Selector(text)
                url_list = selector.css('a::attr(href)').getall()
                url_dict1[url] = url_list

            pf.write(file + "\n")
            pf.flush()
        except FileNotFoundError:
            print(f"File '{file}' not found. Skipping...")
        except Exception as e:
            print(f"An error occurred while processing '{file}': {e}")
            continue

# 输出结果
for key, value in url_dict1.items():
    print(f"Key: {key}\nValue: {value}")

# 初始化清理后的字典
cleaned_url_dict = {}
# 指定需要移除的链接
url_to_remove = "http://mp.weixin.qq.com/profile?src=3&timestamp=1502984449&ver=1&signature=*UeAZIGMU8t-MJaC8RKEVhsEgKvMIuX0o2JUhk2LrMU6yXbkbFUCOxIEsA2HAYWUwdO1JzStDVDeSaziFo-D1g=="

# 遍历原始字典进行清理
for base_url, url_list in url_dict1.items():
    cleaned_links = [link for link in url_list if link != url_to_remove]
    if cleaned_links:
        cleaned_url_dict[base_url] = cleaned_links

# 打印清理后的结果
for key, value in cleaned_url_dict.items():
    print(f"Key: {key}")
    print(f"Value: {value}")

# 进一步清理链接
cleaned_url_dict1 = {}
for base_url, url_list in cleaned_url_dict.items():
    cleaned_links = []
    for link in url_list:
        if not link.startswith("http"):
            link = urljoin(base_url, link)

        if not link.startswith("javascript") and link != "#":
            cleaned_links.append(link)

    if cleaned_links:
        cleaned_url_dict1[base_url] = cleaned_links

# 打印清理后的结果
for key, value in cleaned_url_dict1.items():
    print(f"Key: {key}")
    print(f"Value: {value}")

# 计算 PageRank
def get_page_rank(cleaned_url_dict, df):
    digraph = nx.DiGraph()
    for url, url_list in cleaned_url_dict.items():
        for url2 in url_list:
            if url2 in df['url'].values:
                digraph.add_edge(url, url2)

    pagerank = nx.pagerank(digraph, alpha=0.85)
    page_rank_df = pd.Series(pagerank, name='page_rank')
    page_rank_df = page_rank_df.apply(lambda x: math.log(x * 10000, 10) + 1)
    page_rank_df.to_csv("./page_rank_tju.csv", encoding='utf-8-sig')
    print("PageRank 计算完成并保存为 page_rank_tju.csv")

# 查看排名靠前的网页
def show_top_pages(filepath, top_n=10):
    page_rank = pd.read_csv(filepath, encoding='utf-8')
    top_pages = page_rank.sort_values(by='page_rank', ascending=False).head(top_n)
    print(f"排名靠前的 {top_n} 网页：")
    print(top_pages)
    return top_pages

# 示例使用
get_page_rank(cleaned_url_dict1, df1)
top_pages = show_top_pages("page_rank_tju.csv", top_n=10)

# 合并两个数据集
df1 = pd.read_csv('page_rank.csv')
df2 = pd.read_csv('page_rank_tju.csv')
concatenated_df = pd.concat([df1, df2], ignore_index=True)
concatenated_df.to_csv('page_rank_all_news.csv', index=False)
print(concatenated_df.head())

# 重命名第一列
df = pd.read_csv("page_rank_all_news.csv", encoding="utf-8")
df.rename(columns={'Unnamed: 0': 'url'}, inplace=True)
print(df.head())
df.to_csv("page_rank_allnews.csv", index=False, encoding="utf-8-sig")
print("第一列已重命名为 'url' 并保存为 page_rank_allnews.csv")