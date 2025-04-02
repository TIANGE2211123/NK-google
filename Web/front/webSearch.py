import time
from flask import render_template, request, Response
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired
from . import front
from Search.search import *
from datetime import datetime

class AdvancedSearchForm(FlaskForm):
    all_these_words = StringField('关键词：', validators=[DataRequired()])
    this_exact_word_or_phrase = StringField('完全匹配')
    any_of_these_words = StringField('部分匹配')
    none_of_these_words = StringField('不包含')
    site_or_domain = StringField('网站或域名：')
    time_limit = SelectField('时间范围', choices=["任何时间", "一个月内", "一年内"], validators=[DataRequired()])
    is_title_only = RadioField('查询关键词位于', choices=["全部网页", "标题","文档"], validators=[DataRequired()])
    submit = SubmitField("开启高级搜索！")


@front.route('/advanced_search', methods=['GET', 'POST'])
def _advanced_search():
    form = AdvancedSearchForm(is_title_only='全部网页')  # 实例化表单，并且默认搜索全部网页
    if request.method == 'GET':
        if request.args.get('keywords'):
            form.all_these_words.data = request.args.get('keywords')

    if form.validate_on_submit():
        t = time.perf_counter()
        all_these_words = form.all_these_words.data

        if request.cookies.get('search_history'):
            # 从cookie中获取搜索历史
            search_history: list = json.loads(request.cookies.get('search_history'))
        else:
            search_history = []

        if form.is_title_only.data == '标题':
            is_title_only = True
        else:
            is_title_only = False
            
        # #try:
        # if form.is_title_only.data == '文档':
        #     result_list = search_file_link(file_df, all_these_words)  # 直接搜索文件
        #     if result_list:
        #         results = [result_list] 
        #     else:
        #         results = []
        # else:
        #     result_list = simple_search(all_these_words, search_history, form.is_title_only.data == '标题')
        #     results = expand_results(result_list)  # 扩展出title description time content editor
        # try:
        #     if not is_title_only:  # 搜索全部网页
        #         result_list = simple_search(all_these_words, search_history)
        #     else:
        #         result_list = simple_search(all_these_words, search_history, True)
        # except KeyError:
        #     cost_time = f'{time.perf_counter() - t: .2f}'
        #     return render_template(r'404.html', keywords=all_these_words, cost_time=cost_time)

        try:
            if form.is_title_only.data == '文档':
                result_list = search_file_link(file_sparse_links, all_these_words)  # 直接搜索文件
                if result_list:
                    results = [result_list] 
                else:
                    results = []
                print(results)
            else:
                result_list = simple_search(all_these_words, search_history, form.is_title_only.data == '标题')
                results = expand_results(result_list)  # 扩展出title description time content editor

            # 应用过滤条件，但仅当不是搜索文档时
            if form.is_title_only.data =='网页' or form.is_title_only.data =='标题':

                results = [result for result in results if check_time(result, form.time_limit.data) == True]

                if form.site_or_domain.data:
                    domain = str(form.site_or_domain.data).split("value")[-1][2:].split("\"")[0]
                    results = [result for result in results if check_website(result, str(domain)) == True]

                if form.none_of_these_words.data:
                    results = [result for result in results if check_not_include(result, form.none_of_these_words.data) == True]

                if form.this_exact_word_or_phrase.data:
                    results = [result for result in results if check_match_words(result, form.this_exact_word_or_phrase.data) == True]

                if form.any_of_these_words.data:  
                    # 将任意匹配的词分割成列表  
                    any_words = form.any_of_these_words.data.split(',')  
                    # 使用任意匹配逻辑过滤结果  
                    results = [result for result in results if any(check_match_words(result, word.strip(), False) for word in any_words)] 
        except KeyError:
            cost_time = f'{time.perf_counter() - t: .2f}'
            return render_template(r'404.html', keywords=all_these_words, cost_time=cost_time)
    
        cost_time = f'{time.perf_counter() - t: .2f}'
        if len(results) == 0:
            return render_template(r'404.html', keywords=all_these_words, cost_time=cost_time)

        response = Response(render_template(r'result_page.html', keywords=all_these_words, results=results, len_results=len(results), cost_time=cost_time,search_history=search_history))

        if all_these_words not in search_history:
            search_history.append(all_these_words)
        if len(search_history) > 10:
            search_history.pop(0)
        response.set_cookie('search_history', json.dumps(search_history), max_age=60 * 60 * 24 * 30)

        return response

    return render_template(r'advanced_search.html', form=form)