
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager       
import sys
sys.path.append('/apps/fastapis')
import os
import asyncio
import time
from konlpy.tag import Okt
import pickle
from datetime import datetime,timedelta

from database.connection import Settings
from models.news_weekly import news_weekly
from models.news_weekly_thevoice import news_weekly_thevoice

# # 몽고 디비 연결
# def dbconnect(collection) :
#     mongoClient = MongoClient("mongodb://trainings.iptime.org:45003/")
#     database = mongoClient["teamkim"]
#     collection = database[collection]
#     return collection

# 날짜 바꾸기
def convert_to_datetime(orgin_str):
    current_datetime = datetime.now()
    news_datetime = datetime.strptime(orgin_str, "%m.%d %H:%M")
    current_year = current_datetime.year
    news_datetime = news_datetime.replace(year=current_year)
    return news_datetime

# 뉴스 스크래핑

# def bosascrapping(browser_name, keyword) :

#     bosa_news_coll = collection_news_weekly
#     # bosa_news_coll.delete_many({})

#     chrome_options = Options()
#     # chrome_options.add_argument("--headless")  # Ensure GUI is off
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")

#     # 현재 날짜 설정
#     from datetime import datetime, timedelta
#     current_datetime = datetime.now()
#     current_date = current_datetime.date()
#     one_week_date = current_date - timedelta(days=10)
#     current_date = current_date.strftime('%Y-%m-%d')
#     one_week_date = one_week_date.strftime('%Y-%m-%d')

#     ## 상세검색
#     browser = webdriver.Chrome(options=chrome_options)
#     browser.get(browser_name)
#     browser.find_element(By.CSS_SELECTOR, "div.user-etc > div.search-list > span > a").click() # 상세 검색
#     time.sleep(1)
#     new_tab = browser.window_handles[-1]
#     browser.switch_to.window(new_tab)

#     browser.find_element(By.CSS_SELECTOR, "#sc_sdate").clear()
#     browser.find_element(By.CSS_SELECTOR, "#sc_sdate").send_keys(one_week_date)
#     browser.find_element(By.CSS_SELECTOR, "#sc_edate").clear()
#     browser.find_element(By.CSS_SELECTOR, "#sc_edate").send_keys(current_date)
#     browser.find_element(By.CSS_SELECTOR, "#sc_word").send_keys(keyword)
#     browser.find_element(By.CSS_SELECTOR, "#search-tabs1 > form > footer > div > button").click()
#     browser.find_element(By.CSS_SELECTOR, "header > div > div > a:nth-child(2)").click() # 요약형
#     time.sleep(2)
#     ## 스크래핑
#     contents = browser.find_elements(By.CSS_SELECTOR, "#section-list > ul > li")
#     for index in range(len(contents)) :
#         contents = browser.find_elements(By.CSS_SELECTOR, "#section-list > ul > li")
#         try : 
#             try :
#                 news_title = contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li > h4 > a").text
#                 news_url = contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li> h4 > a").get_attribute("href")
#                 news_when_orgin = contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li > span > em:nth-child(3)").text
#             except :
#                 news_title = contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li > div > h4 > a").text
#                 news_url = contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li > div > h4 > a").get_attribute("href")
#                 news_when_orgin = contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li > div > span > em:nth-child(3)").text
#             try : 
#                 news_image = contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li > a > img").get_attribute('src')
#             except NoSuchElementException :
#                 news_image = ' '
#                 pass
#             try : 
#                 contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li> h4 > a").click() # 안으로 들어가기
#             except :
#                 contents[index].find_element(By.CSS_SELECTOR, "#section-list > ul > li > div > h4 > a").click() # 안으로 들어가기

#             news_contents = ''
#             news_contents_p = browser.find_elements(By.CSS_SELECTOR, "#article-view-content-div > p")
#             for news_p in news_contents_p :
#                 news_contents += f'<p>{news_p.text}</p>'
            
#             # 날짜 형식 맞춰주기
#             news_datetime = datetime.strptime(news_when_orgin, '%Y.%m.%d %H:%M')
            
#             bosa_news_coll.insert_one({"news_title" : news_title
#                                     , "news_datetime" : news_datetime
#                                     ,"news_contents":news_contents
#                                     ,"news_url":news_url
#                                     , "news_image" : news_image
#                                      ,'news_paper' : "의학신문" })
#             browser.back()
#             time.sleep(1)
#         except StaleElementReferenceException :
#             print("StaleElementReferenceException 발생. 다음 요소로 넘어갑니다")
#             continue
    
# def thevoicescrapping(browser_name, keyword) :
#     thevoice_news_all = collection_news_weekly_thevoice
    
#     # 실제 사용할 때 꼭 지울 것
#     # thevoice_news_all.delete_many({})

#     chrome_options = Options()
#     # chrome_options.add_argument("--headless")  # Ensure GUI is off
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
    
#     # 현재 날짜 설정
#     from datetime import datetime, timedelta
#     current_datetime = datetime.now()
#     current_date = current_datetime.date()
#     one_week_date = current_date - timedelta(days=10)
#     current_date = current_date.strftime('%Y-%m-%d')
#     one_week_date = one_week_date.strftime('%Y-%m-%d')

#     # 상세검색
#     browser = webdriver.Chrome(options=chrome_options)
#     browser.get(browser_name)
#     browser.find_element(By.CSS_SELECTOR, "#search").send_keys(keyword)
#     browser.find_element(By.CSS_SELECTOR, "fieldset > form > button").click()
#     time.sleep(2)
    
#     # 스크래핑
#     contents = browser.find_elements(By.CSS_SELECTOR,"div.article-list > section > div")
#     for index in range(len(contents)):
#         try :
#             news_title = browser.find_element(By.CSS_SELECTOR, "div.article-list > section > div > div.list-titles > a").text
#             news_url = contents[index].find_element(By.CSS_SELECTOR, "div > div.list-titles > a").get_attribute("href")
#         except NoSuchElementException :
#             pass
#         try : 
#             # contents[index].find_element(By.CSS_SELECTOR, "div > div.list-titles > a > strong").click()
#             link_element = contents[index].find_element(By.CSS_SELECTOR, "div > div.list-titles > a")
#             link_url = link_element.get_attribute("href")
#             browser.execute_script(f"window.open('{link_url}', '_blank');")
#             new_tab = browser.window_handles[-1]
#             browser.switch_to.window(new_tab)
#             # 페이지 안에서 구하기
#             news_datetime_first = browser.find_element(By.CSS_SELECTOR, "section > div > ul > li:nth-child(2)").text
#             date_str = news_datetime_first.split()[1]
#             news_datetime = datetime.strptime(date_str, '%Y.%m.%d')
#             try : 
#                 news_image = browser.find_element(By.CSS_SELECTOR, "#article-view-content-div > div > figure > img").get_attribute('src')
#             except NoSuchElementException :
#                 news_image = ''
#             news_contents =''
#             news_contents_p = browser.find_elements(By.CSS_SELECTOR, "#article-view-content-div > p")
#             for news_p in news_contents_p:
#                 news_contents += f'<p>{news_p.text}</p>'
#         except NoSuchElementException:
#             news_title = 'none'
#             news_datetime = 'none'
#             news_contents = 'none'
#         thevoice_news_all.insert_one({"news_title" : news_title
#                                     ,"news_datetime" : news_datetime
#                                     ,"news_contents":news_contents
#                                     ,"news_url":news_url
#                                     ,"news_image" : news_image
#                                     ,"news_paper" : "뉴스더보이스" })
#         browser.close()
#         time.sleep(1)
#         new_tab = browser.window_handles[-1]
#         browser.switch_to.window(new_tab)
#     return

# bosascrapping("http://www.bosa.co.kr/", "희귀질환")
# thevoicescrapping("http://www.newsthevoice.com/", "희귀질환")
# pass


async def thevoicescrapping(browser_name, keyword, days_range=7):
    """
    The Voice 뉴스 스크래핑 함수 (async 버전)
    
    Args:
        browser_name: 스크래핑할 사이트 URL
        keyword: 검색 키워드
        days_range: 수집 기간 (기본값: 7일)
    """
    
    # 기존 데이터의 URL 목록 가져오기 (중복 방지)
    print("기존 데이터 확인 중...")
    existing_urls = set()
    existing_docs = await news_weekly_thevoice.find_all().to_list()
    for doc in existing_docs:
        if doc.news_url:
            existing_urls.add(doc.news_url)
    
    print(f"기존 데이터: {len(existing_urls)}개의 URL")
    
    # 수집 기간 계산
    from datetime import datetime, timedelta
    current_datetime = datetime.now()
    date_threshold = current_datetime - timedelta(days=days_range)
    
    print(f"수집 기간: {date_threshold.strftime('%Y-%m-%d')} ~ {current_datetime.strftime('%Y-%m-%d')}")
    
    # Chrome 옵션 설정 (headless 모드 활성화)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # CLI 환경을 위해 headless 모드 활성화
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")  # GPU 가속 비활성화
    chrome_options.add_argument("--window-size=1920,1080")  # 화면 크기 설정

    # 브라우저 시작
    browser = webdriver.Chrome(options=chrome_options)
    
    new_count = 0
    skip_count = 0
    error_count = 0
    
    try:
        browser.get(browser_name)
        browser.find_element(By.CSS_SELECTOR, "#search").send_keys(keyword)
        browser.find_element(By.CSS_SELECTOR, "fieldset > form > button").click()
        time.sleep(2)
        
        # 스크래핑
        contents = browser.find_elements(By.CSS_SELECTOR, "div.article-list > section > div")
        print(f"총 {len(contents)}개의 뉴스를 찾았습니다.\n")
        
        for index in range(len(contents)):
            try:
                # 다시 요소 찾기 (StaleElementReferenceException 방지)
                contents = browser.find_elements(By.CSS_SELECTOR, "div.article-list > section > div")
                
                news_title = contents[index].find_element(By.CSS_SELECTOR, "div.list-titles > a").text
                news_url = contents[index].find_element(By.CSS_SELECTOR, "div.list-titles > a").get_attribute("href")
                
                # 중복 체크
                if news_url in existing_urls:
                    skip_count += 1
                    print(f"[{index + 1}/{len(contents)}] ⊘ 중복 건너뜀: {news_title[:40]}...")
                    continue
                
                # 새 탭으로 열기
                link_element = contents[index].find_element(By.CSS_SELECTOR, "div.list-titles > a")
                link_url = link_element.get_attribute("href")
                browser.execute_script(f"window.open('{link_url}', '_blank');")
                new_tab = browser.window_handles[-1]
                browser.switch_to.window(new_tab)
                
                time.sleep(1)  # 페이지 로딩 대기
                
                # 페이지 안에서 정보 구하기
                try:
                    news_datetime_first = browser.find_element(By.CSS_SELECTOR, "section > div > ul > li:nth-child(2)").text
                    date_str = news_datetime_first.split()[1]
                    news_datetime = datetime.strptime(date_str, '%Y.%m.%d')
                except:
                    news_datetime = datetime.now()
                
                # 날짜 필터링 (설정된 기간 내의 뉴스만 저장)
                if news_datetime < date_threshold:
                    skip_count += 1
                    print(f"[{index + 1}/{len(contents)}] ⊘ 기간 외 건너뜀: {news_title[:40]}... (날짜: {news_datetime.strftime('%Y-%m-%d')})")
                    browser.close()
                    browser.switch_to.window(browser.window_handles[0])
                    continue
                
                try:
                    news_image = browser.find_element(By.CSS_SELECTOR, "#article-view-content-div > div > figure > img").get_attribute('src')
                except NoSuchElementException:
                    news_image = ''
                
                news_contents = ''
                news_contents_p = browser.find_elements(By.CSS_SELECTOR, "#article-view-content-div > p")
                for news_p in news_contents_p:
                    news_contents += f'<p>{news_p.text}</p>'
                
                # Beanie 모델을 사용하여 데이터 삽입
                news_doc = news_weekly_thevoice(
                    news_title=news_title,
                    news_datetime=news_datetime,
                    news_contents=news_contents,
                    news_url=news_url,
                    news_image=news_image,
                    news_paper="뉴스더보이스"
                )
                
                await news_doc.insert()
                existing_urls.add(news_url)  # 중복 체크용 세트에 추가
                new_count += 1
                print(f"[{index + 1}/{len(contents)}] ✓ 저장 완료: {news_title[:40]}... (날짜: {news_datetime.strftime('%Y-%m-%d')})")
                
                # 탭 닫고 원래 탭으로 돌아가기
                browser.close()
                time.sleep(1)
                browser.switch_to.window(browser.window_handles[0])
                
            except NoSuchElementException as e:
                error_count += 1
                print(f"[{index + 1}/{len(contents)}] ✗ 요소를 찾을 수 없습니다: {e}")
                # 탭이 열려있다면 닫기
                if len(browser.window_handles) > 1:
                    browser.close()
                    browser.switch_to.window(browser.window_handles[0])
                continue
            except Exception as e:
                error_count += 1
                print(f"[{index + 1}/{len(contents)}] ✗ 오류 발생: {e}")
                # 탭이 열려있다면 닫기
                if len(browser.window_handles) > 1:
                    browser.close()
                    browser.switch_to.window(browser.window_handles[0])
                continue
    
    finally:
        # 브라우저 종료
        browser.quit()
        print("\n" + "="*50)
        print("스크래핑 완료!")
        print(f"  - 새로 저장: {new_count}개")
        print(f"  - 중복/기간외 건너뜀: {skip_count}개")
        print(f"  - 오류: {error_count}개")
        print("="*50)


async def main():
    """
    메인 함수 - DB 초기화 및 스크래핑 실행
    """
    # DB 초기화
    print("\n" + "="*50)
    print("뉴스 스크래핑 시작")
    print("="*50)
    print("\n데이터베이스 초기화 중...")
    settings = Settings()
    await settings.initialize_database()
    print("데이터베이스 초기화 완료!\n")
    
    # 스크래핑 실행 (days_range로 수집 기간 조정 가능)
    print("스크래핑 시작...\n")
    await thevoicescrapping(
        browser_name="http://www.newsthevoice.com/", 
        keyword="희귀질환",
        days_range=7  # ← 이 값을 변경하여 수집 기간 조정 (일 단위)
    )


if __name__ == "__main__":
    # asyncio 이벤트 루프 실행
    asyncio.run(main())
