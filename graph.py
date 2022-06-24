from functools import cmp_to_key
from math import inf
from dataclasses import dataclass, field
from geopy import distance
from numpy import indices
import pandas as pd
import heapq

DB = './DB'

@dataclass
class Node:
    pos:tuple = ()
    threshold:float = None
    data:dict = field(default_factory=dict)

class MapGraph:
    def __init__(self):
        self.keywords = ['hospital','pharmacy','gas','cafe','pc','convenient']
        self.nodes = []
        self.dataFrames = {}
        self.initNodes()
        self.adjList = [[] for _ in range(len(self.nodes))]
        self.initEdges()
        self.loadDB()
        self.mapDBtoNode()
        self.start = 0
    
    def initNodes(self):
        with open(f'{DB}/Graph/NodeInfo.txt', 'r') as f:
            nodeInfos = f.readlines()
            for nodeInfo in nodeInfos:
                node = nodeInfo.strip().split(' ')
                n = Node(pos=(node[0], node[1]), threshold=0.2)
                for k in self.keywords:
                    n.data[k] = []
                self.nodes.append(n)
        # print('노드 개수: ', len(self.nodes))
    
    def initEdges(self):
        with open(f'{DB}/Graph/EdgeInfo.txt', 'r') as f:
            edgeInfos = f.readlines()
            for edgeInfo in edgeInfos:
                edge = edgeInfo.strip().split(' ')
                u, v = int(edge[0]) - 1, int(edge[1]) - 1
                self.createEdge(u, v)

    def createEdge(self, u, v):
        weight = distance.distance(self.nodes[u].pos, self.nodes[v].pos).km
        self.adjList[u].append((weight, v))
        self.adjList[v].append((weight, u))

        #* 임계값 갱신
        newThreshold = weight * 0.3
        if self.nodes[u].threshold < newThreshold:
            self.nodes[u].threshold = newThreshold
        if self.nodes[v].threshold < newThreshold:
            self.nodes[v].threshold = newThreshold

    def loadDB(self):
        for keyword in self.keywords:
            df = pd.read_csv(f'{DB}/Stores/{keyword}.csv', sep=',').dropna()
            self.dataFrames[keyword] = df
    
    def mapDBtoNode(self):
        # print('데이터 프레임 개수: ', len(self.dataFrames))
        #* 각 데이터 프레임 속
        for key, df in self.dataFrames.items():
            #* 각 가게들에 대해
            for idx, row in df.iterrows():
                gps = (row['alt'], row['lon'])
                if gps == ('None', 'None'):
                    continue

                #* 노드(교차로)의 위/경도로 거리 계산 
                dists = []
                for node in self.nodes:
                    dist = distance.distance(node.pos, gps).km
                    #* 거리가 임계값 이하인 노드만 확인 
                    if dist < node.threshold:
                        dists.append(dist)
                    else:
                        dists.append(inf)
                
                #* 가장 가까운 노드에 가게를 매핑 시킴
                minDist = min(dists)
                minInd = dists.index(minDist)

                #* 임계값 이하인 노드가 하나 이상일 경우에만 매핑
                if minDist != inf:
                    self.nodes[minInd].data[key].append(idx)
    
    #* 휴리스틱함수로 유클리드거리 사용
    def heuristic(self, u, v):
        return distance.distance(self.nodes[u].pos, self.nodes[v].pos).km
    
    #* 각 노드마다 목적지까지 휴리스틱 적용한 결과 저장
    def initHx(self, e):
        h = []
        for i in range(len(self.nodes)):
            if i == e:
                h.append(0)
                continue
            h.append(self.heuristic(i, e))
        return h

    def aStar(self, s, e):
        s -= 1
        e -= 1

        dist = [inf for i in range(len(self.nodes))]
        self.start = s
        dist[s] = self.heuristic(s, e)

        parent = [0 for i in range(len(self.nodes))]  #* 경로 파악을 위한 스택
        parent[s] = -1

        queue = []
        heapq.heappush(queue, (dist[s], s))

        h = self.initHx(e)

        while queue:
            curDist, curInd = heapq.heappop(queue)

            if curInd == e:
                break

            if dist[curInd] < curDist:
                continue
            
            for nextNode in self.adjList[curInd]:
                nextDist, nextInd = nextNode[0], nextNode[1]
                distance = curDist + nextDist + h[nextInd]
                if distance < dist[nextInd]:
                    dist[nextInd] = distance
                    heapq.heappush(queue, (distance, nextInd))
                    parent[nextInd] = curInd
        
        sPath = []
        tmp = e
        while tmp != -1:
            sPath.append(tmp+1)
            tmp = parent[tmp]
        
        return sPath[::-1], dist
    
    def showPath(self, sPath):
        div = '-'
        for i in range(len(sPath)):
            div += '-'
        print(div)

        print('최단 경로: ', end=' ')
        for i in sPath:
            print(i, end=' ')
        
        print()
        print(div)
    
    def findStores(self, sPath, keyword):
        res = []
        for node in sPath:
            indices = self.nodes[node - 1].data[keyword]
            for row in indices:
                res.append(self.dataFrames[keyword].loc[row])

        return res
    
    def getRank(self, data):
        if data.score != 'None':
            s = float(str(data.score).replace(',',''))
        else:
            s = 0.5
        
        if data.visitor != 'None':
            v = float(str(data.visitor).replace(',',''))
        else:
            v = 0.0
        
        if data.blog != 'None':
            b = float(str(data.blog).replace(',',''))
        else:
            b = 0.0

        distFromStart = distance.distance(self.nodes[self.start].pos, (data.alt, data.lon)).km
        
        alpha = 0.6
        beta = 0.4
        return ((1 + s / 5.0) + beta * (alpha * v + (1-alpha) * b)) / distFromStart

    def comp(self, a, b):
        aRank = self.getRank(a)
        bRank = self.getRank(b)
        if aRank < bRank:
            return 1
        elif aRank == bRank:
            return 0
        else: 
            return -1
    
    def sortByRank(self, stores):
        stores.sort(key=cmp_to_key(self.comp))
        return stores
    
    def showResult(self, result:list):
        if len(result) == 0:
            print('검색 결과가 없습니다.')

        for store in result:
            s = '%s, %s, %s' % (store.title, store.score, store.address)
            print(s)