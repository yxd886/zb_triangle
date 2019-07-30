import json, hashlib, struct, time, sys
import urllib.request
import numpy as np
from datetime import datetime

class zb_api:
    def __init__(self, mykey, mysecret):
        self.mykey = mykey
        self.mysecret = mysecret
        self.jm = ''
        self.buy_order = list()
        self.sell_order = list()
        self.current_buy_order = None
        self.current_buy_order = None

    def __fill(self, value, lenght, fillByte):
        if len(value) >= lenght:
            return value
        else:
            fillSize = lenght - len(value)
        return value + chr(fillByte) * fillSize

    def __doXOr(self, s, value):
        slist = list(s.decode('utf-8'))
        for index in range(len(slist)):
            slist[index] = chr(ord(slist[index]) ^ value)
        return "".join(slist)

    def __hmacSign(self, aValue, aKey):
        keyb = struct.pack("%ds" % len(aKey), aKey.encode('utf-8'))
        value = struct.pack("%ds" % len(aValue), aValue.encode('utf-8'))
        k_ipad = self.__doXOr(keyb, 0x36)
        k_opad = self.__doXOr(keyb, 0x5c)
        k_ipad = self.__fill(k_ipad, 64, 54)
        k_opad = self.__fill(k_opad, 64, 92)
        m = hashlib.md5()
        m.update(k_ipad.encode('utf-8'))
        m.update(value)
        dg = m.digest()

        m = hashlib.md5()
        m.update(k_opad.encode('utf-8'))
        subStr = dg[0:16]
        m.update(subStr)
        dg = m.hexdigest()
        return dg

    def __digest(self, aValue):
        value = struct.pack("%ds" % len(aValue), aValue.encode('utf-8'))
        # print(value)
        h = hashlib.sha1()
        h.update(value)
        dg = h.hexdigest()
        return dg

    def __trade_api_call(self, path, params=''):
        try:
            SHA_secret = self.__digest(self.mysecret)
            sign = self.__hmacSign(params, SHA_secret)
            self.jm = sign
            reqTime = (int)(time.time() * 1000)
            params += '&sign=%s&reqTime=%d' % (sign, reqTime)
            url = 'https://trade.zb.com/api/' + path + '?' + params
            # print(url)
            req = urllib.request.Request(url)
            res = urllib.request.urlopen(req, timeout=2)
            doc = json.loads(res.read().decode('utf-8'))
            return doc
        except Exception as ex:
            print(sys.stderr, 'zb request ex: ', ex)
            return None

    def __data_api_call(self, path, params=''):

        reqTime = (int)(time.time() * 1000)
        url = 'http://api.zb.cn/data/v1/' + path + '?' + params
        print(url)
        req = urllib.request.Request(url)
        res = urllib.request.urlopen(req, timeout=2)
        txt = res.read().decode('utf-8')
        # print(txt)
        doc = json.loads(txt)
        return doc

    def query_account(self):

        params = "accesskey=" + self.mykey + "&method=getAccountInfo"
        path = 'getAccountInfo'

        obj = self.__trade_api_call(path, params)
        # print obj
        return obj

    def get_depth(self, market):
        # try:
        params = "market=" + market + "&size=20"
        path = 'depth'
        obj = self.__data_api_call(path, params)
        return obj
        #  except Exception as ex:
        #      print(sys.stderr, 'zb query_account exception,', ex)
        #      return None

    def take_order(self, market, direction, price, size,coin_place=None):
        print(direction)
        print(price)
        print(size)
        if direction == "buy":
            trade_direction = 1
        else:
            trade_direction = 0
        params = "accesskey=" + self.mykey + "&amount=" + str(
            size) + "&currency=" + market + "&method=order&price=" + str(price) + "&tradeType=" + str(trade_direction)
        path = 'order'

        obj = self.__trade_api_call(path, params)
        print(obj)
        id = obj.get("id", "-1")
        return id

    def get_order_info(self, market, id):
        params = "accesskey=" + self.mykey + "&currency=" + market + "&id=" + str(id) + "&method=getOrder"
        path = 'getOrder'

        obj = self.__trade_api_call(path, params)
        print(obj)
        return obj

    def is_order_complete(self, market, id):
        obj = self.get_order_info(market, id)
        if "message" in obj.keys():
            return True
        if obj["status"] == 2 or obj["status"]==1:
            return True
        else:
            return False

    def get_kline(self,market,type,since=None,size="1000"):
        if since==None:
            params = "market=" + market + "&type=" + type + "&size=" + size
        else:
            params = "market=" + market + "&type="+type+"&since="+since+"&size="+size
        path = 'kline'
        obj = self.__data_api_call(path, params)
        return obj



    def get_available_balance(self, money, coin):
        obj = self.query_account()
        coin_list = obj["result"]["coins"]
       # print(coin_list)
        for item in coin_list:
            if item["enName"] == money:
                res_money = float(item["available"])
                res_freez_money = float(item["freez"])
            elif item["enName"] == coin:
                res_coin = float(item["available"])
                res_freez_coin = float(item["freez"])
        return res_money,res_coin,res_freez_money,res_freez_coin

    def get_total_balance(self):
        obj = self.query_account()
        coin_list = obj["result"]["coins"]
        #print(coin_list)
        money =0
        for item in coin_list:
            coin = item["enName"]
            available = float(item["available"])
            frozen = float(item["freez"])
            #print("available:%f,frozen:%f"%(available,frozen))
            if available<0.001 and frozen<0.001:
                continue
            else:
                time.sleep(0.5)
                if coin=="QC"or coin=="qc":
                    buy1=1
                else:
                    buy1,_=self.get_buy1_and_sell_one(coin+"_qc")
                money+=(available+frozen)*buy1

        return money

        return res_money, res_coin, res_freez_money, res_freez_coin

    def get_buy1_and_sell_one(self, market):
       # print(market)
        obj = self.get_depth(market)
        #print(obj)
        if obj.get("error",None)=="市场错误":
            return 0,0
        buy1 = obj["bids"][0][0]
        sell1 = obj["asks"][-1][0]
        return buy1, sell1


    def get_buy1_and_sell_one_and_depth(self, market):
       # print(market)
        obj = self.get_depth(market)
        #print(obj)
        if obj.get("error",None)=="市场错误":
            return 0,0
        buy1 = obj["bids"][0][0]
        sell1 = obj["asks"][-1][0]
        depth_buy1 = obj["bids"][0][1]

        depth_sell1 = obj["asks"][-1][1]
        return buy1, sell1,depth_buy1,depth_sell1


    def get_pending_orders1(self, market):
        params = "accesskey=" + self.mykey + "&currency=" + market + "&method=getUnfinishedOrdersIgnoreTradeType&pageIndex=1&pageSize=10"
        path = 'getUnfinishedOrdersIgnoreTradeType'
        obj = self.__trade_api_call(path, params)
        # print(obj)
        return obj

    def get_pending_orders(self, market):

        obj=list()
        ids = list()

        for i in range(2,100):
            buy_obj = self.get_orders(market,"buy",i)
            sell_obj = self.get_orders(market,"sell",i)
            if isinstance(buy_obj,dict) and isinstance(sell_obj,dict):
                break

            if not isinstance(buy_obj,dict):
                for item in buy_obj:
                    if int(item["status"])==0 or int(item["status"])==3:
                        if item["id"] not in ids:
                            obj.append(item)
                            ids.append(item["id"])
            if not isinstance(sell_obj,dict):
                for item in sell_obj:
                    if int(item["status"])==0 or int(item["status"])==3:
                        if item["id"] not in ids:
                            obj.append(item)
                            ids.append(item["id"])


        return obj

    def get_orders(self, market,direction,index):
        if direction=="buy":
            trade_type=1
        elif direction=="sell":
            trade_type=0
        params = "accesskey=" + self.mykey + "&currency=" + market + "&method=getOrdersNew&pageIndex="+str(index)+"&pageSize=100&tradeType="+str(trade_type)
        path = 'getOrdersNew'
        obj = self.__trade_api_call(path, params)
        print(obj)
        return obj

    def cancel_order(self, market, id):
        params = "accesskey=" + self.mykey + "&currency=" + market + "&id=" + str(id) + "&method=cancelOrder"
        path = 'cancelOrder'
        obj = self.__trade_api_call(path, params)
        return obj

    '''
    def balance_account(self,money,coin):
        buy,ask = api.get_buy1_and_sell_one(market)
        avail_money,avail_coin,freez_money,freez_coin = api.get_available_balance(money,coin)
        ratio = (avail_money+freez_money)/(avail_money+freez_money+(avail_coin+freez_coin)*buy)
        print("ratio:%f" % ratio)
        while(ratio>0.52 or ratio<0.48):
            buy, ask = api.get_buy1_and_sell_one(market)
            avail_money,avail_coin,freez_money,freez_coin = api.get_available_balance(money, coin)
            ratio = (avail_money+freez_money)/(avail_money+freez_money+(avail_coin+freez_coin)*buy)
            print("ratio:%f" % ratio)
            if ratio<0.48:
                sell_order_id = api.take_order(market, "sell", buy, size=1)
                time.sleep(2)
                if not api.is_order_complete(market,sell_order_id):
                    api.cancel_order(market,sell_order_id)
            elif ratio>0.52:
                buy_order_id = api.take_order(market, "buy", ask, size=1)
                time.sleep(2)
                if not api.is_order_complete(market,buy_order_id):
                    api.cancel_order(market,buy_order_id)

    '''

    def balance_account(self, money, coin,market):
        buy, ask = self.get_buy1_and_sell_one(market)
        avail_money, avail_coin, freez_money, freez_coin = self.get_available_balance(money, coin)
        ratio = (avail_money + freez_money) / (avail_money + freez_money + (avail_coin + freez_coin) * buy)
        print("ratio:%f" % ratio)
        if ratio < 0.48:
            sell_size = ((avail_money + avail_coin * buy) * 0.5 - avail_money) / ask
            self.take_order(market, "sell", ask, size=sell_size)
        elif ratio > 0.52:
            buy_size = (avail_money - (avail_money + avail_coin * buy) * 0.5) / buy
            self.take_order(market, "buy", buy, size=buy_size)

        while True:
            time.sleep(2.001)
            obj = self.get_pending_orders1(market)
            print(obj)
            if isinstance(obj, dict):
                break

    def wait_pending_order(self, market):
        while True:
            time.sleep(2.001)
            obj = self.get_pending_orders1(market)
            print(obj)
            if isinstance(obj, dict):
                break

    def check_and_aggregate_orders(self,market):
        while True:
            time.sleep(1)
            obj = self.get_pending_orders1(market)
            if isinstance(obj, dict):
                return
            buy_orders=list()
            buy_money = 0
            buy_amount=0
            sell_money = 0
            sell_amount=0
            sell_orders=list()
            for item in obj:
                if int(item["type"])==1:
                    buy_orders.append(item)
                elif int(item["type"])==0:
                    sell_orders.append(item)

            print("buy_order_num:%d"%len(buy_orders))
            print("sell_order_num:%d" % len(sell_orders))

            if len(sell_orders)<5 and len(buy_orders)<5:
                return


            if len(buy_orders)>1:
                for i,item in enumerate(buy_orders):
                    amount = item["total_amount"]-item["trade_amount"]
                    price = item["price"]
                    buy_money+=amount*price
                    buy_amount+=amount
                    self.cancel_order(market,item["id"])
                    time.sleep(0.5)

                new_buy_price = buy_money/buy_amount
                print(self.take_order(market,"buy",new_buy_price,buy_amount))
            if len(sell_orders) > 1:
                for i,item in enumerate(sell_orders):
                    amount = item["total_amount"]-item["trade_amount"]
                    price = item["price"]
                    sell_money+=amount*price
                    sell_amount+=amount
                    self.cancel_order(market,item["id"])
                    time.sleep(0.5)

                new_sell_price = sell_money/sell_amount
                print(self.take_order(market,"sell",new_sell_price,sell_amount))


    def cancel_all_pending_order(self,market):
        while True:
            time.sleep(1)
            obj = self.get_pending_orders1(market)
            if isinstance(obj, dict):
                return
            for item in obj:
                self.cancel_order(market,item["id"])



    def enqueue_sell_order(self, price, size):
        self.sell_order.append((price, size))
        self.sell_order.sort(key=lambda a: a[0], reverse=False)
        self.current_sell_order = (price, size)

    def enqueue_buy_order(self, price, size):
        self.buy_order.append((price, size))
        self.buy_order.sort(key=lambda a: a[0], reverse=True)
        self.current_buy_order = (price, size)

    def dequeue_current_sell_order(self):
        if self.current_sell_order and self.current_sell_order in self.sell_order:
            self.sell_order.remove(self.current_sell_order)
            self.current_sell_order = None

    def dequeue_current_buy_order(self):
        if self.current_buy_order and self.current_buy_order in self.buy_order:
            self.buy_order.remove(self.current_buy_order)
            self.current_buy_order = None

    def handle_order_in_queue(self, market):
        print("handling sell_orders and buy orders in queue")
        import copy
        new_sell_order = copy.deepcopy(self.sell_order)
        new_buy_order = copy.deepcopy(self.buy_order)
        for i, item in enumerate(self.sell_order):
            time.sleep(1)
            money, coin, freez_money, freez_coin = self.get_available_balance("QC", "USDT")
            price = item[0]
            size = item[1]
            if coin >= size:
                self.take_order(market=market, direction="sell", price=price, size=size)
                new_sell_order.remove(item)
            else:
                break

        for i, item in enumerate(self.buy_order):
            time.sleep(1)
            money, coin, freez_money, freez_coin = self.get_available_balance("QC", "USDT")
            price = item[0]
            size = item[1]
            if money >= price * size:
                self.take_order(market=market, direction="buy", price=price, size=size)
                new_buy_order.remove(item)
            else:
                break
        self.sell_order = new_sell_order
        self.buy_order = new_buy_order

    def create_cells(self, upper_price, lower_price, middle_price, total_coin, cell_num):
        price_per_cell = (upper_price - lower_price) / cell_num
        upper_half_cell_num = int((upper_price - middle_price) / price_per_cell)
        lower_half_cell_num = cell_num - upper_half_cell_num
        money_for_each_area = total_coin / 2
        base = 0
        d_for_upper_area = 2 * (money_for_each_area - base) / (upper_half_cell_num * (upper_half_cell_num - 1))
        base = money_for_each_area + (upper_half_cell_num) * d_for_upper_area
        d_for_lower_area = 2 * (total_coin - base) / (lower_half_cell_num * (lower_half_cell_num - 1))
        self.cell_money = list()
        self.cell_step = list()
        base = 0
        for i in range(upper_half_cell_num):
            if i == 0:
                self.cell_money.append(base)
            else:
                self.cell_money.append(self.cell_money[-1] + d_for_upper_area * (i + 1))
            self.cell_step.append(d_for_upper_area * (i + 1))
        base = money_for_each_area + (upper_half_cell_num) * d_for_upper_area
        for i in range(lower_half_cell_num):
            if i == 0:
                self.cell_money.append(base)
            else:
                self.cell_money.append(self.cell_money[-1] + d_for_lower_area * (lower_half_cell_num - i))
            self.cell_step.append(d_for_lower_area * (lower_half_cell_num - i))

        print(self.cell_step)
        print(self.cell_money)

    def compute_current_num_of_coin_should_have(self, upper_price, lower_price, cell_num, current_price):
        if current_price <= lower_price:
            return self.cell_money[-1]
        if current_price >= upper_price:
            return 0
        index = int(((upper_price - current_price) / (upper_price - lower_price)) * cell_num)
        # print("current_price:%f" % current_price)
        # print("index:%d" % index)
        # print("coin_should_have:%f" % self.cell_money[index])
        return self.cell_money[index]

    def compute_current_num_coin_step(self, upper_price, lower_price, cell_num, current_price):
        if current_price <= lower_price:
            return 0
        if current_price >= upper_price:
            return 0
        index = int(((upper_price - current_price) / (upper_price - lower_price)) * cell_num)
        # print("current_price:%f" % current_price)
        # print("index:%d" % index)
        # print("coin_should_have:%f" % self.cell_money[index])
        return self.cell_step[index]


if __name__ == '__main__':
    access_key = '8892c7da-2c95-41e7-b303-5703d011af9e'
    access_secret = 'ac058da7-7f18-4b8a-b86f-0cc3d9a8a752'
    market="USDT_QC"
    api = zb_api(access_key, access_secret)


    time_list = list()
    profit_list = list()
    while True:
        time.sleep(2)
        time_now = int(time.time())
        time_local = time.localtime(time_now)

        dt = (time.strftime("%m/%d-%H:%M:%S", time_local))
        Total_balance=api.get_total_balance()
        print(dt)
        time_list.append(dt)
        profit_list.append(Total_balance)
        print(time_list)
        plt.gca().get_yaxis().get_major_formatter().set_useOffset(False)
        plt.plot(time_list,profit_list)
        plt.gcf().autofmt_xdate()  # 自动旋转日期标记
        plt.savefig("fig.png")
