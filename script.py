import webbrowser
from bs4 import BeautifulSoup, NavigableString, Tag
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import  os
import pandas as pd
import json
import bs4
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib3 import request
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.select import Select
import datetime
import plotly.graph_objects as go

################ JUST MAKE CHANGES HERE ########################
startDate = '2021/06/07'  # <- FORMAT (YYYY/MM/DD)
endDate = '2021/06/09'
symbol = 'VTI'
################################################################

############### RESULTING FILE FORMAT ###########################

#           '<SYMBOL>_<DD>_<MM>_<YYYY>.CSV'

#################################################################

cols = ['Date (DD/MM/YYYY)','Broker','Buy Value ($)','Sell Value ($)','Net Value ($)','Total Value ($)','Buy Volume','Sell Volume','Net Volume','Total Volume','Buy Trade Count','Sell Trade Count','Total Trade Count','Buy Price','Sell Price','Rank']
graph1_df = pd.DataFrame(columns=cols)
graph2_df = pd.DataFrame(columns=cols)

def workdays(d, end, excluded=(6, 7)):
    days = []
    while d.date() <= end.date():
        if d.isoweekday() not in excluded:
            days.append(d.strftime('%Y/%m/%d'))
        d += datetime.timedelta(days=1)
    return days

def main():

    global startDate
    global endDate
    global symbol
    global graph1_df
    global graph2_df

    cols = ['Date (DD/MM/YYYY)','Broker','Buy Value ($)','Sell Value ($)','Net Value ($)','Total Value ($)','Buy Volume','Sell Volume','Net Volume','Total Volume','Buy Trade Count','Sell Trade Count','Total Trade Count','Buy Price','Sell Price','Rank']
    

    prefs = {"profile.default_content_setting_values.notifications" : 2}  #block notifications
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs",prefs)
    chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--headless")     
    #chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    #chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)

    driver.get("https://scanner.daytradescans.com/signin")
    driver.implicitly_wait(20)
    driver.maximize_window()

    user_name='//*[@id="user_email"]'
    password='//*[@id="user_password"]'
    submit_button='//*[@id="new_user"]/div[2]/div/input'
    fundamentals='//*[@id="navbarDropdown"]'
    broker_data = '//*[@id="navbarSupportedContent"]/ul/li[1]/div/a[2]'
    capture = '//*[@id="capture-broker-data"]/span'
    dl = '//*[@id="canvas-link"]'

    #on_login_page
    driver.find_element_by_xpath(user_name).send_keys('ivan.cortez.paulo@gmail.com')  #login_id
    driver.find_element_by_xpath(password).send_keys("qwertyuiop2021")    #password
    driver.find_element_by_xpath(submit_button).click()
    driver.implicitly_wait(30)

    print("logged in")

    driver.find_element_by_xpath(fundamentals).click()
    driver.find_element_by_xpath(broker_data).click()

    print("in broker data")
    

    startDate = datetime.datetime.strptime(startDate, "%Y/%m/%d")
    endDate = datetime.datetime.strptime(endDate, "%Y/%m/%d")
    
    # driver.find_element_by_xpath(text_box).send_keys(input_for_search)
    # driver.find_element_by_xpath(from_date).send_keys(from_date_in)
    # driver.find_element_by_xpath(to_date).send_keys(to_date_in)
    # driver.find_element_by_xpath(search_button).click()

    import time
    
    dates = workdays(startDate,endDate)

    filedate1 = datetime.datetime.strptime(dates[0],'%Y/%m/%d').strftime('%d/%m/%Y').replace('/','_')
    filedate2 = datetime.datetime.strptime(dates[-1],'%Y/%m/%d').strftime('%d/%m/%Y').replace('/','_')

    for date in dates:

        new_url = f'https://scanner.daytradescans.com/brokers?code_autocomplete_label={symbol}&code=&name_autocomplete_label=&name=&from={date}&to={date}&commit=Search&minimum_share_price=&maximum_share_price=&minimum_market_cap=&maximum_market_cap=&minimum_eps=&maximum_eps=&minimum_soi=&maximum_soi='
        driver.get(new_url)
        driver.implicitly_wait(10)

        driver.find_element_by_xpath(capture).click()
        driver.find_element_by_xpath(dl).click()
        
        driver.back()
        html=driver.page_source
        soup = BeautifulSoup(html,features="lxml")
        soup_data = soup.get_text()
        a = json.loads(soup_data)

        if bool(a):
            df = pd.DataFrame(a)
            df.drop(['id'],axis=1, inplace = True)
            # import pdb; pdb.set_trace()
            df['buy_volume'] = df['buy_volume'].map(float)
            df['sell_volume'] = df['sell_volume'].map(float)

            df['total_volume'] = abs(df['buy_volume']) + abs(df['sell_volume'])
            tsum = df.tail(1)['total_volume']
            df['Rank'] = df['total_volume']
            df.Rank = df.Rank.div(float(tsum)) * 100
            df.Rank = df.Rank.round(2)

            td = datetime.datetime.strptime(date,'%Y/%m/%d').strftime('%d/%m/%Y')
            df.rename(columns={'name':'Broker','buy_value':'Buy Value ($)','sell_value':'Sell Value ($)','net_value':'Net Value ($)','total_value':'Total Value ($)','buy_volume':'Buy Volume','sell_volume':'Sell Volume','net_volume':'Net Volume','total_volume':'Total Volume','buy_trade_count':'Buy Trade Count','sell_trade_count':'Sell Trade Count','total_trade_count':'Total Trade Count','buy_price':'Buy Price','sell_price':'Sell Price'},inplace=True)
            df['Date (DD/MM/YYYY)'] = td

            df = df[cols]

            file_name = f'{symbol}_{filedate1}_to_{filedate2}.csv'
            if not(os.path.exists(file_name) and os.path.getsize(file_name) > 0):
                df.to_csv(file_name, mode = 'a',index=False)
            else:
                df.to_csv(file_name, mode = 'a', header = False, index=False)
#             import pdb; pdb.set_trace()
            graph1_df = graph1_df.append(df.tail(1))
        
    time.sleep(10)
    driver.close()

def graph1_plotting():
    global graph1_df

    fig = go.Figure(data=[go.Candlestick(x=graph1_df['Date (DD/MM/YYYY)'], open=graph1_df['Sell Price'], high=graph1_df['Sell Price'], low=graph1_df['Buy Price'], close=graph1_df['Buy Price'])])
    fig.add_trace(go.Bar(x=graph1_df['Date (DD/MM/YYYY)'], y=graph1_df['total_volume']),secondary_y=False)

    fig.layout.yaxis2.showgrid=False
    fig.show()

if __name__=="__main__":
    main()
    graph1_plotting()