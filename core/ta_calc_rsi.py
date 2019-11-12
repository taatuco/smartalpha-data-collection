""" Functionalities related to relative strength index """
# Copyright (c) 2018-present, Taatu Ltd.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import sys
import os
PDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(PDIR))
from settings import SmartAlphaPath
SETT = SmartAlphaPath()
sys.path.append(os.path.abspath(SETT.get_path_pwd()))
from sa_access import sa_db_access
ACCESS_OBJ = sa_db_access()
DB_USR = ACCESS_OBJ.username()
DB_PWD = ACCESS_OBJ.password()
DB_NAME = ACCESS_OBJ.db_name()
DB_SRV = ACCESS_OBJ.db_server()

# Notes:
#
# Retrieve data in this order is recomended.
#
# rsi = rsi_data()
# change_1d = rsi.get_change()
# gain_1d = rsi.get_gain()
# loss_1d = rsi.get_loss()
# avg_gain = rsi.get_avg_gain()
# avg_loss = rsi.get_avg_loss()
# rs = rsi.get_rs()
# rsi = rsi.get_rsi()
# ...
#

class rsi_data:
    """
    Get and compute relative strength index
    Args:
        String: Instrument symbol
        String: Date in string format YYYYMMDD
        Integer: RSI period
    """
    import pymysql.cursors
    c_curr_gain = 0
    c_curr_loss = 0
    c_prev_price_close = 0
    c_curr_price_close = 0
    c_change_1d = 0
    c_prev_avg_gain = 0
    c_prev_avg_loss = 0
    c_curr_avg_gain = 0
    c_curr_avg_loss = 0
    c_prev_is_ta_calc = 0
    c_curr_is_ta_calc = 0
    c_rs = 0
    c_rsi = 0

    def __init__(self, symbol, date, period):
        """ Initialize RSI data """
        self.symbol = symbol
        self.date = date
        self.period = period

        connection = rsi_data.pymysql.connect(host=DB_SRV,
                                              user=DB_USR,
                                              password=DB_PWD,
                                              db=DB_NAME,
                                              charset='utf8mb4',
                                              cursorclass=rsi_data.pymysql.cursors.DictCursor)
        cr_get_pr_d = connection.cursor(rsi_data.pymysql.cursors.SSCursor)
        sql_get_pr_d = "SELECT price_close, avg_gain, avg_loss, is_ta_calc "+\
        "FROM price_instruments_data "+\
                             "WHERE symbol='"+self.symbol+"' AND date<"+str(self.date)+" "+\
                             "ORDER BY date DESC LIMIT 1"
        cr_get_pr_d.execute(sql_get_pr_d)
        rs_prev = cr_get_pr_d.fetchall()
        if rs_prev:
            for row in rs_prev:
                rsi_data.c_prev_price_close = row[0]
                rsi_data.c_prev_avg_gain = row[1]
                rsi_data.c_prev_avg_loss = row[2]
                rsi_data.c_prev_is_ta_calc = row[3]

            cr_get_curr_d = connection.cursor(rsi_data.pymysql.cursors.SSCursor)
            sql_get_curr_d = "SELECT price_close, avg_gain, avg_loss, is_ta_calc "+\
            "FROM price_instruments_data "+\
                                 "WHERE symbol='"+self.symbol+"' AND date="+str(self.date)+" "+\
                                 "ORDER BY date DESC LIMIT 1"
            cr_get_curr_d.execute(sql_get_curr_d)
            rs_curr = cr_get_curr_d.fetchall()
            if rs_curr:
                for row in rs_curr:
                    rsi_data.c_curr_price_close = row[0]
                    rsi_data.c_curr_avg_gain = row[1]
                    rsi_data.c_curr_avg_loss = row[2]
                    rsi_data.c_curr_is_ta_calc = row[3]
            cr_get_curr_d.close()
        cr_get_pr_d.close()
        connection.close()


    def get_gain(self):
        """ Get 1 day gain """
        gain_1d = 0
        if rsi_data.c_change_1d >= 0:
            gain_1d = rsi_data.c_change_1d
        rsi_data.c_curr_gain = gain_1d
        return gain_1d

    def get_avg_gain(self):
        """ Get period average gain """
        #(FIRST_AVG, GAIN, LOSS) = AVERAGE( (GAIN) ), AVERAGE( (LOSS) ) (if count> period)
        # In case previous is 0 then get average of last period
        tt_gain = 0
        if rsi_data.c_prev_avg_gain == 0:
            #with rsi_data.connection.cursor() as cr_get_avg_g:

            connection = rsi_data.pymysql.connect(host=DB_SRV,
                                                  user=DB_USR,
                                                  password=DB_PWD,
                                                  db=DB_NAME,
                                                  charset='utf8mb4',
                                                  cursorclass=rsi_data.pymysql.cursors.DictCursor)
            cr_get_avg_g = connection.cursor(rsi_data.pymysql.cursors.SSCursor)
            sql_get_avg_g = "SELECT gain_1d FROM price_instruments_data "+\
                          "WHERE symbol='"+self.symbol+"' AND date<"+\
                          str(self.date)+" AND is_ta_calc=1 "+\
                          "LIMIT "+str(self.period)
            cr_get_avg_g.execute(sql_get_avg_g)
            rs_avg_g = cr_get_avg_g.fetchall()
            for row in rs_avg_g:
                tt_gain = tt_gain + row[0]
            rsi_data.c_curr_avg_gain = tt_gain / self.period
            cr_get_avg_g.close()
            connection.close()
        else:
            #(AVG_GAIN) = ( (PREVIOUS_AVG_GAIN)*(period-1)+ (GAIN) ) / period
            rsi_data.c_curr_avg_gain = ((rsi_data.c_prev_avg_gain*(self.period-1))+
                                        rsi_data.c_curr_gain)
            rsi_data.c_curr_avg_gain = rsi_data.c_curr_avg_gain/self.period
        return rsi_data.c_curr_avg_gain

    def get_avg_loss(self):
        """ Get period average loss """
        #(AVG_LOSS) = ( (PREVIOUS_AVG_LOSS)*(period-1)+ (LOSS) ) / period
        tt_loss = 0
        if rsi_data.c_prev_avg_loss == 0:
            #with rsi_data.connection.cursor() as cr_get_avg_l:

            connection = rsi_data.pymysql.connect(host=DB_SRV,
                                                  user=DB_USR,
                                                  password=DB_PWD,
                                                  db=DB_NAME,
                                                  charset='utf8mb4',
                                                  cursorclass=rsi_data.pymysql.cursors.DictCursor)
            cr_get_avg_l = connection.cursor(rsi_data.pymysql.cursors.SSCursor)
            sql_get_avg_l = "SELECT loss_1d FROM price_instruments_data "+\
                          "WHERE symbol='"+self.symbol+"' AND date<"+str(self.date)+\
                          " AND is_ta_calc=1 "+\
                          "LIMIT "+str(self.period)
            cr_get_avg_l.execute(sql_get_avg_l)
            rs_avg_l = cr_get_avg_l.fetchall()
            for row in rs_avg_l:
                tt_loss = tt_loss + row[0]
            rsi_data.c_curr_avg_loss = tt_loss / self.period
            cr_get_avg_l.close()
            connection.close()
        else:
            #(AVG_LOSS) = ( (PREVIOUS_AVG_LOSS)*(period-1)+ (LOSS) ) / period
            rsi_data.c_curr_avg_loss = ((rsi_data.c_prev_avg_loss*(self.period-1))+
                                        rsi_data.c_curr_loss)
            rsi_data.c_curr_avg_loss = rsi_data.c_curr_avg_loss/self.period
        return rsi_data.c_curr_avg_loss


    def get_loss(self):
        """ Get 1 day loss """
        loss_1d = 0
        if rsi_data.c_change_1d < 0:
            loss_1d = (rsi_data.c_change_1d)*(-1)
        rsi_data.c_curr_loss = loss_1d
        return loss_1d

    def get_change(self):
        """ Get 1 day change """
        rsi_data.c_change_1d = rsi_data.c_curr_price_close - rsi_data.c_prev_price_close
        return rsi_data.c_change_1d

    def get_rs(self):
        """ Get the relative strength """
        #(RS) = (AVG_GAIN) / (AVG_LOSS)
        if rsi_data.c_curr_avg_loss != 0:
            rsi_data.c_rs = rsi_data.c_curr_avg_gain / rsi_data.c_curr_avg_loss
        return rsi_data.c_rs

    def get_rsi(self):
        """ Get the relative strength index """
        #(RSI) = if( (RS)=0, 100, 100-(100/1+(RS)) )
        if rsi_data.c_curr_avg_gain != 0:
            if rsi_data.c_rs == 0:
                rsi_data.c_rsi = 100
            else:
                rsi_data.c_rsi = 100-(100/(1+ rsi_data.c_rs))
        return rsi_data.c_rsi

    def get_rsi_overbought(self):
        """ Get the overbought upper level """
        return 70

    def get_rsi_oversold(self):
        """ Get the oversold lower level """
        return 30
