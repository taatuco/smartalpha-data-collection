# Copyright (c) 2018-present, Taatu Ltd.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import sys
import os
import datetime; import time; from datetime import timedelta
from sa_numeric import *

pdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(pdir) )
from settings import *
sett = sa_path()

sys.path.append(os.path.abspath( sett.get_path_pwd() ))
from sa_access import *
access_obj = sa_db_access()

sys.path.append(os.path.abspath( sett.get_path_core() ))
from ta_calc_ma import *

db_usr = access_obj.username(); db_pwd = access_obj.password(); db_name = access_obj.db_name(); db_srv = access_obj.db_server()

import pymysql.cursors
connection = pymysql.connect(host=db_srv,
                             user=db_usr,
                             password=db_pwd,
                             db=db_name,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


def get_trades(s,uid,dc):
    try:
        #start from date
        daycount = dc
        dfrom = datetime.datetime.now() - timedelta(days=daycount) ; dfrom_str = dfrom.strftime('%Y%m%d')

        trade_symbol = ''; trade_order_type = ''
        trade_entry_price = ''; trade_entry_date = dfrom
        trade_expiration_date = dfrom; trade_close_price = -1
        trade_pnl_pct = 0; trade_status = ''

        cr_1 = connection.cursor(pymysql.cursors.SSCursor)
        sql_1 = "SELECT symbol, date, price_close, target_price"+\
        "FROM price_instruments_data WHERE symbol = '"+ s +"' AND date >=" + dfrom_str + " ORDER BY date"
        cr_1.execute(sql_1)
        rs_1 = cr_1.fetchall()
        for row in rs_1:
            symbol_1 = row[0]
            date_1 = row[1]
            price_close_1 = row[2]
            target_price_1 = row[3]

            dto = dfrom + timedelta(days=7) ; dto_str = dto.strftime('%Y%m%d')
            cr_2 = connection.cursor(pymysql.cursors.SSCursor)
            sql_2 = "SELECT date, price_close FROM price_instruments_data WHERE symbol = '"+ s +"' AND date >=" + dto_str + " ORDER BY date "
            cr_2.execute(sql_2)
            rs_2 = cr_2.fetchall()
            date_2 = None; price_close_2 = -1
            for row in rs_2: date_2 = row[0]; price_close_2 = row[1]; break

            trade_symbol = s
            if price_close_1 <= target_price_1:
                trade_order_type = 'buy'
            else:
                trade_order_type = 'sell'
            trade_entry_price = price_close_1; trade_entry_date = date_1
            trade_expiration_date = date_2; trade_close_price = price_close_2
            if trade_order_type == 'buy':
                trade_pnl_pct = get_pct_change(price_close_1, price_close_2)
            else:
                trade_pnl_pct = get_pct_change(price_close_2, price_close_1)
            if price_close_2 == -1:
                trade_status = 'active'
            else:
                trade_status = 'expired'

            cr_i = connection.cursor(pymysql.cursors.SSCursor)
            sql_i = "INSERT INTO trades(symbol, order_type, entry_price, entry_date, expiration_date, close_price, pnl_pct, status) "+\
            "VALUES ('"+ trade_symbol +"','"+ trade_order_type +"',"+ str(trade_entry_price) +",'"+ str(trade_entry_date) +"','"+\
            str(trade_expiration_date) +"',"+ str(trade_close_price) +","+ str(trade_pnl_pct) +",'"+ str(trade_status) +"')"
            cr_i.execute(sql_i)
            connection.commit()


    except Exception as e: print(e)
