import threading
from random import randint
import numpy as np


# 每一个搜索到将到添加到OPEN集的节点，都会创建一个下面的节点类，保存有entry的位置信息（x，y）
# 计算得到的G值和F值，和该节点的父节点（pre_entry）
class SearchEntry:
    def __init__(self, x, y, g_cost, f_cost=0, pre_entry=None):
        self.x = x
        self.y = y
        # cost move form start entry to this entry
        self.g_cost = g_cost
        self.f_cost = f_cost
        self.pre_entry = pre_entry

    def getPos(self):
        return self.x, self.y


class Map:
    # 初始化MAP
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.map = [[0 for x in range(self.width)] for y in range(self.height)]

    def value(self, v):
        self.map = v
        self.height = len(v)
        self.width = len(v[0])

    def set(self, x, y, v):
        self.map[y][x] = v

    # 锁定节点
    def block(self, x, y, v):
        self.map[x][y] = v

    # 遮挡节点
    def unView(self, x, y):
        self.map[x][y] = 3

    # 清除路线和临时锁定
    def clearWay(self):
        a = np.array(self.map)
        a[a == 2] = 0
        a[a == -1] = 0
        self.map = a.tolist()

    # 获取节点
    def get(self, x, y):
        try:
            return self.map[y][x]
        except Exception:
            return None

    # 随机获取可移动节点
    def generatePos(self, rangeX, rangeY):
        x, y = (randint(rangeX[0], rangeX[1]), randint(rangeY[0], rangeY[1]))
        while self.map[y][x] == 1:
            x, y = (randint(rangeX[0], rangeX[1]), randint(rangeY[0], rangeY[1]))
        return x, y

    # 分配一个不可见区域
    def generateUnview(self, width, height):
        # for x in self.map:
        #     for y in x:
        #         if y == 3:
        #             return self.map.index(x), x.index(y)
        return self.generatePos((0, width // 3), (0, height // 3))

    # 显示地图
    def showMap(self):
        print("+" * (3 * self.width + 2))

        for row in self.map:
            s = '+'
            for entry in row:
                s += ' ' + str(entry) + ' '
            s += '+'
            print(s)

        print("+" * (3 * self.width + 2))


# 算法主循环介绍的代码实现，OPEN集和CLOSED集的数据结构使用了字典，
# 在一般情况下，查找，添加和删除节点的时间复杂度为O(1), 遍历的时间复杂度为O(n), n为字典中对象数目
def AStarSearch(map, source, dest):
    def getNewPosition(map, locatioin, offset):
        x, y = (location.x + offset[0], location.y + offset[1])
        if x < 0 or x >= map.width or y < 0 or y >= map.height or map.map[y][x] == 1 or map.map[y][x] == -1:
            return None
        return x, y

    # 获取到所有能够移动的节点,这里提供了2种移动的方式
    # 允许上，下，左，右 4邻域的移动
    # 允许上，下，左，右，左上，右上，左下，右下 8邻域的移动
    def getPositions(map, location):
        # use four ways or eight ways to move
        offsets = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        # offsets = [(-1,0), (0, -1), (1, 0), (0, 1), (-1,-1), (1, -1), (-1, 1), (1, 1)]
        poslist = []
        for offset in offsets:
            pos = getNewPosition(map, location, offset)
            if pos is not None:
                poslist.append(pos)
        return poslist

    # imporve the heuristic distance more precisely in future
    # calHeuristic 函数简单得使用了曼哈顿距离，这个后续可以进行优化。
    def calHeuristic(pos, dest):
        # return np.dot(dest.x, dest.y) / (np.linalg.norm(dest.x) * np.linalg.norm(dest.y))
        # return max(np.abs(dest.x - pos[0]), np.abs(dest.y - pos[1]))
        # 直线
        return min(abs(dest.x - pos[0]) + abs(dest.y - pos[1]), np.sqrt(np.square(dest.x - pos[0]) + np.square(dest.y - pos[1])))
        # 哈夫曼
        # return np.abs(dest.x - pos[0]) + np.abs(dest.y - pos[1])
        # print("距离:", c)
        # 近路
        # if c > 2:
        #     c = np.sqrt(np.square(dest.x - pos[0]) + np.square(dest.y - pos[1]))
        # return c

    # getMoveCost 函数根据是否是斜向移动来计算消耗（斜向就是2的开根号，约等于1.4）
    def getMoveCost(location, pos):
        if location.x != pos[0] and location.y != pos[1]:
            return 1.4
        else:
            return 1

    # check if the position is in list
    # 判断节点是否在OPEN集 或CLOSED集中
    def isInList(list, pos):
        if pos in list:
            return list[pos]
        return None

    # add available adjacent positions
    def addAdjacentPositions(map, location, dest, openlist, closedlist):
        poslist = getPositions(map, location)
        for pos in poslist:
            # if position is already in closedlist, do nothing
            if isInList(closedlist, pos) is None:
                findEntry = isInList(openlist, pos)
                h_cost = calHeuristic(pos, dest)
                g_cost = location.g_cost + getMoveCost(location, pos)
                if findEntry is None:
                    # if position is not in openlist, add it to openlist
                    openlist[pos] = SearchEntry(pos[0], pos[1], g_cost, g_cost + h_cost, location)
                elif findEntry.g_cost > g_cost:
                    # if position is in openlist and cost is larger than current one,
                    # then update cost and previous position
                    findEntry.g_cost = g_cost
                    findEntry.f_cost = g_cost + h_cost
                    findEntry.pre_entry = location

    # find a least cost position in openlist, return None if openlist is empty
    # 从OPEN集中获取一个F值最小的节点，如果OPEN集会空，则返回None
    def getFastPosition(openlist):
        fast = None
        for entry in openlist.values():
            if fast is None:
                fast = entry
            elif fast.f_cost > entry.f_cost:
                fast = entry
        return fast

    openlist = {}
    closedlist = {}
    location = SearchEntry(source[0], source[1], 0.0)
    dest = SearchEntry(dest[0], dest[1], 0.0)
    openlist[source] = location
    while True:
        location = getFastPosition(openlist)
        if location is None:
            # not found valid path
            print("can't find valid path")
            break

        if location.x == dest.x and location.y == dest.y:
            break

        closedlist[location.getPos()] = location
        openlist.pop(location.getPos())
        addAdjacentPositions(map, location, dest, openlist, closedlist)

    # mark the found path at the map
    while location is not None:
        map.map[location.y][location.x] = 2
        location = location.pre_entry


class MyThread(threading.Thread):

    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.result = self.func(*self.args)

    def run(self):
        pass

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None
