# 몽고디비 연결
import asyncio
import pickle
import os
from konlpy.tag import Okt
import sys
sys.path.append('/apps/fastapis')

from database.connection import Settings
from models.trend_news import news_trends
from models.news_weekly import news_weekly
from models.news_weekly_thevoice import news_weekly_thevoice

# load_dotenv()
# def dbconnect(Database_name, collection_name) :
#     mongoClient = MongoClient("mongodb://trainings.iptime.org:45003/")
#     database = mongoClient[Database_name]
#     collection = database[collection_name]
#     return collection

def tokenizer(raw, pos=['Noun', 'Verb']):
    stopword = ['서울대', '희귀질환', '희귀', '대다',  '케다', '소아', '생명', '한국', '한미','사노피', '하다', '급여', '국내', '샤이어',  '스케', '세포'
            , '병원',  '질환',  '한독', '화이자제약',  '전달', '질병', '인하대병원',  '관리', '다국적', '환자', '지정', '치료'
            , '오다', '헌터', '작년', '브리', '위해', '베다', '받다', '심평원', '코로나', '건보', '화순', '전남대', '실시', '자임','녹십자'
            ] #추가 생성 필요
    okt=Okt()
    return [
        word for word, tag in okt.pos(raw, norm=True, stem=True)
        if len(word) >1 and tag in pos and word not in stopword
    ]
    

# def update_news_trend_collection(collection_name):
#     news_weekly_collection = dbconnect("teamkim", collection_name)
#     news_collection = dbconnect("teamkim", "trend_news")
    
#     # daily 에 있는 내용 가지고 오기
#     cursor = news_weekly_collection.find({})
    
#     file_path = os.path.join(os.getcwd(), 'data', 'pkl', 'news_recommend_vectorizer.pkl')
#     with open(file_path, "rb") as file:
#         vectorizer = pickle.load(file)

#     with open(os.path.join('data', 'pkl', 'news_recommend_model.pkl'), "rb") as file:
#         model = pickle.load(file)

#     # vectorizer(tokenizer=tokenizer)

#     for document in cursor :
#         news_title = document.get('news_title')
#         news_topic_array = model.predict(vectorizer.transform([news_title]))
#         news_topic = ''.join(news_topic_array)
#         document['news_topic'] = news_topic
#         news_collection.insert_one(document)
#         pass

#     # news_trend_collection에 내용 추가하기

# if __name__ == "__main__" :
#     update_news_trend_collection("news_weekly") #bosa
#     update_news_trend_collection("news_weekly_thevoice") #thevoice
#     pass

async def update_news_trend_collection(source_model, collection_name):
    """
    뉴스를 토픽 분류하여 trend_news 컬렉션에 병합
    
    Args:
        source_model: Beanie 모델 클래스 (news_weekly 또는 news_weekly_thevoice)
        collection_name: 로그용 컬렉션 이름
    """
    print(f"\n{'='*50}")
    print(f"{collection_name} 처리 시작...")
    print(f"{'='*50}")
    
    # 머신러닝 모델 로드
    file_path = os.path.join(os.getcwd(), 'data', 'pkl', 'news_recommend_vectorizer.pkl')
    with open(file_path, "rb") as file:
        vectorizer = pickle.load(file)
    
    with open(os.path.join('data', 'pkl', 'news_recommend_model.pkl'), "rb") as file:
        model = pickle.load(file)
    
    # 1주일 전 날짜 계산
    from datetime import datetime, timedelta
    one_week_ago = datetime.now() - timedelta(days=7)
    
    print(f"처리 기준: {one_week_ago.strftime('%Y-%m-%d %H:%M:%S')} 이후 뉴스만 처리")
    
    # 최근 1주일 데이터만 가져오기
    documents = await source_model.find(
        source_model.news_datetime >= one_week_ago
    ).to_list()
    
    print(f"최근 1주일 내 {len(documents)}개의 뉴스를 찾았습니다.")
    
    if len(documents) == 0:
        print("처리할 새로운 뉴스가 없습니다.")
        return
    
    # 이미 trend_news에 있는 URL 목록 가져오기 (중복 방지)
    existing_urls = set()
    existing_docs = await news_trends.find_all().to_list()
    for doc in existing_docs:
        if doc.news_url:
            existing_urls.add(doc.news_url)
    
    print(f"기존 trend_news에 {len(existing_urls)}개의 URL이 이미 존재합니다.")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for idx, document in enumerate(documents, 1):
        try:
            news_title = document.news_title
            news_url = document.news_url
            
            # 중복 체크
            if news_url in existing_urls:
                skip_count += 1
                print(f"[{idx}/{len(documents)}] ⊘ 중복 건너뜀: {news_title[:30]}...")
                continue
            
            if not news_title:
                print(f"[{idx}] 제목이 없는 뉴스 건너뜀")
                error_count += 1
                continue
            
            # 토픽 예측 (vectorizer가 이미 토크나이징 포함)
            news_topic_array = model.predict(vectorizer.transform([news_title]))
            news_topic = ''.join(news_topic_array)
            # 예상 결과: "의료/법안", "신약/개발", "심포지엄/행사" 중 하나
            
            # trend_news에 저장할 새 문서 생성
            trend_news_doc = news_trends(
                news_title=document.news_title,
                news_datetime=document.news_datetime,
                news_contents=document.news_contents,
                news_url=document.news_url,
                news_image=document.news_image,
                news_paper=document.news_paper,
                news_topic=news_topic  # 토픽 추가
            )
            
            # trend_news 컬렉션에 삽입
            await trend_news_doc.insert()
            existing_urls.add(news_url)  # 중복 체크용 세트에 추가
            
            success_count += 1
            print(f"[{idx}/{len(documents)}] ✓ {news_title[:30]}... → 토픽: {news_topic}")
            
        except Exception as e:
            error_count += 1
            print(f"[{idx}/{len(documents)}] ✗ 오류: {e}")
            continue
    
    print(f"\n{collection_name} 처리 완료!")
    print(f"  - 성공: {success_count}개")
    print(f"  - 중복 건너뜀: {skip_count}개")
    print(f"  - 실패: {error_count}개")
    print(f"{'='*50}\n")


async def main():
    """
    메인 함수 - DB 초기화 및 뉴스 병합 실행
    """
    print("\n" + "="*50)
    print("뉴스 토픽 분류 및 병합 시작")
    print("="*50)
    
    # DB 초기화
    print("\n데이터베이스 초기화 중...")
    settings = Settings()
    await settings.initialize_database()
    print("데이터베이스 초기화 완료!\n")
    
    # news_weekly 처리
    await update_news_trend_collection(news_weekly, "news_weekly")
    
    # news_weekly_thevoice 처리
    await update_news_trend_collection(news_weekly_thevoice, "news_weekly_thevoice")
    
    print("\n" + "="*50)
    print("모든 작업 완료!")
    print("="*50 + "\n")


if __name__ == "__main__":
    # asyncio 이벤트 루프 실행
    asyncio.run(main())