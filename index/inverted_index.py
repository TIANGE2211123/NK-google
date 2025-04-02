import pandas as pd
import numpy as np
import os
import json
import ijson

# 读取 CSV 文件
data = pd.read_csv("total_news.csv", encoding='utf-8-sig', index_col='url')

# 创建目录，存储倒排索引文件
os.mkdir("./jsons")

# 读取停用词表
stopWords = []
with open("stopwords.txt", 'r', encoding='utf-8') as f:
    words = f.read().splitlines()
stopWords.extend(words)


# 为每个HTML文档计算词频，用于后续构建倒排索引
def calculateTFInHTML(data=data, title_only=False):
    # 要返回的“正向”索引词典，映射关系为：url->{}，而作为value的词典是一个词项到词频的映射
    index = {}
    # 遍历data的每一行，遍历标题，内容等信息，计算词频
    for url, info in data.iterrows():
        index[url] = {}
        if isinstance(info['title'], str):  # 检查是否为字符串
            for word in info['title'].split(" "):
                # 不在停用词列表中的才计数
                if word not in stopWords:
                    if word not in index[url]:
                        index[url][word] = 1
                    else:
                        index[url][word] += 1
        if not title_only:
            if isinstance(info['description'], str):  # 检查是否为字符串
                for word in info['description'].split(" "):
                    if word not in stopWords:
                        if word not in index[url]:
                            index[url][word] = 1
                        else:
                            index[url][word] += 1
            if isinstance(info['content'], str):  # 检查是否为字符串
                for word in info['content'].split(" "):
                    if word not in stopWords:
                        if word not in index[url]:
                            index[url][word] = 1
                        else:
                            index[url][word] += 1
            if isinstance(info['editor'], str):  # 检查是否为字符串
                for word in info['editor'].split(" "):
                    if word not in stopWords:
                        if word not in index[url]:
                            index[url][word] = 1
                        else:
                            index[url][word] += 1
    return index


index = calculateTFInHTML(data)
index_only_title = calculateTFInHTML(data, True)

# 倒排索引构建
def gen_inverted_index(index):
    inverted_index = {}
    # 遍历原始索引中的每个URL和对应的词汇及频率信息
    for url, words in index.items():
        # 遍历每个URL对应的词汇及其频率信息
        for word, frequency in words.items():
            # 如果当前词汇不在倒排索引中，就创建一个空字典作为该词的索引项
            if word not in inverted_index:
                inverted_index[word] = {}
            inverted_index[word][url] = frequency
    return inverted_index


inverted_index = gen_inverted_index(index)
inverted_index_only_title = gen_inverted_index(index_only_title)

# 计算TF
def get_TF(index):
    tf = {}
    for url, words in index.items():
        temp_dict = {}
        for word, frequency in words.items():
            temp_dict[word] = frequency
        tf[url] = temp_dict
    return tf


tf = get_TF(index)
tf_only_title = get_TF(index_only_title)

# 计算IDF
def get_IDF(index):
    idf = {}
    num_docs = len(index)
    doc_count = {}
    for url, frequency_dict in index.items():
        for word in frequency_dict.keys():
            if word not in doc_count:
                doc_count[word] = 0
            doc_count[word] += 1
    for word, count in doc_count.items():
        idf[word] = np.log(num_docs / count)
    return idf


IDF = get_IDF(index)
IDF_only_title = get_IDF(index_only_title)

# 计算tf-idf值
def get_TF_IDF(index, IDF):
    tf_idf = {}
    for url, words in index.items():
        temp_dict = {}
        for word, frequency in words.items():
            temp_dict[word] = frequency * IDF[word]
        tf_idf[url] = temp_dict
    return tf_idf


TF_IDF = get_TF_IDF(index, IDF)
TF_IDF_only_title = get_TF_IDF(index_only_title, IDF_only_title)

# 保存各个文档的TF-IDF值
with open('./jsons/tf-idf.json', 'w', encoding='utf-8') as f:
    json.dump(TF_IDF, f, ensure_ascii=False)
with open('./jsons/tf-idf_title.json', 'w', encoding='utf-8') as f:
    json.dump(TF_IDF_only_title, f, ensure_ascii=False)
with open("./jsons/tf.json", 'w', encoding='utf-8') as f:
    json.dump(tf, f, ensure_ascii=False)
with open("./jsons/tf_title.json", 'w', encoding='utf-8') as f:
    json.dump(tf_only_title, f, ensure_ascii=False)
with open("./jsons/idf.json", 'w', encoding='utf-8') as f:
    json.dump(IDF, f, ensure_ascii=False)
with open("./jsons/idf_title.json", 'w', encoding='utf-8') as f:
    json.dump(IDF_only_title, f, ensure_ascii=False)

# 保存倒排索引为json格式，便于前端使用
with open('./jsons/invert_index.json', 'w', encoding='utf-8') as f:
    json.dump(inverted_index, f, ensure_ascii=False)
with open('./jsons/invert_index_title.json', 'w', encoding='utf-8') as f:
    json.dump(inverted_index_only_title, f, ensure_ascii=False)

# 下面计算一下HTML库中所有非停用词的词频，方便推荐系统实现以及词云功能实现
def getAllTF(index):
    word_frequency = {}
    for url, words in index.items():
        for word, frequency in words.items():
            if word not in word_frequency:
                word_frequency[word] = frequency
            else:
                word_frequency[word] += frequency
    return word_frequency


with open('./jsons/allTF.json', 'w', encoding='utf-8') as f:
    json.dump(getAllTF(index), f, ensure_ascii=False)
with open('./jsons/allTF_title.json', 'w', encoding='utf-8') as f:
    json.dump(getAllTF(index_only_title), f, ensure_ascii=False)

# 结果展示
# 逐步解析 JSON 文件
with open('jsons/invert_index.json', 'r', encoding='utf-8') as file:
    # ijson 逐步解析，假设 '计算机' 对应的是一个列表
    objects = ijson.items(file, '计算机')
    for obj in objects:
        # 假设 obj 是一个列表或者字典，每个元素或者每个键值对逐个打印
        if isinstance(obj, list):
            # 如果 obj 是一个列表，逐个打印列表项
            for item in obj:
                print(item)
        elif isinstance(obj, dict):
            # 如果 obj 是字典，逐个打印键值对
            for key, value in obj.items():
                print(f"{key}: {value}")

# 逐步解析 JSON 文件
with open('jsons/tf-idf.json', 'r', encoding='utf-8') as file:
    objects = ijson.items(file, 'http://news.nankai.edu.cn/ywsd/system/2017/01/29/000316735.shtml')
    for obj in objects:
        # 假设 obj 是一个列表或者字典，每个元素或者每个键值对逐个打印
        if isinstance(obj, list):
            # 如果 obj 是一个列表，逐个打印列表项
            for item in obj:
                print(item)
        elif isinstance(obj, dict):
            # 如果 obj 是字典，逐个打印键值对
            for key, value in obj.items():
                print(f"{key}: {value}")
    