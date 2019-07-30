import rsa
from base64 import b64decode
import os
import uuid
from zb_api import  *
import threading
import base64

from multiprocessing import Process
import multiprocessing

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def buy_main_body(api,base1,base2,_coin,coin_place):

    market1 = _coin +"_"+ base1
    market2=base2+"_"+base1
    market3=_coin+"_"+base2
    action_ratio = 0.004

    obj1 = api.get_depth(market1)
    obj2 = api.get_depth(market2)
    obj3 = api.get_depth(market3)

    market1_ask = obj1["asks"][-3][0]
    market1_buy = obj1["bids"][2][0]

    market2_ask = obj2["asks"][-3][0]
    market2_buy = obj2["bids"][2][0]

    market3_ask = obj3["asks"][-3][0]
    market3_buy = obj3["bids"][2][0]

    min_money = 350
    amount = min_money/market1_ask
    '''
    money, coin, freez_money, freez_coin = api.get_available_balance(base1, base2)
    money_amount = money/market2_ask
    if (money_amount)/(money_amount+coin)>0.53:
        need_buy_amount = money_amount-(money_amount+coin)/2
        api.take_order(market2, "buy", market2_ask*1.05,need_buy_amount, coin_place)
    elif (coin)/(money_amount+coin)>0.53:
        need_sell_amount = coin-(money_amount+coin)/2
        api.take_order(market2, "sell", market2_buy*0.95, need_sell_amount, coin_place)

    '''

    need_wait = True
    while True:
        try:
            if need_wait:
                time.sleep(5)
            obj1 = api.get_depth(market1)
            obj2 = api.get_depth(market2)
            obj3 = api.get_depth(market3)

            real_ask = obj3["asks"][-3][0]
            real_buy = obj3["bids"][2][0]

            market1_ask = obj1["asks"][-3][0]
            market1_buy = obj1["bids"][2][0]

            market2_ask = obj2["asks"][-3][0]
            market2_buy = obj2["bids"][2][0]

            hecheng_ask =market1_ask/market2_buy
            hecheng_buy = market1_buy/market2_ask


            print("real_ask:",real_ask)
            print("hecheng_buy:",hecheng_buy)
            ratio1 = (hecheng_buy-real_ask)/real_ask
            print("Ratio1:",ratio1)


            print("real_buy:",real_buy)
            print("hecheng_ask:",hecheng_ask)
            ratio2 = (real_buy-hecheng_ask)/hecheng_ask
            print("Ratio2:",ratio2)
            next_round = False

            if ratio1>action_ratio:
                need_wait = False
                coin_amount = amount*1.1
                id=api.take_order(market3, "buy", real_ask,coin_amount, coin_place)
                if(id=="-1"):
                    pass
                else:
                    counter=0
                    while not api.is_order_complete(market3,id):
                        counter+=1
                        time.sleep(0.1)
                        if counter>40:
                            api.cancel_order(market3,id)
                            break
                money, coin, freez_money, freez_coin = api.get_available_balance(base1, _coin)
                coin_amount = coin
                api.take_order(market1, "sell", market1_buy, coin_amount, coin_place)

                api.take_order(market2, "buy", market2_ask, (market1_buy*coin_amount/market2_ask), coin_place)


            elif ratio2>action_ratio:
                need_wait = False
                coin_amount = amount*1.1
                id=api.take_order(market1, "buy", market1_ask, coin_amount, coin_place)
                if(id=="-1"):
                    pass
                else:
                    counter=0
                    while not api.is_order_complete(market1,id):
                        counter+=1
                        time.sleep(0.1)
                        if counter>40:
                            api.cancel_order(market1,id)
                            break
                money, coin, freez_money, freez_coin = api.get_available_balance(base1, _coin)
                coin_amount = coin
                api.take_order(market3, "sell", real_buy, coin_amount, coin_place)

                api.take_order(market2, "sell", market2_buy,(market1_ask * coin_amount/market2_buy), coin_place)
            else:
                need_wait=True

        except Exception as err:
            print("err")
            print(err)



def tick(load_access_key, load_access_secret, load_money, load_coin, load_parition, load_total_money, load_bidirection, load_coin_place):
    try:
        mutex2 = threading.Lock()
        access_key = load_access_key.strip()
        access_secret = load_access_secret.strip()
        _money =load_money.strip().upper()
        tmp =load_coin.strip().upper()
        if " "in tmp:
            coins =tmp.split(" ")
        else:
            coins = [tmp]
        markets = [_coin+_money for _coin in coins]
        print(markets)
        partition = int(load_parition.strip())
        assert(partition!=0)
        money_have = float(load_total_money.strip())

        market_exchange_dict = {"bbgcusdt":"renren","btmusdt":"jingxuanremenbi","zipusdt":"servicex","fiusdt":"fiofficial","dogeusdt":"tudamu","aeusdt":"servicex","zrxusdt":"tudamu","batusdt":"jiucai","linkusdt":"jingxuanremenbi","icxusdt":"allin","omgusdt":"ninthzone","zilusdt":"langchao"}

        bidirection=int(load_bidirection.strip())
        coin_place_list = [market_exchange_dict.get(item,"main") for item in markets]


        base1 = "QC"
        base2=_money

        api = zb_api(access_key, access_secret)
        market2 = base2 +"_"+ base1
        obj2 = api.get_depth(market2)
        market2_ask = obj2["asks"][-3][0]
        market2_buy = obj2["bids"][2][0]

        money, coin, freez_money, freez_coin = api.get_available_balance(base1, base2)
        money_amount = money / market2_ask
        if (money_amount) / (money_amount + coin) > 0.53:
            need_buy_amount = money_amount - (money_amount + coin) / 2
            api.take_order(market2, "buy", market2_ask * 1.05, need_buy_amount, coin_place)
        elif (coin) / (money_amount + coin) > 0.53:
            need_sell_amount = coin - (money_amount + coin) / 2
            api.take_order(market2, "sell", market2_buy * 0.95, need_sell_amount, coin_place)

        print("start cancel existing pending orders")
        for market in markets:
            time.sleep(0.1)
            api.cancel_all_pending_order(market)
        print("cancel pending orders completed")
        for i, market in enumerate(markets):
            time.sleep(1)
            thread = threading.Thread(target=buy_main_body,args=(api,base1,base2,coins[i],coin_place_list[i]))
            thread.setDaemon(True)
            thread.start()
        time.sleep(3600)
        print("tick exit!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    except Exception as ex:
        print(sys.stderr, 'tick: ', ex)
        #a= input()



def init_sell(apikey,apisecret,total_load_coin,load_money):
    access_key = apikey.strip()
    access_secret = apisecret.strip()
    _money =load_money.strip().upper()
    tmp =total_load_coin.strip().upper()
    if " "in tmp:
        coins =tmp.split(" ")
    else:
        coins = [tmp]
    markets = [_coin+"_"+_money for _coin in coins]
    print(markets)
    partition = int(load_parition.strip())
    assert(partition!=0)
    api = zb_api(access_key, access_secret)
    for market in markets:
        print("cancel"+market)
        api.cancel_all_pending_order(market)
        time.sleep(0.5)
    for _coin in coins:
        market=_coin+"_"+_money
        obj = api.get_depth(market)
        buy1 = obj["bids"][0][0]
        money, coin, freez_money, freez_coin = api.get_available_balance(_money, _coin)
        print(money,coin)
        api.take_order(market, "sell", buy1*0.99, coin, coin_place)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    print("begin")

    load_access_key, load_access_secret, load_money, load_coin, load_parition, load_total_money, load_bidirection, load_coin_place = None, None, None, None, None, None, None, None
    win1 = None
    license_day=0
    emerency = False

    mutex1 = threading.Lock()
    mutex3 = threading.Lock()
    mutex4 = threading.Lock()
    mutex5 = threading.Lock()

    access_key = None
    access_secret = None

    _money =None
    coins = None
    min_size = None
    money_have = None

    api = None
    partition=0
    bidirection=3
    coin_place = "main"
    total_amount_limit = 0
    yanzheng_file_name = "multi_coin_yanzheng.txt"
    gap = "multicoin"
    config_file = "multi_coinlastconfig.txt"
    multi_config_file = "multi_account_config.txt"

    need_exit = False
    coins = list()
    coin_place_list = list()
    markets = list()


    #load_money = "usdt"
    total_load_coin="xem eos eth ltc xrp B91 brc qtum etc topc ada dash bts"
    load_coin = "xem eos eth ltc xrp B91 brc qtum etc topc ada dash bts"
    load_parition="2"
    load_total_money="100"
    load_bidirection="3"
    load_coin_place="1"
    processes =list()
    '''
    with open(multi_config_file, "r") as f:
        local_thread=list()
        for line in f.readlines():
            apikey = line.split("#")[0]
            apisecret = line.split("#")[1]
            total_money = line.split("#")[2]
            thread = threading.Thread(target=init_sell,args=(apikey,apisecret,total_load_coin,load_money))
            thread.setDaemon(True)
            thread.start()
            local_thread.append(thread)
        for _th in local_thread:
            _th.join()
    '''
    while True:
        with open(multi_config_file, "r") as f:
            for line in f.readlines():
                apikey = line.split("#")[0]
                apisecret = line.split("#")[1]
                load_money = line.split("#")[2]
                total_money="1000"
                try:
                    init_sell(apikey,apisecret,total_load_coin,load_money)
                except:
                    pass
                p1 = Process(target=tick, args=(
                    apikey, apisecret, load_money, load_coin, load_parition, total_money,
                    load_bidirection, load_coin_place))
                p1.daemon = True
                p1.start()
                processes.append(p1)
        processes[0].join(timeout=3600)
        for p in processes:
            p.terminate()
        processes=[]

  #  period_restart()









