import numpy as np
import pandas as pd
import datetime
import os
import re
from parsel import Selector


### 一、数据清洗
# 将多个nk相关的csv合并
nk_news_csv = pd.read_csv("../nk_media.csv", encoding='utf-8', index_col=0)
nk_news1_csv = pd.read_csv("../nk_media1.csv", encoding='utf-8', index_col=0)
nk_news2_csv = pd.read_csv("../nk_media2.csv", encoding='utf-8', index_col=0)
data = pd.concat([nk_news_csv, nk_news1_csv, nk_news2_csv], axis=0)
data.to_csv("nkumedia.csv")

nk_news_csv = pd.read_csv("nku_shengyu.csv", encoding='utf-8', index_col=0)
nk_news1_csv = pd.read_csv("nkumedia.csv", encoding='utf-8', index_col=0)
nk_news2_csv = pd.read_csv("nkunews.csv", encoding='utf-8', index_col=0)
data = pd.concat([nk_news_csv, nk_news1_csv, nk_news2_csv], axis=0)
data.to_csv("nku.csv")

# 将多个tj相关的csv合并
nk_news_csv = pd.read_csv("../tjumtbd.csv", encoding='utf-8', index_col=0)
nk_news1_csv = pd.read_csv("../tjunews.csv", encoding='utf-8', index_col=0)
nk_news2_csv = pd.read_csv("../tjuxnxw.csv", encoding='utf-8', index_col=0)
data = pd.concat([nk_news_csv, nk_news1_csv, nk_news2_csv], axis=0)
data.to_csv("tjunews.csv")


# 清理nku相关的HTML文件和CSV记录
nku_csv = pd.read_csv("nku.csv")
csv_titles = set(nku_csv['title'].to_numpy())
path = "nku"
files = os.listdir(path)
folder_titles = set(file.split(".html")[0] for file in files if file.endswith(".html"))

files_to_remove = folder_titles - csv_titles
titles_to_remove = csv_titles - folder_titles

for file in files:
    if file.split(".html")[0] in files_to_remove:
        os.remove(os.path.join(path, file))

nku_csv = nku_csv[~nku_csv['title'].isin(titles_to_remove)]
nku_csv.reset_index(drop=True, inplace=True)
nku_csv.to_csv("nk_media.csv", index=False)
print("nku清理完成！")

# 对nku的CSV文件进行去重
csv_file = "nk_media.csv"
data = pd.read_csv(csv_file)
data = data.drop_duplicates(subset="title")
data.to_csv("nku_news.csv", index=False)
print("nku去重完成，结果已保存为 nku_news.csv")


# 清理tj相关的HTML文件和CSV记录
nku_csv = pd.read_csv("tjunews.csv")
csv_titles = set(nku_csv['title'].to_numpy())
path = "tju"
files = os.listdir(path)
folder_titles = set(file.split(".html")[0] for file in files if file.endswith(".html"))

files_to_remove = folder_titles - csv_titles
titles_to_remove = csv_titles - folder_titles

for file in files:
    if file.split(".html")[0] in files_to_remove:
        os.remove(os.path.join(path, file))

nku_csv = nku_csv[~nku_csv['title'].isin(titles_to_remove)]
nku_csv.reset_index(drop=True, inplace=True)
nku_csv.to_csv("tjunews0.csv", index=False)
print("tju清理完成！")

# 对tju的CSV文件进行去重
csv_file = "tjunews0.csv"
data = pd.read_csv(csv_file)
data = data.drop_duplicates(subset="title")
data.to_csv("tju_news.csv", index=False)
print("tju去重完成，结果已保存为 tju_news.csv")


### 二、数据预处理
# 为nku本地文件夹下的所有HTML文档添加description
nku_news = pd.read_csv('nku_news.csv')
data = pd.DataFrame(columns=['title', 'description'])


def add_description_to_csv(path1="nku"):
    files = os.listdir(path1)
    for file_name in files:
        if file_name.endswith('.html'):
            file_path = os.path.join(path1, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                selector = Selector(content)
                title = selector.css('title::text').get()
                if title is None:
                    continue
                description = selector.css('meta[name="description"]::attr(content)').get()
                if description is not None:
                    description = description.replace('\r', '').replace('\n', '').replace('\t', '').replace('　', '')
                data.loc[title, 'title'] = title
                data.loc[title, 'description'] = description


add_description_to_csv(path1="nku")

for idx, row in nku_news.iterrows():
    title = row['title']
    if title in data.index:
        nku_news.at[idx, 'description'] = data.loc[title, 'description']

nku_news.to_csv('nku_news_with_description.csv', index=False)
print(nku_news.head())


# 获取nku一个HTML文档的全部信息
nku_news = pd.read_csv('nku_news.csv')
data = pd.DataFrame(columns=['title', 'description', 'date', 'content', 'editor'])


def extract_info_from_html(path1="nku"):
    files = os.listdir(path1)
    for file_name in files:
        if file_name.endswith('.html'):
            file_path = os.path.join(path1, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                selector = Selector(content)
                title = selector.css('title::text').get()
                if not title:
                    continue
                description = selector.css('meta[name="description"]::attr(content)').get()
                if description:
                    description = description.replace('\r', '').replace('\n', '').replace('\t', '').replace('　', '')
                _content = selector.css('p::text').getall()
                if _content:
                    content_text = "".join(_content[:-1]).replace('\r', '').replace('\n', '').replace('\t', '').replace(' ',
                                                                                                                  ' ').replace(
                        '　', '')
                    editor = _content[-1].strip()
                else:
                    content_text, editor = None, None
                all_text = selector.css('*::text').getall()
                date = None
                for line in all_text:
                    match = re.search(r'(20\d{2})-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01])', line.strip())
                    if match:
                        date = match.group()
                        break
                if date:
                    print(f"Extracted date: {date}")
                try:
                    date_timestamp = datetime.datetime.strptime(date, '%Y-%m-%d').timestamp()
                    print(f"Converted timestamp: {date_timestamp}")
                except ValueError as e:
                    print(f"Error converting date {date} to timestamp: {e}")
                    date_timestamp = None
                else:
                    date_timestamp = None
                data.loc[title] = [title, description, date_timestamp, content_text, editor]


extract_info_from_html(path1="nku")

for idx, row in nku_news.iterrows():
    title = row['title']
    if title in data.index:
        nku_news.at[idx, 'description'] = data.loc[title, 'description']
        nku_news.at[idx, 'date'] = data.loc[title, 'date']
        nku_news.at[idx, 'content'] = data.loc[title, 'content']
        nku_news.at[idx, 'editor'] = data.loc[title, 'editor']

nku_news.to_csv('nku_allinfo.csv', index=False)
print(nku_news.head())


# 获取tju一个HTML文档的全部信息
tju_news = pd.read_csv('tju_news.csv')
data = pd.DataFrame(columns=['title', 'content', 'date', 'editor'])


def extract_content_and_metadata(path="tju"):
    files = os.listdir(path)
    for file_name in files:
        if file_name.endswith('.html'):
            file_path = os.path.join(path, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                selector = Selector(content)
                title = selector.css('title::text').get()
                if title is None:
                    continue
                content_paragraphs = selector.css('.TRS_Editor p::text').getall()
                content = "".join(content_paragraphs).replace('\r', '').replace('\n', '').replace('\t', '').replace('　', '')
                all_text = selector.css('form[name="_newscontent_fromname"] p.contentTime::text').getall()
                date = None
                for line in all_text:
                    match = re.search(r'(20\d{2})-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01])', line.strip())
                    if match:
                        date = match.group()
                        break
                if date:
                    print(f"Extracted date: {date}")
                try:
                    date_timestamp = datetime.datetime.strptime(date.strip(), '%Y-%m-%d').timestamp()
                except ValueError:
                    date_timestamp = None
                else:
                    date_timestamp = None
                editor_paragraphs = selector.css('.TRS_Editor p::text').getall()
                if editor_paragraphs:
                    editor = editor_paragraphs[-1].strip()
                else:
                    editor = None
                data.loc[title] = [title, content, date_timestamp, editor]


extract_content_and_metadata(path="tju")

for idx, row in tju_news.iterrows():
    title = row['title']
    if title in data.index:
        tju_news.at[idx, 'content'] = data.loc[title, 'content']
        tju_news.at[idx, 'date'] = data.loc[title, 'date']
        tju_news.at[idx, 'editor'] = data.loc[title, 'editor']

tju_news.to_csv('tju_allinfo.csv', index=False)
print(tju_news.head())


# 为tju的CSV文件添加description列
tju_news = pd.read_csv('tju_allinfo.csv')
tju_news['description'] = tju_news['title']
tju_news.to_csv('tju_allinfo1.csv', index=False)
print(tju_news.head())


# 提取tju的CSV文件中content列的文件链接
tju_news = pd.read_csv('tju_allinfo.csv')
file_patterns = r"(https?://[^\s]+(\.pdf|\.docx?|\.xlsx?))"


def extract_file_links(content):
    return re.findall(file_patterns, content)


tju_news['file_links'] = tju_news['content'].apply(lambda x: extract_file_links(str(x)))
print(tju_news[['title', 'file_links']].head())
tju_news.to_csv('tju_allinfo1.csv', index=False)


# 合并tju和nku的CSV文件
df1 = pd.read_csv('tju_allinfo.csv')
df2 = pd.read_csv('nku_allinfo.csv')
concatenated_df = pd.concat([df1, df2], ignore_index=True)
concatenated_df.to_csv('all_news.csv', index=False)
print(concatenated_df.head())
