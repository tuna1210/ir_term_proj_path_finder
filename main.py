from graph import *
from konlpy.tag import Hannanum

def findNode(word):
    if word == '구정문':
        return 15
    if word == '신정문':
        return 30
    if word == '사대부고':
        return 48
    if word == '덕진광장':
        return 2
    if word == '종합경기장':
        return 20
    if word == '박물관':
        return 5

    return None

def findKey(word):
    if word == '카페':
        return 'cafe'
    if word == '병원':
        return 'hospital'
    if word == '주유소':
        return 'gas'
    if word == '피시방' or word == 'PC방':
        return 'pc'
    if word == '약국':
        return 'pharmacy'
    if word == '편의점':
        return 'convenient'
    
    return None

if __name__=='__main__':
    han = Hannanum()
    mg = MapGraph()

    print('검색어를 입력하시오')
    query = input()
    try:
        nouns = han.nouns(query)
        a = findNode(nouns[0])
        b = findNode(nouns[1])
        c = findKey(nouns[2])
        assert a != None and b != None and c != None, '형태소 분석 실패'
    except:
        q1 = query.split('부터 ')
        q2 = q1[1].split('까지 ')
        a = findNode(q1[0])
        b = findNode(q2[0])
        c = findKey(q2[1])

    if a == None or b == None or c == None:
        print('잘못된 검색어입니다.')
        exit()

    sPath, dist = mg.aStar(a, b)
    mg.showPath(sPath)
    store = mg.findStores(sPath, c)
    result = mg.sortByRank(store)
    mg.showResult(result)