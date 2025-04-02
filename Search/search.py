from jieba import cut_for_search
from datetime import datetime,timedelta
#from readData import * 
from Search.readData import *
import math
import time
import re

# 这个函数主要用于计算输入字符串和历史记录的TF值，文档库的TF值和IDF值我们已经通过前期数据处理得到
def getTF(words, input):
    # 初始化一个词频字典，key为传入的所有的词，value为0
    tf = dict.fromkeys(words, 0)
    for word in input:
        if word in words:
            tf[word] += 1
    for word, count in tf.items():
        tf[word] = math.log10(count + 1)
    return tf

def getTF_IDF(tf, idf):
    tfidf = {}
    for word, count in tf.items():
        tfidf[word] = float(count) * float(idf[word])
    return tfidf

def getVecLength(key:list)->float:
    """
    :param key: 关键词列表
    :return: 向量长度
    """
    length = 0
    for i in range(len(key)):
        length = length + key[i][1]**2
    return round(math.sqrt(length),2)


def search_documents(input_query: str, all_info_dict: dict):
    """
    查询包含附件链接的条目，支持对附件标题、描述、链接的搜索。
    
    :param input_query: 用户输入的查询关键字
    :param all_info_dict: 包含所有网页数据的字典
    :return: 带有附件链接的查询结果列表
    """
    # 存放匹配结果
    matched_results = []
    
    for key, row in all_info_dict.items():
        doc_link = row.get("doc_link", "")
        # 跳过 doc_link 为 NaN 或者非字符串的值
        if not isinstance(doc_link, str) or not doc_link.strip():
            continue
        
        # 判断 doc_link 是否包含输入查询字符串
        if input_query.lower() in doc_link.lower():
            matched_results.append({
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "description": row.get("description", ""),
                "doc_link": doc_link
            })
    
    return matched_results

#http://epaper.jwb.com.cn/jwb/resfile/2018-12-17/02/jwb2018121702.pdf
#https://www.nature.com/articles/s41467-024-51414-6.pdf
def simple_search(input: str, history: list, onlyTitle: bool = False, num: int = 100):
    """
    :param input: 用户输入的查询字符串
    :param history: 检索历史列表
    :param onlyTitle: 是否启动仅在标题中检索
    :param num：返回结果的数量，默认为100条最相似的
    :return: 一个列表，元素为URL和相似度组成的元组
    """
    # # 判断是否输入了文档链接
    # if re.match(r'^https?://.*\.pdf$', input.strip()):
    #     print("进入文档链接查询模式")
    #     return search_documents(input_query=input.strip(), all_info_dict=all_info_dict)
    
    # 对输入中的通配符替换为正则表达式
    wildcard_to_regex = lambda s: re.sub(r"(\*)", ".*", re.sub(r"(\?)", ".", re.escape(s)))
    regex_query = wildcard_to_regex(input)
    
    # Debug: 输出正则表达式
    print(f"Converted wildcard input to regex: {regex_query}")
    
    regex = r'[\.\^\$\*\+\?\{\}\[\]\|\(\)]'
    isRe = re.search(regex, input)
    if isRe is not None:
        input = re.sub(regex, '', input)
    
    spilt_input = sorted(list(cut_for_search(input)))
    spilt_input = [term for term in spilt_input if term not in ["", " "]]
    spilt_history = []
    for i in range(len(history)):
        ls = list(cut_for_search(history[i]))
        ls = [term for term in ls if term not in ["", " "]]
        spilt_history.extend(ls)
    
    # 输出分词结果
    print(f"Spilt input: {spilt_input}")
    print(f"Spilt history: {spilt_history}")
    
    # 判断用户需要的搜索模式
    if onlyTitle:
        tf_dict = tf_title  # 读取的json数据
        idf_dict = idf_title
        words = word_set_title
    else:
        tf_dict = tf
        idf_dict = idf
        words = word_set
    
    tfidf_dict = {}
    for key, value in tf_dict.items():
        tfidf_dict[key] = getTF_IDF(value, idf_dict)
    
    # 存储关键词的tfidf值，找到num个最大的
    key_tfidf_dict = {}
    for key, value in tfidf_dict.items():
        key_tfidf_dict[key] = sorted(tfidf_dict[key].items(), key=lambda item: item[1], reverse=True)[0:num]
    
    # 保存关键词字典的key与value
    key_tfidf_dict_keys = list(key_tfidf_dict.keys())  # 即url组成的列表
    key_tfidf_dict_values = list(key_tfidf_dict.values())
    
    # 用户输入查询的TFIDF
    tf_input = getTF(words, spilt_input)
    tfidf_input = getTF_IDF(tf_input, idf_dict)
    key_input = sorted(tfidf_input.items(), key=lambda item: item[1], reverse=True)[0:num]
    len_key_input = getVecLength(key_input)
    
    # Validate input vector length
    if len_key_input == 0:
        raise ValueError("Input query resulted in an empty vector. Please refine your search query.")
    
    # 历史记录的TFIDF
    tf_history = getTF(words, spilt_history)
    tfidf_history = getTF_IDF(tf_history, idf_dict)
    key_history = sorted(tfidf_history.items(), key=lambda item: item[1], reverse=True)[0:num]
    len_key_history = getVecLength(key_history)
    
    # 如果词库里没有搜索项，那么返回错误
    if len_key_input == 0:
        print("调试信息：key_input为空，用户输入的关键词未在词库中找到。")
        raise KeyError("用户输入的关键词未找到，请检查索引或输入的正确性。")
    
    # 向量空间模型，计算余弦相似度
    key_results = []  # 用于存储余弦相似度
    key_results_index = []  # 记录文档索引
    for i in range(len(key_tfidf_dict_keys)):
        length = 0
        temp_list = key_tfidf_dict_values[i]
        # 遍历每个输入关键词
        for key in key_input:
            if key[1] != 0:  # tf-idf值不为0才存在相似度
                # 遍历文档内的每个关键词
                for value in temp_list:
                    if key[0] == value[0]:
                        length = length + key[1] * value[1]
        res = getVecLength(temp_list)
        if res == 0.0:
            continue
        # 余弦相似度
        sim = round(length / (len_key_input * res), 4)
        
        key_results.append((key_tfidf_dict_keys[i], sim))
        if sim > 0:
            key_results_index.append(i)
    
    if len(history) > 0:
        history_results_dict = {}
        for item in key_results_index:
            length = 0
            temp_list = key_tfidf_dict_values[item]
            for _key_history in key_history:
                if _key_history[1] != 0:
                    for value in temp_list:
                        if _key_history[0] == value[0]:
                            length = length + _key_history[1] * value[1]
            sim = round(length / (len_key_history * getVecLength(temp_list)), 4)
            history_results_dict[item] = (key_tfidf_dict_keys[item], sim)
        
        results = []
        for i in range(len(key_tfidf_dict_keys)):
            if i >= len(key_results):
                break
            #print(f"Key results输出结果调试: {key_results[i][1]}")
            if key_results[i][1] == 0:
                pass
            elif j := history_results_dict.get(i):
                # 设置历史记录的权重为0.1
                results.append((key_results[i][0], key_results[i][1] + j[1] / 10))
            else:
                results.append((key_results[i][0], key_results[i][1]))
        results = sorted(results, key=lambda item: item[1], reverse=True)
    # 没有历史记录时，直接利用字典计算余弦相似度即可
    else:
        results = []
        for i in range(len(key_tfidf_dict_keys)):
            if i >= len(key_results):
                break
            results.append((key_results[i][0], key_results[i][1]))
        results = sorted(results, key=lambda item: item[1], reverse=True)
    

    ls, ans = [], []
    for res in results:
        if res[1] > 0:
            ls.append((res[0], res[1]))
    if isRe is not None:
        for item in ls:
            row = all_info_dict.get(item[0])
            if re.search(regex_query, row['title']) or re.search(regex_query, row['description']):
                ans.append(item)
    if isRe is None:
        return ls 
    return ans

def simple_search_test(input:str,history:list):
    time1 = time.time()
    ret = simple_search(input,history)
    print("在全文中出现的结果：")
    time2 = time.time()
    for item in ret:
        print(item)
    print("在"+str(time2-time1)+"秒时间内响应，返回"+str(len(ret))+"项结果")

    time1 = time.time()
    ret = simple_search(input,history,True)
    time2 = time.time()
    print("仅在标题中出现的结果：")
    for item in ret:
        print(item)
    print("在" + str(time2 - time1) + "秒时间内响应，返回" + str(len(ret)) + "项结果")
    
def expand_results(results: list):
    expanded = []
    for res in results:
        url = res[0]
        
        # 从字典中查找 all_info
        row = all_info_dict.get(url)
        if row is None:
            print(f"URL {url} 不存在于 all_info 中，跳过该项。")
            continue
        
        title = str(row['title']).replace("_", "/")
        dsp = str(row['description'])
        
        # 从字典中查找 page_rank 值，默认为 0
        page_rank_value = page_rank_dict.get(url, 0)
        if page_rank_value == 0:
            print(f"URL {url} 不存在于 page_rank 中，使用默认值 0 计算综合得分。")
        
        # 计算综合得分
        score = res[1] * 0.7 + 0.3 * page_rank_value
        expanded.append((title, url, dsp, score))
    
    # 按综合得分排序
    return sorted(expanded, key=lambda item: item[-1], reverse=True)


# 测试函数：接收输入和历史记录，并打印结果
def expand_results_test(input: str, history: list):
    results = simple_search(input, history, True)  # 假设 simple_search 返回一个结果列表
    expanded = expand_results(results)
    for entry in expanded:
        print(entry)

# 带有发布时间限制的搜索函数
def check_time(result,limit):
    """
    :param result: simple_search返回结果拓展后的结果的一行
    :param limit：时间限制字符串
    :return: 是否满足要求
    """
    row = all_info_dict.get(result[1])
    if str(row['date']) != "nan":
        # 将时间戳转换为datetime
        articleTime = datetime.fromtimestamp(int(row['date']))
        res = datetime.now() - articleTime
        if limit == "一周内":
            if res > timedelta(days=7):
                return False
        elif limit == "一个月内":
            if res > timedelta(days=30):
                return False
        elif limit == "一年内":
            if res > timedelta(days=365):
                return False
    if str(row['date']) == "nan":
        return False
    return True

def check_time_test(input,limit):
    ret = simple_search(input,[])
    expanded = expand_results(ret)
    print("时间限制添加前的结果，共有"+str(len(expanded))+"条：")
    for item in expanded:
        print(item)
    expanded = [item for item in expanded if check_time(item,limit)==True]
    print("时间限制添加后的结果，共有"+str(len(expanded))+"条：")
    for item in expanded:
        print(item)

# 检查是不是指定的域名或者网站
def check_website(result,name):
    if name not in result[1]:
        return False
    return True

def check_website_test(input,name):
    ret = simple_search(input,[])
    expanded = expand_results(ret)
    print(f"网站或域名限制前的结果，共有{len(expanded)}条：")
    for item in expanded:
        print(item)
    expanded = [item for item in expanded if check_website(item,name)==True]
    print(f"网站或域名限制后的结果，共有{len(expanded)}条：")
    for item in expanded:
        print(item)
        
# 检查是否和规定的词匹配，传入一个标志位代表是否进行完全匹配
# 如果不进行完全匹配，那么只要出现一个词就可以判定为True
def check_match_words(result,input,complete=True):
    row = all_info_dict.get(result[1])  
    text = f"{row['title']}#{row['description']}#{row['content']}#{row['editor']}"
    ls = str(input).split(" ")
    for word in ls:
        if word == '#':
            pass
        if word not in text:
            if complete == True:
                return False
        if word in text:
            if complete == False:
                return True
    if complete == True:
        return True
    return False

def check_complete_match_test(input,limit):
    ret = simple_search(input,[])
    expanded = expand_results(ret)
    print(f"限制前的结果，共有{len(expanded)}条：")
    expanded = [item for item in expanded if check_match_words(item,limit,True) == True]
    print(f"包含以下所有词限制后的结果，共有{len(expanded)}条：")
    for item in expanded:
        print(item)
        
# 检查是否不含一些词
def check_not_include(result,input):
    row = all_info_dict.get(result[1])
    text = f"{row['title']}#{row['description']}#{row['content']}#{row['editor']}"
    ls = str(input).split(" ")
    ls = [word for word in ls if word != '']
    for word in ls:
        if word == '#':
            pass
        if word in text:
            return False
    return True


def load_file_links_from_csv(file_path):  
    """  
    Load file links from a CSV file and return as a DataFrame.  

    Parameters:  
    file_path (str): The path to the CSV file.  

    Returns:  
    DataFrame: A DataFrame containing file links.  
    """  
    return pd.read_csv(file_path)  

def search_file_link(file_df, query):  
    """  
    Search for a file link based on the query in the DataFrame.  

    Parameters:  
    file_df (DataFrame): The DataFrame containing file links.  
    query (str): The query to search for.  

    Returns:  
    dict: A dictionary with link and description if found, else None.  
    """  
     # 处理缺失值  
    file_df = file_df.dropna(subset=['title'])  
    filtered_files = file_df[file_df['title'].str.contains(query, case=False)]  
    if not filtered_files.empty:  
        return filtered_files.iloc[0].to_dict()  
    return None  

def test_file_link_search(query, file_df):  
    file_link = search_file_link(file_df, query)  
    if file_link:  
        print(f"文件链接: {file_link['url']} - {file_link['title']}")  
    else:  
        print("未找到匹配的文件链接。")  

output_csv_file = './spider/file_links.csv'  # CSV 文件的路径  
file_sparse_links = load_file_links_from_csv(output_csv_file)  

if __name__ == "__main__":  
    # Step 1: Load file links from CSV  
    output_csv_file = './spider/file_links.csv'  # CSV 文件的路径  
    file_sparse_links = load_file_links_from_csv(output_csv_file)  

    # Step 2: Test search function  
    test_query = "新冠肺炎防控指南漫画（汉西双语）"  # 示例查询  
    test_query = ""  # 示例查询  
    test_file_link_search(test_query, file_sparse_links)
    #ret = simple_search("123",[])
    #ret = expand_results(ret)
    #print(ret)
    # ret = [item for item in ret if check_time(item,"一年内")]
    # print(f"过滤时间后，剩余{len(ret)}条")
    # ret = [item for item in ret if check_website(item,"nankai")]
    # print(f"过滤来源后，剩余{len(ret)}条")
    # ret = [item for item in ret if check_match_words(item,"校长 大学",True)]
    # for item in ret:
    #     print(item)
    # print(f"过滤必须词后，剩余{len(ret)}条")
    # check_complete_match_test("运动会","\"校长\"")
    # 查询所有 PDF 附件
    #results = search_documents("*.pdf", all_info_dict)
    #results1 = search_documents("onlinelibrary", all_info_dict)#搜索链接名
    #print(results)