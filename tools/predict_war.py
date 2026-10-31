import struct, sys
# usage: predict_war.py <dump label> <aggressor> <victim>   -> prints the predicted G<aggressor> row after a war on <victim>, from the formula
N = 23
d = open('C:/GOG Games/Imperialism-RE/results/diplo_%s.bin' % sys.argv[1], 'rb').read()
a, v = int(sys.argv[2]), int(sys.argv[3])
rel = [[struct.unpack('<h', d[0x79c + (r * N + c) * 2: 0x79c + (r * N + c) * 2 + 2])[0] for c in range(N)] for r in range(N)]
gp = lambda n: n < 7
neigh = lambda i: (not gp(i)) and rel[v][i] == 150          # neighbouring Minor Nations score 150 with each other


def setrel(x, y, val):
    if val < 0: val = 0
    u = val
    if val > 255 and x != y: u = 255
    if val < 50: u = 50 if True else val                     # not at war yet when the formula runs? war status is set first: below 50 allowed
    return u


s = rel[a][v]
pred = list(rel[a])
pred[v] = min(s - 50, 49)
for i in range(N):
    if i in (a, v): continue
    if not gp(v): div = 8 if gp(i) else (2 if neigh(i) else 4)
    else: div = 4 if gp(i) else 8
    num = (90 - rel[v][i]) * s
    delta = int(num / (div * 50))                          # truncate toward zero
    cur = rel[a][i]
    now = cur + delta
    if cur < 50:
        if delta > 0 and now > 49: now = 49
    elif now < 50: now = 50
    pred[i] = now
print('before :', rel[a])
print('predict:', pred)
