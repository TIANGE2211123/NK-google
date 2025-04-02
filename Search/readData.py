import json
import os
import pandas as pd
from bs4 import BeautifulSoup

path = "./index/jsons"
rankPath = "./rank"
spiderPath = "./spider"
html_directory = './spider/htmls' 

# 读取index/jsons下的所有数据：
with open(os.path.join(path,'invert_index.json'),'r',encoding='utf-8') as f:
    invert_index = json.load(f)

with open(os.path.join(path,'invert_index_title.json'),'r',encoding='utf-8') as f:
    invert_index_title = json.load(f)

with open(os.path.join(path,'tf-idf.json'),'r',encoding='utf-8') as f:
    tf_idf = json.load(f)

with open(os.path.join(path,'tf-idf_title.json'),'r',encoding='utf-8') as f:
    tf_idf_title = json.load(f)

# 读取词频，即所有出现过的词的TF值
with open(os.path.join(path,"allTF.json"),'r',encoding='utf-8') as f:
    word_frequency = json.load(f)
    word_set = sorted(set(word_frequency.keys()))

with open(os.path.join(path,"allTF_title.json"),'r',encoding='utf-8') as f:
    word_frequency_title = json.load(f)
    word_set_title = sorted(set(word_frequency_title.keys()))

with open(os.path.join(path,"tf.json"),'r',encoding='utf-8') as f:
    tf = json.load(f)

with open(os.path.join(path,"tf_title.json"),'r',encoding='utf-8') as f:
    tf_title = json.load(f)

with open(os.path.join(path,"idf.json"),'r',encoding='utf-8') as f:
    idf = json.load(f)

with open(os.path.join(path,"idf_title.json"),'r',encoding='utf-8') as f:
    idf_title = json.load(f)


# 读取csv文件：
page_rank = pd.read_csv(os.path.join(rankPath, "page_rank_allnews.csv"), encoding='utf-8-sig')
all_info = pd.read_csv(os.path.join(spiderPath, "all_news.csv"), encoding='utf-8')

all_info_dict = all_info.set_index('url').to_dict(orient='index')
page_rank_dict = page_rank.set_index('url')['page_rank'].to_dict()

# print(all_info_dict)

def extract_file_links_from_html(html_directory):  

    file_links = []  
    # Supported file extensions  
    supported_extensions = ('.pdf', '.doc', '.docx', '.xls', '.xlsx')  
    
    # Traverse all HTML files in the directory  
    for filename in os.listdir(html_directory):  
        if filename.endswith('.html'):  
            file_path = os.path.join(html_directory, filename)  
            with open(file_path, 'r', encoding='utf-8') as file:  
                content = file.read()  
                soup = BeautifulSoup(content, 'html.parser')  

                # Find all links  
                links = soup.find_all('a', href=True)  
                for link in links:  
                    href = link['href']  
                    if href.endswith(supported_extensions):  # Check if it's one of the supported types  
                        # Ensure it is a complete URL  
                        if not href.startswith(('http://', 'https://')):  
                            href = os.path.join(os.path.dirname(file_path), href)  
                        file_links.append({'title': link.get_text(), 'url': href})  
    return file_links  

def create_file_links_dataframe(file_links):  
    """  
    Creates a DataFrame from the list of file links.  
    
    Parameters:  
    file_links (list): A list of dictionaries with 'title' and 'url'.  
    """  
    file_df = pd.DataFrame(file_links)  
    # Optionally, drop duplicates based on 'title'  
    file_df.drop_duplicates(subset='title', inplace=True)  
    return file_df  

def save_file_links_to_csv(file_df, output_file):  
    
    file_df.to_csv(output_file, index=False)  
    
    
if __name__ == "__main__":  
    
    file_links = extract_file_links_from_html(html_directory)  

    file_df = create_file_links_dataframe(file_links)  
    output_csv_file = os.path.join(spiderPath, "file_links.csv")  # Desired CSV file name  
    save_file_links_to_csv(file_df, output_csv_file)  

    # You may want to print file_df to check the extracted file links  
    print(file_df)