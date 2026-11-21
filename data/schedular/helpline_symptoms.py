from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import re
import sys
import os
import shutil
sys.path.append('/apps/fastapis')
import asyncio

from database.connection import Settings
from beanie import Document
from pydantic import BaseModel
from typing import Optional
from models.helpline_symptoms import HelplineSymptoms


def get_chrome_driver(headless=True):
    """
    ChromeDriver를 올바르게 설치하고 반환
    
    Args:
        headless: headless 모드 여부
    
    Returns:
        webdriver: Chrome WebDriver 인스턴스
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # ChromeDriver 경로 가져오기
        driver_path = ChromeDriverManager().install()
        
        # 경로 수정: 실제 chromedriver 실행 파일 찾기
        import os
        if 'THIRD_PARTY_NOTICES' in driver_path or not driver_path.endswith('chromedriver'):
            # 디렉토리에서 실제 chromedriver 찾기
            driver_dir = os.path.dirname(driver_path)
            
            # chromedriver 파일 찾기
            for file in os.listdir(driver_dir):
                if file == 'chromedriver' or file == 'chromedriver.exe':
                    driver_path = os.path.join(driver_dir, file)
                    break
        
        # 실행 권한 부여 (Linux)
        if os.path.exists(driver_path) and not driver_path.endswith('.exe'):
            os.chmod(driver_path, 0o755)
        
        driver = webdriver.Chrome(
            service=ChromeService(driver_path),
            options=chrome_options
        )
        return driver
        
    except Exception as e:
        print(f"ChromeDriver 설치 오류: {e}")
        print("캐시를 삭제하고 재시도합니다...")
        
        # 캐시 삭제
        import shutil
        cache_path = os.path.join(os.path.expanduser('~'), '.wdm')
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
        
        # 재시도
        driver_path = ChromeDriverManager().install()
        
        # 경로 수정
        import os
        if 'THIRD_PARTY_NOTICES' in driver_path or not driver_path.endswith('chromedriver'):
            driver_dir = os.path.dirname(driver_path)
            for file in os.listdir(driver_dir):
                if file == 'chromedriver' or file == 'chromedriver.exe':
                    driver_path = os.path.join(driver_dir, file)
                    break
        
        # 실행 권한 부여
        if os.path.exists(driver_path) and not driver_path.endswith('.exe'):
            os.chmod(driver_path, 0o755)
        
        driver = webdriver.Chrome(
            service=ChromeService(driver_path),
            options=chrome_options
        )
        return driver


def get_total_pages(headless=True):
    """
    전체 페이지 수를 자동으로 감지
    '총 1389건 [ 1/139 페이지 ]' 형태의 텍스트에서 총 페이지 수 추출
    
    Returns:
        int: 전체 페이지 수
    """
    driver = get_chrome_driver(headless)
    
    try:
        # 첫 페이지로 이동
        driver.get("https://helpline.kdca.go.kr/cdchelp/ph/rdiz/selectRdizInfList.do?menu=A0100&pageIndex=1")
        time.sleep(2)
        
        try:
            # 총 페이지 정보 텍스트 가져오기
            # 예: '총 1389건 [ 1/139 페이지 ]'
            page_info_element = driver.find_element(By.CSS_SELECTOR, '#frm > div > div.tbl_top > p')
            page_info_text = page_info_element.text.strip()
            
            print(f"페이지 정보: {page_info_text}")
            
            # 정규표현식으로 "X/Y 페이지"에서 Y 추출
            import re
            match = re.search(r'(\d+)/(\d+)\s*페이지', page_info_text)
            
            if match:
                current_page = int(match.group(1))
                total_pages = int(match.group(2))
                print(f"감지된 총 페이지 수: {total_pages}페이지")
                return total_pages
            else:
                print("페이지 정보를 파싱할 수 없습니다. 기본값 124를 사용합니다.")
                return 124
                
        except Exception as e:
            print(f"페이지 수 감지 중 오류: {e}")
            print("기본값 124를 사용합니다.")
            return 124
    
    finally:
        driver.quit()


async def scrape_helpline_symptoms_optimized(page_num, headless, existing_urls, existing_names_kr, existing_names_en):
    """
    헬프라인 증상 정보 스크래핑 (최적화 버전)
    
    Args:
        page_num: 페이지 번호
        headless: CLI 환경 여부
        existing_urls: 기존 URL 세트
        existing_names_kr: 기존 한국어명 세트 (정규화됨)
        existing_names_en: 기존 영어명 세트 (정규화됨)
    
    Returns:
        (new_count, skip_count, error_count) 튜플
    """
    driver = get_chrome_driver(headless)
    
    new_count = 0
    skip_count = 0
    error_count = 0
    
    try:
        url = f"https://helpline.kdca.go.kr/cdchelp/ph/rdiz/selectRdizInfList.do?menu=A0100&pageIndex={page_num}"
        driver.get(url)
        time.sleep(2)
        
        table_rows = driver.find_elements(By.CSS_SELECTOR, "#frm > div > table > tbody > tr")
        
        # 데이터가 없으면 종료
        if len(table_rows) == 0:
            print(f"[페이지 {page_num}] 데이터 없음 - 건너뜀")
            return new_count, skip_count, error_count
        
        for idx, row in enumerate(table_rows, 1):
            data = {}
            
            try:
                full_text = row.find_element(By.CSS_SELECTOR, value="td:nth-child(2) > dl > dt").text
                data['dise_name_kr'] = full_text.split('\n')[0]
            except:
                data['dise_name_kr'] = ""
            
            try:
                data['dise_name_en'] = row.find_element(By.CSS_SELECTOR, value="td:nth-child(2) > dl > dt > p").text
            except:
                data['dise_name_en'] = ""
            
            try:
                KCD_code = row.find_element(By.XPATH, value='.//td[1]/dl/dd/ul/li[4]').text
                data['dise_KCD_code'] = KCD_code.replace('KCD코드 : ', '').strip()
            except:
                data['dise_KCD_code'] = ""
            
            try:
                spc = row.find_element(By.XPATH, value='.//td[1]/dl/dd/ul/li[5]').text
                data['dise_spc_code'] = spc.replace('산정특례 특정기호 : ', '').strip()
            except:
                data['dise_spc_code'] = ""
            
            try:
                group = row.find_element(By.XPATH, value='.//td[1]/dl/dd/ul/li[1]').text
                data['dise_group'] = group.replace('항목분류 : ', '').strip()
            except:
                data['dise_group'] = ""
            
            try:
                support = row.find_element(By.XPATH, value='.//td[1]/dl/dd/ul/li[3]').text
                data['dise_support'] = support.replace('의료비지원 : ', '').strip()
            except:
                data['dise_support'] = ""
            
            try:
                link_element = row.find_element(By.CSS_SELECTOR, value="a[title='질환정보 바로가기']")
                onclick_attr = link_element.get_attribute('onclick')
                match = re.search(r"fn_moveDetail\('(.+?)'\);", onclick_attr)
                if match:
                    detail_code = match.group(1)
                    url_template = 'https://helpline.kdca.go.kr/cdchelp/ph/rdiz/selectRdizInfDetail.do?menu=A0100&rdizCd={}'
                    data['dise_url'] = url_template.format(detail_code)
                else:
                    data['dise_url'] = ""
            except Exception as url_error:
                data['dise_url'] = ""
            
            # 3단계 중복 체크
            is_duplicate = False
            duplicate_reason = ""
            
            # 1단계: URL이 있으면 URL로 중복 체크 (가장 확실)
            if data['dise_url'] and data['dise_url'] in existing_urls:
                is_duplicate = True
                duplicate_reason = "URL 중복"
            
            # 2단계: URL 중복이 아니고 한국어명이 있으면
            elif data['dise_name_kr']:
                normalized_name_kr = data['dise_name_kr'].replace(' ', '').strip()
                
                # 한국어명이 중복된 경우
                if normalized_name_kr in existing_names_kr:
                    # 3단계: 영어명도 확인 (둘 다 같아야 진짜 중복)
                    if data['dise_name_en']:
                        normalized_name_en = data['dise_name_en'].replace(' ', '').strip().lower()
                        if normalized_name_en in existing_names_en:
                            is_duplicate = True
                            duplicate_reason = "한국어명+영어명 중복"
                        else:
                            # 한국어명은 같지만 영어명이 다름 → 다른 질환
                            is_duplicate = False
                            print(f"  ℹ 주의: {data['dise_name_kr']} - 한국어명 동일하나 영어명 다름 (신규 저장)")
                    else:
                        # 영어명이 없는 경우는 한국어명만으로 중복 판단
                        is_duplicate = True
                        duplicate_reason = "한국어명 중복 (영어명 없음)"
            
            if is_duplicate:
                skip_count += 1
                print(f"  ⊘ 중복: {data['dise_name_kr']} ({duplicate_reason})")
                continue
            
            # MongoDB에 직접 저장 (빈 필드 완전 제거)
            try:
                # 빈 문자열이나 None 값을 가진 필드 제거
                cleaned_data = {k: v for k, v in data.items() if v}
                
                # Beanie의 insert_one 대신 MongoDB 직접 접근
                await HelplineSymptoms.get_motor_collection().insert_one(cleaned_data)
                
                # 중복 체크용 세트에 추가
                if cleaned_data.get('dise_url'):
                    existing_urls.add(cleaned_data['dise_url'])
                if cleaned_data.get('dise_name_kr'):
                    normalized_name_kr = cleaned_data['dise_name_kr'].replace(' ', '').strip()
                    existing_names_kr.add(normalized_name_kr)
                if cleaned_data.get('dise_name_en'):
                    normalized_name_en = cleaned_data['dise_name_en'].replace(' ', '').strip().lower()
                    existing_names_en.add(normalized_name_en)
                
                new_count += 1
                url_status = "✓" if cleaned_data.get('dise_url') else "⚠"
                print(f"  {url_status} 새 데이터: {cleaned_data.get('dise_name_kr', '이름없음')}")
                
            except Exception as e:
                error_count += 1
                print(f"  ✗ 저장 오류: {data.get('dise_name_kr', '이름없음')} - {e}")
            
            time.sleep(0.5)
    
    except Exception as e:
        print(f"[페이지 {page_num}] 오류: {e}")
        error_count += 1
    
    finally:
        driver.quit()
        # 항상 결과 출력 (데이터가 있든 없든)
        print(f"[페이지 {page_num}] 완료 - 신규: {new_count}, 중복: {skip_count}, 오류: {error_count}")
    
    return new_count, skip_count, error_count


async def scrape_all_pages(headless=True):
    """
    전체 페이지 스크래핑 (자동 페이지 수 감지)
    
    Args:
        headless: CLI 환경 여부
    """
    print("\n" + "="*60)
    print("전체 스크래핑 시작 (매월 1일 정기 업데이트)")
    print("="*60)
    
    # 전체 페이지 수 자동 감지
    print("\n페이지 수 확인 중...")
    total_pages = get_total_pages(headless)
    print(f"총 {total_pages}개 페이지를 스크래핑합니다.\n")
    
    # 기존 데이터 로드 - URL, 한국어명, 영어명 모두 수집
    print("기존 데이터 확인 중...")
    existing_urls = set()
    existing_names_kr = set()
    existing_names_en = set()
    existing_docs = await HelplineSymptoms.find_all().to_list()
    
    for doc in existing_docs:
        if doc.dise_url:
            existing_urls.add(doc.dise_url)
        if doc.dise_name_kr:
            # 한국어 이름 정규화 (공백 제거)
            normalized_name_kr = doc.dise_name_kr.replace(' ', '').strip()
            existing_names_kr.add(normalized_name_kr)
        if doc.dise_name_en:
            # 영어 이름 정규화 (공백 제거, 소문자 변환)
            normalized_name_en = doc.dise_name_en.replace(' ', '').strip().lower()
            existing_names_en.add(normalized_name_en)
    
    print(f"기존 데이터: {len(existing_docs)}개")
    print(f"  - URL: {len(existing_urls)}개")
    print(f"  - 한국어명: {len(existing_names_kr)}개")
    print(f"  - 영어명: {len(existing_names_en)}개")
    print(f"중복 체크: 1) URL → 2) 한국어명 같으면 → 3) 영어명도 확인 (둘 다 같아야 중복)\n")
    
    total_new = 0
    total_skip = 0
    total_error = 0
    
    for page_num in range(1, total_pages + 1):
        new_count, skip_count, error_count = await scrape_helpline_symptoms_optimized(
            page_num, 
            headless, 
            existing_urls,
            existing_names_kr,
            existing_names_en
        )
        total_new += new_count
        total_skip += skip_count
        total_error += error_count
        
        time.sleep(2)  # 페이지 간 대기
    
    print("\n" + "="*60)
    print("전체 스크래핑 완료!")
    print(f"  - 총 페이지: {total_pages}개")
    print(f"  - 새로 저장: {total_new}개")
    print(f"  - 중복 건너뜀: {total_skip}개")
    print(f"  - 오류: {total_error}개")
    print("="*60)


async def main():
    """
    메인 함수
    """
    # DB 초기화
    print("\n데이터베이스 초기화 중...")
    settings = Settings()
    await settings.initialize_database()
    print("데이터베이스 초기화 완료!\n")
    
    # 전체 스크래핑 실행
    await scrape_all_pages(headless=True)


if __name__ == "__main__":
    asyncio.run(main())