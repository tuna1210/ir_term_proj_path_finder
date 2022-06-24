from selenium import webdriver 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import time
import pandas as pd
import warnings
import requests, json

RESTAPIKEY=''

def geocoding(address):
  url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + address
  headers = {"Authorization": f"KakaoAK {RESTAPIKEY}"}
  api_json = json.loads(str(requests.get(url,headers=headers).text))
  address = api_json['documents'][0]['address']
  lat, lon = str(address['y']), str(address['x'])

  return lat, lon

warnings.filterwarnings('ignore')

keyword = input()
query = f'전북대 {keyword}'
path = chromedriver_autoinstaller.install()
driver = webdriver.Chrome(path)
driver.get(f"https://map.naver.com/v5/search/{query}")

driver.switch_to.frame("searchIframe")
time.sleep(2)

title_list = []
score_list = []
visitor_list = []
blog_list = []
address_list = []
alt_list = []
lon_list = []

try: 
    for i in range(1,5): 
        time.sleep(2)
        driver.find_element_by_link_text(str(i)).click()
        try: 
            for j in range(3,70,3):
                element = driver.find_elements(By.CSS_SELECTOR, '._3Apve')[j]
                ActionChains(driver).move_to_element(element).key_down(Keys.PAGE_DOWN).key_up(Keys.PAGE_DOWN).perform()
        except: 
            pass

        link_boxes = driver.find_elements(By.CSS_SELECTOR, '._3ZU00._1rBq3')
    
        for box in link_boxes:
            link = box.find_elements(By.CSS_SELECTOR, '._3LMxZ')[0]

            link.click()
            driver.switch_to.default_content()
            time.sleep(2)        
            frame_in = driver.find_element(By.XPATH, '/html/body/app/layout/div[3]/div[2]/shrinkable-layout/div/app-base/search-layout/div[2]/entry-layout/entry-place-bridge/div/nm-external-frame-bridge/nm-iframe/iframe')
            driver.switch_to.frame(frame_in) 
            time.sleep(1)

            title = driver.find_element(By.CSS_SELECTOR, '._3XamX').text

            s = 1
            try:
                scorep = driver.find_element(By.CSS_SELECTOR, '._1Y6hi._1A8_M')
                score = scorep.find_element(By.TAG_NAME, 'em').text
            except:
                score = 'None'
                s = 0

            try:
                parents = driver.find_elements(By.CSS_SELECTOR, '._1Y6hi')
                try:
                    visitor = parents[s].find_element(By.TAG_NAME, 'em').text
                except:
                    visitor = 'None'
                try:
                    blog = parents[s+1].find_element(By.TAG_NAME, 'em').text
                except:
                    blog = 'None'
            except:
                visitor = 'None'
                blog = 'None'

            try:
                address = driver.find_element(By.CSS_SELECTOR, '._2yqUQ').text
                try:
                    alt, lon = geocoding(address)
                except:
                    alt, lon = 'None', 'None'
            except:
                address = 'None'
            
            print(f'{title}, {score}, {visitor}, {blog}, {address}, {alt}, {lon}')

            title_list.append(title)
            score_list.append(score)
            visitor_list.append(visitor)
            blog_list.append(blog)
            address_list.append(address)
            alt_list.append(alt)
            lon_list.append(lon)

            driver.switch_to.default_content()
            driver.switch_to.frame("searchIframe")
    
except:
    print('Error')
    pass

print(len(title_list),len(score_list),len(visitor_list),len(blog_list),len(address_list)
,len(alt_list),len(lon_list))

## 데이터 프레임 만들기
df = pd.DataFrame(
    {
        'title':title_list,
        'score':score_list,
        'visitor': visitor_list,
        'blog':blog_list,
        'address':address_list,
        'alt':alt_list,
        'lon':lon_list
    }
)

df.to_csv(f"naver({query.replace(' ', '_')}).csv".format(query), encoding='utf-8-sig')