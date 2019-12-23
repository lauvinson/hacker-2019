# coding=utf-8
import copy
from queue import Queue

from flask import Flask, jsonify
from flask import request
import json
import random
import sys
import numpy as np

from urllib3.connectionpool import xrange

from _class import direction
from search import Map, AStarSearch, MyThread
from took import getLocation

app = Flask(__name__)
maps = []
width = 0
height = 0
name = ''
enemy = ''
# 起始节点
startNode = 0, 0
# 起始buff节点
startBuffNode = 0, 0
# 起始buff临近点
sbn = None
# 行走记录
moveRec1 = []
moveRec2 = []
moveRec3 = []
moveRec4 = []
# 行走回合
step = 0


@app.route('/player/start', methods=["POST"])
def init():
    game_map = json.loads(request.data.decode('utf-8'))  # 地图信息
    global maps, width, height, name, enemy, startNode, startBuffNode, sbn, moveRec1, moveRec2, moveRec3, moveRec4, step
    maps = []
    width = 0
    height = 0
    name = ''
    enemy = ''
    # 起始节点
    startNode = 0, 0
    # 起始buff节点
    startBuffNode = 0, 0
    sbn = None
    moveRec1 = []
    moveRec2 = []
    moveRec3 = []
    moveRec4 = []
    step = 0
    # 生成可移动地图
    width = game_map['colLen']
    height = game_map['rowLen']
    map1 = Map(width, height)
    map2 = Map(width, height)
    map3 = Map(width, height)
    map4 = Map(width, height)
    maps.append(map1)
    maps.append(map2)
    maps.append(map3)
    maps.append(map4)
    # 已方
    name = game_map["name"]
    # 敌方
    enemy = ''
    if name == 'shu':
        enemy = 'cao'
    else:
        enemy = 'shu'
    startNode = game_map["selfGraveColLen"], game_map["selfGraveRowLen"]
    startBuffNode = getLocation(game_map["map"], "target")
    json_data = {"code": "0"}
    return jsonify(json_data)


# 获取距离
def getFar(pos, dest):
    return np.abs(dest[0] - pos[0]) + np.abs(dest[1] - pos[1])


@app.route('/player/stop', methods=["POST"])
def stop():
    game_map = json.loads(request.data.decode('utf-8'))  # 地图信息
    json_data = {"code": "0"}
    return jsonify(json_data)


@app.route('/player/move', methods=["POST"])
def move():
    global maps, width, height, name, enemy, startNode, startBuffNode, sbn, moveRec1, moveRec2, moveRec3, moveRec4, step
    game_map = json.loads(request.data.decode('utf-8'))
    gmap = copy.deepcopy(game_map["map"])
    targetWith = game_map["targetWith"]
    noBuff = None is targetWith
    buffMe = False
    targetWithName = ''
    if not noBuff:
        targetWithName = targetWith.lower()
        buffMe = name == targetWith.lower()[:len(targetWith) - 1]
    # 获取英雄位置
    ps = []
    p1 = getLocation(gmap, name + "1")
    p2 = getLocation(gmap, name + "2")
    p3 = getLocation(gmap, name + "3")
    p4 = getLocation(gmap, name + "4")
    ps.append(p1)
    ps.append(p2)
    ps.append(p3)
    ps.append(p4)

    # 行走位置记录
    moveRec1.append(p1)
    if len(moveRec1) > 5:
        moveRec1 = moveRec1[-5:]
    moveRec2.append(p2)
    if len(moveRec2) > 5:
        moveRec2 = moveRec2[-5:]
    moveRec3.append(p3)
    if len(moveRec3) > 5:
        moveRec3 = moveRec3[-5:]
    moveRec4.append(p4)
    if len(moveRec4) > 5:
        moveRec4 = moveRec4[-5:]

    # 目标计算
    # 目标集合
    ts = []
    # t1目标为buff
    target = getLocation(gmap, "target")
    # buff没有拿到时值守
    # 当队伍为shu，并且步数为最后一步，不锁定
    if name == "shu" and step > 248:
        print()
    else:
        if noBuff and getFar(p1, target) < 2:
            maps[0].block(target[1], target[0], -1)
        if noBuff and getFar(p2, target) < 2:
            maps[1].block(target[1], target[0], -1)
        if noBuff and getFar(p3, target) < 2:
            maps[2].block(target[1], target[0], -1)
        if noBuff and getFar(p4, target) < 2:
            maps[3].block(target[1], target[0], -1)

    t1, t2, t3, t4 = target, target, target, target

    # 锁定节点
    for ix in range(height):
        for iy in range(width):
            # 当宝物在已方时，锁定敌方节点上下左右，防止主动触碰敌方
            if not noBuff and buffMe:
                if gmap[ix][iy][enemy + '1'] or gmap[ix][iy][enemy + '2'] or gmap[ix][iy][enemy + '3'] or gmap[ix][iy][enemy + '4']:
                    k = 0
                    if name + str(2) == targetWithName:
                        k = 1
                    elif name + str(3) == targetWithName:
                        k = 2
                    elif name + str(4) == targetWithName:
                        k = 3
                    maps[k].block(ix, iy, -1)
                    if ix < height - 1:
                        maps[k].block(ix + 1, iy, -1)
                    if ix > height - 1:
                        maps[k].block(ix - 1, iy, -1)
                    if iy < width - 1:
                        maps[k].block(ix, iy + 1, -1)
                    if iy > width - 1:
                        maps[k].block(ix, iy - 1, -1)
            if gmap[ix][iy]["block"]:
                maps[0].block(ix, iy, 1)
                maps[1].block(ix, iy, 1)
                maps[2].block(ix, iy, 1)
                maps[3].block(ix, iy, 1)
            if gmap[ix][iy]["unknown"]:
                maps[0].unView(ix, iy)
                maps[1].unView(ix, iy)
                maps[2].unView(ix, iy)
                maps[3].unView(ix, iy)

    # 计算buff临近点
    if maps[0].map[startBuffNode[1]][startBuffNode[0] + 1] != 1 and maps[0].map[startBuffNode[1]][
        startBuffNode[0] + 1] != -1:
        sbn = startBuffNode[0] + 1, startBuffNode[1]
    elif maps[0].map[startBuffNode[1]][startBuffNode[0] - 1] != 1 and maps[0].map[startBuffNode[1]][
        startBuffNode[0] - 1] != -1:
        sbn = startBuffNode[0] - 1, startBuffNode[1]
    elif maps[0].map[startBuffNode[1] + 1][startBuffNode[0]] != 1 and maps[0].map[startBuffNode[1] + 1][
        startBuffNode[0]] != -1:
        sbn = startBuffNode[0], startBuffNode[1] + 1
    elif maps[0].map[startBuffNode[1] - 1][startBuffNode[0]] != 1 and maps[0].map[startBuffNode[1] - 1][
        startBuffNode[0]] != -1:
        sbn = startBuffNode[0], startBuffNode[1] - 1
    # 如果buff在我方，就远离对面，否则就去追击buff
    hfar = 5
    unfar = 7
    if not noBuff and buffMe:
        tail = 1
        if getFar(p1, target) < getFar(p4, target):
            tail += 1
            if target[0] < width:
                t1 = target[0] + 1, target[1]
            else:
                t1 = target[0] - 1, target[1]
            if getFar(p4, target) < hfar and tail < 3:
                t4 = target
            else:
                t4 = sbn
        else:
            tail += 1
            if getFar(p1, target) < hfar and tail < 3:
                t1 = target
            else:
                t1 = sbn
            if target[0] < width:
                t4 = target[0] + 1, target[1]
            else:
                t4 = target[0] - 1, target[1]
        if getFar(p2, target) < getFar(p1, target):
            tail += 1
            if target[0] < width - 1:
                t2 = target[0] + 1, target[1]
            else:
                t2 = target[0] - 1, target[1]
            if getFar(p1, target) < hfar and tail < 3:
                t1 = target
            else:
                t1 = sbn
        else:
            tail += 1
            if getFar(p2, target) < hfar and tail < 3:
                t2 = target
            else:
                t2 = sbn
            if target[0] < width - 1:
                t1 = target[0] + 1, target[1]
            else:
                t1 = target[0] - 1, target[1]
        if getFar(p3, target) < getFar(p2, target):
            tail += 1
            if target[0] < width - 1:
                t3 = target[0] + 1, target[1]
            else:
                t3 = target[0] - 1, target[1]
            if getFar(p2, target) < hfar and tail < 3:
                t2 = target
            else:
                t2 = sbn
        else:
            tail += 1
            if getFar(p3, target) < hfar and tail < 3:
                t3 = target
            else:
                t3 = sbn
            if target[0] < width - 1:
                t2 = target[0] + 1, target[1]
            else:
                t2 = target[0] - 1, target[1]
        if getFar(p4, target) < getFar(p3, target):
            tail += 1
            if target[1] < height - 1:
                t4 = target[0], target[1] + 1
            else:
                t4 = target[0], target[1] - 1
            if getFar(p3, target) < hfar and tail < 3:
                t3 = target
            else:
                t3 = sbn
        else:
            tail += 1
            if getFar(p4, target) < hfar and tail < 3:
                t4 = target
            else:
                t4 = sbn
            if target[1] < height - 1:
                t3 = target[0], target[1] + 1
            else:
                t3 = target[0], target[1] - 1

        if name + str(1) == targetWithName:
            t1 = startNode
        if name + str(2) == targetWithName:
            t2 = startNode
        if name + str(3) == targetWithName:
            t3 = startNode
        if name + str(4) == targetWithName:
            t4 = startNode
    elif not noBuff and not buffMe:
        if getFar(p4, target) <= unfar:
            t4 = target
        else:
            t4 = sbn
        if getFar(p1, target) <= unfar:
            t1 = target
        else:
            t1 = sbn
        if getFar(p2, target) <= unfar:
            t2 = target
        else:
            t2 = sbn
        if getFar(p3, target) <= unfar:
            t3 = target
        else:
            t3 = sbn

    ts.append(t1)
    ts.append(t2)
    ts.append(t3)
    ts.append(t4)

    # 计算移动线程
    li = []
    for i, p in enumerate(ps):
        t = MyThread(excute, args=(maps.__getitem__(i), p, ts.__getitem__(i)))
        li.append(t)
        t.start()

    results = {}
    for i, t in enumerate(li):
        t.join()  # 一定要join，不然主线程比子线程跑的快，会拿不到结果
        result = t.get_result()
        if results is not None:
            if step / 1 < i:
                result = direction.STAY
            results['player%s' % (i + 1)] = result
        elif buffMe:
            tl = gmap[target[0] - 1][target[1]]
            t2 = gmap[target[0] + 1][target[1]]
            t3 = gmap[target[0]][target[1] - 1]
            t4 = gmap[target[0]][target[1] + 1]
            if t1[enemy + '1'] or t1[enemy + '2'] or \
                    t1[enemy + '3'] or t1[enemy + '4']:
                results['player%s' % (i + 1)] = direction.RIGHT
            elif t2[enemy + '1'] or t2[enemy + '2'] or \
                    t2[enemy + '3'] or t2[enemy + '4']:
                results['player%s' % (i + 1)] = direction.LEFT
            elif t3[enemy + '1'] or t3[enemy + '2'] or \
                    t3[enemy + '3'] or t3[enemy + '4']:
                results['player%s' % (i + 1)] = direction.DOWN
            elif t4[enemy + '1'] or t4[enemy + '2'] or \
                    t4[enemy + '3'] or t4[enemy + '4']:
                results['player%s' % (i + 1)] = direction.UP
            else:
                results['player%s' % (i + 1)] = direction.STAY
    step += 1
    return jsonify(results)


# 获取移动节点
def excute(map, p, target):
    # 让p1去拿大龙
    AStarSearch(map, p, target)
    move1 = nearMove(p[0], p[1], map)
    print("source:", p)
    print("dest:", target)
    print("move:", move1)
    # 清除路线
    map.showMap()
    map.clearWay()
    # map.showMap()
    return move1


# 获取最近的可移动节点,返回direction
def nearMove(x, y, map):
    # x0,y0 only right,bottom
    # xmax,ymax only left, top
    # 把当前位置变2为0
    # left
    map.map[y][x] = 0
    if x > 0:
        if map.get(x - 1, y) == 2:
            return direction.LEFT
    # right
    if x < map.width - 1:
        if map.get(x + 1, y) == 2:
            return direction.RIGHT
    # up
    if y > 0:
        if map.get(x, y - 1) == 2:
            return direction.UP
    # down
    if y < map.height - 1:
        if map.get(x, y + 1) == 2:
            return direction.DOWN
    # random
    return None


if __name__ == '__main__':
    port = 5000
    argv = sys.argv
    if len(argv) > 1:
        port = int(argv[1])
    # app.debug = True
    app.run(host='0.0.0.0', port=port)


# 用对象包装起来，太乱不太好整理
class Graph:
    # 初始化MAP
    def __init__(self, m, t):
        self.m = m
        self.t = t
