def getLocation(map, role):
    for x in map:
        for y in x:
            if y[role]:
                return x.index(y), map.index(x)
