# Copyright (c) 2018-present, Taatu Ltd.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import sys
import os
import datetime
import time
from datetime import timedelta
import feedparser
from get_sentiment_score import *

pdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(pdir) )
from settings import *
sett = sa_path()

sys.path.append(os.path.abspath( sett.get_path_feed() ))
from add_feed_type import *

sys.path.append(os.path.abspath( sett.get_path_pwd() ))
from sa_access import *
access_obj = sa_db_access()


db_usr = access_obj.username(); db_pwd = access_obj.password(); db_name = access_obj.db_name(); db_srv = access_obj.db_server()

sys.path.append(os.path.abspath( sett.get_path_feed() ))
from add_feed_type import *

from pathlib import Path

import pymysql.cursors
connection = pymysql.connect(host=db_srv,
                             user=db_usr,
                             password=db_pwd,
                             db=db_name,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

def get_newsdata(limit):
    try:
        d = datetime.datetime.now()
        dn = datetime.datetime.now() - timedelta(days=1)
        dh = datetime.datetime.now() - timedelta(days=30)
        d = d.strftime("%Y%m%d")
        dn = dn.strftime("%Y%m%d")
        dh = dh.strftime("%Y%m%d")

        feed_id = 3
        feed_type = "news"
        if limit == 0: limit = 1000
        add_feed_type(feed_id, feed_type)
        get_newsdata_rss(d,feed_id,limit)
        if limit == 0:
            count_news(dn,feed_id)
            clear_old_newsdata(dh,feed_id)

    except Exception as e: print(e)

def get_newsdata_rss(d,feed_id,limit):
    try:
        cr = connection.cursor(pymysql.cursors.SSCursor)
        sql = 'SELECT url,format,type,asset_class,market,lang FROM newsdata WHERE format="rss"'
        cr.execute(sql)
        rs = cr.fetchall()

        for row in rs:
            feed_url = row[0]
            format = row[1]
            type = row[2]
            asset_class = row[3]
            market = row[4]
            lang = row[5]

            if type == str('global'):
                get_rss_global(feed_id,d,feed_url,asset_class,market,lang,limit)
            if type == str('specific'):
                get_rss_specific(feed_id,d,feed_url,lang,limit)
        cr.close()
    except Exception as e: print(e)

def get_rss_global(feed_id,date_d,feed_url,asset_class,market,lang,limit):
    try:
        feed = feedparser.parse(feed_url)
        insert_line = ''
        short_title = ''
        short_description = ''
        url = ''
        search = ''
        sep = ''
        insert_line = ''
        sentiment_score = 0
        i = 1
        for post in feed.entries:
            short_title = str(post.title).replace("'","`")
            try:
                short_description = str(post.description).replace("'","`") + ' '+ str(post.published)
            except:
                short_description = str(post.published)

            url = str(post.link)
            search = url
            sentiment_score = analyze_sentiment_of_this(short_title+' '+short_description)

            if i > 1: sep=','
            insert_line = insert_line + sep +\
            '(\''+ str(date_d)+'\',\''+str(short_title)+'\',\''+str(short_description)+'\',\''+\
            str(url)+'\',\''+str(feed_id)+'\',\''+str(search)+'\',\''+str(asset_class)+'\',\''+str(market)+'\',\''+str(lang)+'\','+ str(sentiment_score) +')'

            if i >= limit: break
            i += 1


        cr = connection.cursor(pymysql.cursors.SSCursor)
        sql = 'INSERT IGNORE INTO feed(date, short_title, short_description, '+\
        'url, type, search, asset_class, market, lang, ranking) VALUES '+ insert_line
        print(sql +": "+ os.path.basename(__file__) )
        try:
            cr.execute(sql)
            connection.commit()
        except: pass
        cr.close()

    except Exception as e: print(s)

def get_rss_specific(feed_id,date_d,feed_url,lang,limit):
    try:
        cr_s = connection.cursor(pymysql.cursors.SSCursor)
        sql_s = 'SELECT instruments.asset_class, instruments.market, '+\
        'symbol_list.symbol, symbol_list.yahoo_finance, symbol_list.seekingalpha, instruments.fullname '+\
        'FROM symbol_list JOIN instruments ON symbol_list.symbol = instruments.symbol '+\
        'WHERE symbol_list.disabled=0 AND symbol_list.seekingalpha<>"" OR symbol_list.yahoo_finance<>"" ORDER BY symbol'
        cr_s.execute(sql_s)
        rs = cr_s.fetchall()

        for row in rs:
            asset_class = row[0]
            market = row[1]
            symbol = row[2]
            yahoo_finance = row[3]
            seekingalpha = row[4]
            instrument_fullname = row[5].replace(' ','+').replace('.','').replace(',','')
            feed_url_selection = feed_url.replace('{seekingalpha}', seekingalpha)
            feed_url_selection = feed_url_selection.replace('{yahoo_finance}', yahoo_finance)
            feed_url_selection = feed_url_selection.replace('{instrument_fullname}', instrument_fullname)
            feed = feedparser.parse(feed_url_selection)
            print(feed_url_selection)

            insert_line = ''
            short_title = ''
            short_description = ''
            url = ''
            search = ''
            sep = ''
            insert_line = ''
            sentiment_score = 0
            i = 1
            for post in feed.entries:
                short_title = str(post.title).replace("'","`")
                try:
                    short_description = str(post.description).replace("'","`") + ' '+ str(post.published)
                except:
                    short_description = str(post.published)

                url = str(post.link)
                search = url
                sentiment_score = analyze_sentiment_of_this(short_title+' '+short_description)

                if i > 1: sep = ','
                insert_line = insert_line + sep +\
                '(\''+ str(date_d)+'\',\''+str(short_title)+'\',\''+str(short_description)+'\',\''+\
                str(url)+'\',\''+str(feed_id)+'\',\''+str(search)+'\',\''+str(asset_class)+'\',\''+str(market)+'\',\''+str(lang)+'\',\''+\
                str(symbol)+'\','+ str(sentiment_score) + ')'

                if i >= limit: break
                i += 1

            cr = connection.cursor(pymysql.cursors.SSCursor)
            sql = 'INSERT IGNORE INTO feed(date, short_title, short_description, '+\
            'url, type, search, asset_class, market, lang, symbol, ranking) VALUES '+ insert_line
            print(sql +": "+ os.path.basename(__file__) )
            try:
                cr.execute(sql)
                connection.commit()
            except: pass
            cr.close()
        cr_s.close()
    except Exception as e: print(e)

def count_news(dn,feed_id):
    try:
        symbol = ''
        vshortSymbol = ''
        vFullname = ''
        cr = connection.cursor(pymysql.cursors.SSCursor)
        sql = 'SELECT '+\
        'instruments.symbol, '+\
        '(SELECT SUBSTRING_INDEX(instruments.symbol,":",-1)) AS vshortSymbol, '+\
        'instruments.fullname '+\
        'FROM instruments '+\
        'WHERE instruments.symbol NOT LIKE "%'+ get_portf_suffix() +'%"'
        print(sql)
        cr.execute(sql)
        rs = cr.fetchall()
        news_count = 0
        for row in rs:
            symbol = row[0]
            vshortSymbol = row[1]
            fullname = row[2]

            cr_s = connection.cursor(pymysql.cursors.SSCursor)
            sql_s = 'SELECT COUNT(*) FROM feed '+\
            'WHERE type = '+ str(feed_id) + ' AND '+\
            '(short_title LIKE "%'+ str(fullname) +'%" OR '+\
            'short_description LIKE "%'+ str(fullname) +'%" OR symbol LIKE "%'+ str(symbol) +'%") AND '+\
            'date>='+ str(dn)
            print(sql_s)
            cr_s.execute(sql_s)
            rs_s = cr_s.fetchall()
            for row in rs_s:
                news_count = row[0]
            cr_s.close()

            cr_u = connection.cursor(pymysql.cursors.SSCursor)
            sql_u = 'UPDATE instruments SET news_count_1d = ' + str(news_count) + ' WHERE symbol = "'+ str(symbol) +'"'
            print(sql_u)
            cr_u.execute(sql_u)
            connection.commit()
            cr_u.close()
        cr.close()

    except Exception as e: print(e)

def clear_old_newsdata(dh,feed_id):
    try:
        cr = connection.cursor(pymysql.cursors.SSCursor)
        sql = 'DELETE FROM feed WHERE type='+ str(feed_id) + ' AND date < '+ str(dh)
        print(sql)
        cr.execute(sql)
        connection.commit()
        cr.close()
    except Exception as e: print(e)
