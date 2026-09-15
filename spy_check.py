import json, math
d = json.load(open(r"D:\wk-probes\weekend_pairs.json"))
def stats(r):
    n=len(r); m=sum(r)/n; s=math.sqrt(sum((x-m)**2 for x in r)/(n-1)) if n>1 else 0
    return n, m*100, s*100
for s in ["SPYUSDT","QQQUSDT"]:
    sm=[r[1] for r in d[s]]; mo=[r[2] for r in d[s]]
    cont=[(1 if sm[i]>0 else -1)*mo[i] for i in range(len(sm))]
    n,m,sd=stats(mo); n2,m2,s2=stats(cont)
    print("%-8s always-long %+.2f%% (IR %+.2f) | continuation %+.2f%%/wk IR %+.2f | t(cont)=%+.2f" % (s, m, m/sd, m2, m2/s2, (m2/s2)*math.sqrt(n2) if s2 else 0))
    # split long/short legs
    up=[mo[i] for i in range(len(sm)) if sm[i]>0]; dn=[-mo[i] for i in range(len(sm)) if sm[i]<0]
    print("    long leg n=%d avg %+.2f%% | short leg n=%d avg %+.2f%%" % (len(up), sum(up)/len(up)*100, len(dn), sum(dn)/len(dn)*100))
