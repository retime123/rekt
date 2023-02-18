# -*- coding: UTF-8 -*-
"""
https://rekt.news/en/

author:chengzi

模板
"""
import os, sys
import scrapy
from bs4 import BeautifulSoup
from spiderprocessor3.spiders.base_spider import BaseSpider
from spiderprocessor3.common.common_util import *
from spiderprocessor3.config.ipconfig.config import *
from urllib.parse import urlparse  # python3用法
import traceback
import csv, xlwt


class rekt_news3(BaseSpider):
    name = "rekt_news3"
    start_url = 'https://rekt.news/en/'
    # js_url = 'https://rekt.news/_next/static/chunks/397-7023138e71fd12f9.js'
    base_url = "https://rekt.news"
    template_url = ''
    detail_url_template = 'https://rekt.news/{0}/'
    is_proxy = False
    proxy_type = PROXY_TYPE_SSA
    count = 0

    custom_settings = {
        'RETRY_TIMES': 10,  # 重试次数
        'DOWNLOAD_TIMEOUT': 15,  # 超时时间
        'CONCURRENT_REQUESTS': 10,  # 同时最大允许量
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,  # 同一个ip同时最大允许量
        'REDIRECT_ENABLED': False,  # 重定向：False关闭
        'HTTPERROR_ALLOWED_CODES': [302, 304, ],  # 状态码：允许
        'RETRY_HTTP_CODES': [504, 408, 500, 502, 503, 533, 407, 403, 400],  # 状态码：重试
        # 'DOWNLOAD_DELAY': 0.2, # 间隔
        'COOKIES_ENABLED': False,
        'REFERER_ENABLED': False,
    }

    def __init__(self, page=1, increment=False, *args, **kwargs):
        super(eval(self.__class__.__name__), self).__init__(*args, **kwargs)
        path = os.path.abspath(os.path.dirname(sys.argv[0]))
        store_file = 'rekt_news.csv'
        self.file = open(store_file, 'w', encoding='utf-8', newline='')
        # csv写法
        self.writer = csv.writer(self.file)
        self.label = ['NewsId', 'Title', 'NewsTime', 'AttackerAddress', 'AttackerTx', 'ExploitTx', 'ExploitAddress',
                        'ExampleTx', 'ExampleTransaction','Ethereum', 'HackerAddress', 'HackerWallet', 'AttackTransaction',
                      'AttackContract', 'Url', 'Content']
        self.writer.writerow(self.label)

    def start_requests(self):
        yield scrapy.Request(url=self.start_url,
                             encoding='utf-8', method='GET',
                             headers=self.head(self.start_url),
                             callback=self.parse,
                             dont_filter=True)

    def parse(self, response):
        req_url = response.url
        # print '当前页', req_url
        resp_text = response.text
        resp_doc = BeautifulSoup(resp_text, 'html5lib')

        # 获取下一页
        try:
            pages_temp = resp_doc.select_one('script[src*="_next/static/chunks/397"]').attrs.get('src')
            # 'https://rekt.news/_next/static/chunks/397-7023138e71fd12f9.js'
            u = self.base_url + pages_temp
            yield scrapy.Request(url=u,
                                 encoding='utf-8', method='GET',
                                 headers=self.head(self.start_url),
                                 callback=self.processlist,
                                 dont_filter=True)
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def processlist(self, response):
        req_url = response.url
        # print '当前页', req_url
        resp_text = response.text
        # resp_doc = BeautifulSoup(resp_text, 'html5lib')
        # 获取列表  en:6426    zh:1024
        _list = re.findall(r"6426:.*?exports=JSON.parse\('(.*?)'\)}", resp_text, re.S)
        aa = re.findall('{.*?slug.*?}', _list[0])
        slug = []
        for k in aa:
            v = re.findall(r'{"date":\s?"(.*?)".*?slug":.*?"(.*?)"', k)
            if v and v[0][1] not in slug:
                slug.append(v[0][1])
        print(len(slug))
        for item in slug[:]:
            try:
                u = self.detail_url_template.format(item)
                # print(u)
                # u = 'https://rekt.news/en/orion-protocol-rekt/'
                # u = 'https://rekt.news/dforce-network-rekt/'
                # u = 'https://rekt.news/indexed-finance-rekt/'
                # u = 'https://rekt.news/chainswap-rekt/'
                # u = 'https://rekt.news/voltage-finance-rekt/'
                yield scrapy.Request(url=u,
                                     encoding='utf-8', method='GET',
                                     headers=self.head(self.start_url),
                                     callback=self.processdetail,
                                     dont_filter=True)
            except Exception as e:
                # print(n, req_url)
                self.logger.error(traceback.format_exc())

    def processdetail(self, response):
        req_url = response.url
        resp_body = response.body
        # resp_doc = BeautifulSoup(resp_body, 'html5lib', from_encoding='utf-8')
        resp_doc = BeautifulSoup(resp_body, 'html5lib')
        table_if = resp_doc.select('div[id="zoom"] table')  # 判断是否有表格
        try:
            Title = resp_doc.select_one('h1[class="post-title"]').get_text().strip()
            # NewsTime = resp_doc.select('main header:nth-of-type(1) span[class="post-meta"] time')[0].get_text().strip()
            NewsTime = resp_doc.select('main > article > header span[class="post-meta"] time')[0].get_text().strip()
            self.count += 1
            print(self.count, Title, NewsTime, req_url)
            Content_tag = resp_doc.select_one('section[class="post-content"]')
            if Content_tag:
                div_del = Content_tag.select('div[id="mc_embed_signup"]')
                next_del = div_del[0].next_siblings
                # 删除不必要的数据
                for j in list(next_del):
                    j.decompose()
                for i in div_del:
                    i.decompose()
                Content = Content_tag.get_text().strip()
                Attacker_address = []
                Attacker_tx = []
                Exploit_tx = []
                Example_tx = []
                Exploit_address = []
                Example_transaction = []
                Hacker_address = []
                Ethereum = []
                Hacker_wallet = []
                Attack_transaction = []
                Attack_contract = []
                base_tag = Content_tag.select('p')
                for n, tg in enumerate(base_tag):
                    new_tag = str(tg)
                    if n < len(base_tag) - 1:
                        new_tag += str(base_tag[n+1])
                    Attacker_address_temp = re.findall(r'[Aa]ttacker.*? [Aa]ddress.*?:.*(http.*?0x.*?)">', str(new_tag), re.S)
                    if Attacker_address_temp:
                        Attacker_address += Attacker_address_temp
                    Attacker_tx_temp = re.findall(r'[Aa]ttack.*? tx.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Attacker_tx_temp:
                        Attacker_tx += Attacker_tx_temp
                    Exploit_tx_temp = re.findall(r'[Ee]xploit.*? [Tt]x.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Exploit_tx_temp:
                        Exploit_tx += Exploit_tx_temp
                    Example_tx_temp = re.findall(r'[Ee]xample.*? [Tt]x.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Example_tx_temp:
                        Example_tx += Example_tx_temp
                    Exploit_address_temp = re.findall(r'[Ee]xploiter.*? [Aa]ddress.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Exploit_address_temp:
                        Exploit_address += Exploit_address_temp
                    Example_transaction_temp = re.findall(r'[Ee]xample.*? [Tt]ransaction.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Example_transaction_temp:
                        Example_transaction += Example_transaction_temp
                    Ethereum_temp = re.findall(r'[Ee]Hacker.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Ethereum_temp:
                        Ethereum += Ethereum_temp
                    Hacker_address_temp = re.findall(r'[Hh]acker.*? [Aa]ddress.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Hacker_address_temp:
                        Hacker_address += Hacker_address_temp
                    Hacker_wallet_temp = re.findall(r'[Hh]acker.*? [Ww]allet.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Hacker_wallet_temp:
                        Hacker_wallet += Hacker_wallet_temp
                    Attack_transaction_temp = re.findall(r'[Aa]ttack.*? [Tt]ransaction.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Attack_transaction_temp:
                        Attack_transaction += Attack_transaction_temp
                    Attack_contract_temp = re.findall(r'[Aa]ttack.*? [Cc]ontract.*?:.*?(http.*?0x.*?)">', str(new_tag), re.S)
                    if Attack_contract_temp:
                        Attack_contract += Attack_contract_temp
                if Content:
                    anno_info = {}
                    print('Process detail success: ' + req_url)
                    anno_info['Title'] = Title
                    anno_info['NewsTime'] = NewsTime
                    anno_info['Url'] = req_url
                    if Attacker_address:
                        anno_info['AttackerAddress'] = ', '.join([i.strip() for i in list(set(Attacker_address))])
                    else:
                        anno_info['AttackerAddress'] = ''
                    if Attacker_tx:
                        anno_info['AttackerTx'] = ', '.join([i.strip() for i in list(set(Attacker_tx))])
                    else:
                        anno_info['AttackerTx'] = ''
                    if Exploit_tx:
                        anno_info['ExploitTx'] = ', '.join([i.strip() for i in list(set(Exploit_tx))])
                    else:
                        anno_info['ExploitTx'] = ''
                    if Example_tx:
                        anno_info['ExampleTx'] = ', '.join([i.strip() for i in list(set(Exploit_tx))])
                    else:
                        anno_info['ExampleTx'] = ''
                    if Exploit_address:
                        anno_info['ExploitAddress'] = ', '.join([i.strip() for i in list(set(Exploit_address))])
                    else:
                        anno_info['ExploitAddress'] = ''
                    if Example_transaction:
                        anno_info['ExampleTransaction'] = ', '.join([i.strip() for i in list(set(Example_transaction))])
                    else:
                        anno_info['ExampleTransaction'] = ''
                    if Ethereum:
                        anno_info['Ethereum'] = ', '.join([i.strip() for i in list(set(Ethereum))])
                    else:
                        anno_info['Ethereum'] = ''
                    if Hacker_address:
                        anno_info['HackerAddress'] = ', '.join([i.strip() for i in list(set(Hacker_address))])
                    else:
                        anno_info['HackerAddress'] = ''
                    if Hacker_wallet:
                        anno_info['HackerWallet'] = ', '.join([i.strip() for i in list(set(Hacker_wallet))])
                    else:
                        anno_info['HackerWallet'] = ''
                    if Attack_transaction:
                        anno_info['AttackTransaction'] = ', '.join([i.strip() for i in list(set(Attack_transaction))])
                    else:
                        anno_info['AttackTransaction'] = ''
                    if Attack_contract:
                        anno_info['AttackContract'] = ', '.join([i.strip() for i in list(set(Attack_contract))])
                    else:
                        anno_info['AttackContract'] = ''
                    anno_info['Content'] = str(Content_tag)
                    anno_info['NewsId'] = md5encode(Content)

                    # 3个字段定位pipeline
                    # anno_info['FileName'] = 'env_punishment_pipeline'
                    # anno_info['Class'] = 'EnvPunishPipeline'
                    # anno_info['Method'] = 'insert_env_punish_db'
                    # yield anno_info

                    print(anno_info)
                    value = [anno_info[i] for i in self.label]
                    self.writer.writerow(value)
            else:
                print('Process detail fail :content or companyname is null or empty ,req_url is ' + req_url)
        except Exception as e:
            print(traceback.format_exc())
            print('错误', response.url)

    def head(self, u, dict_data=None):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': urlparse(u).netloc,
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://rekt.news/en/?page=1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
        }
        if isinstance(dict_data, dict):
            new_dict = {}
            for k, v in dict_data.items():
                # # 把第一个字母转化为大写字母，其余小写
                # new_dict[k.capitalize()] = v
                # 把每个单词的第一个字母转化为大写，其余小写
                new_dict[k.title()] = v
            headers.update(new_dict)
        return headers


if __name__ == '__main__':
    import os, re
    from scrapy import cmdline

    fileName = os.path.abspath(__file__)
    try:
        file = open(fileName, 'r').readlines()
    except:
        file = open(fileName, 'r', encoding='utf-8').readlines()  # python3
    className = None
    for i in file:
        if i.startswith('class'):
            className = re.findall(r'\s+(\w+)', i)[0]
            break
    if className:
        name = eval(className).name
        # cmdline.execute("scrapy crawl {0}".format(name).split())
        cmdline.execute("scrapy crawl {0} -s SPIDER_MODULES=spiderprocessor3.spiders.{1}".format(name, fileName.split(
            'spiders\\')[1].split('.py')[0].replace('\\', '.')).split())
    else:
        print('获取类名失败！')
