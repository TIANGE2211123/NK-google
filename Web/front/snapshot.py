import json

from flask import render_template, request

from . import front
from Search.readData import *


@front.route('/snapshot')
def _snapshot():
    if url := request.args.get('url'):
        #title = all_info_dict.get[url]['title']
        title = all_info_dict.get(url, {}).get('title', '') 
        with open(rf'./spider/htmls/{title}.html',encoding='utf-8') as f:
            snapshot = f.read()
        # 向前端以网页的形式返回快照
        return render_template(r'snapshot.html', snapshot=snapshot)
    else:
        return "invalid arguments!"
    