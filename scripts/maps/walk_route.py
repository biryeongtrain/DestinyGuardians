"""Bounded A* over a supplied walk-neighbour function; no global map state."""
import heapq
from collections import deque
import numpy as np


def reachable(moves, start, shape):
    seen=np.zeros(shape,bool);queue=deque([start]);seen[start[1],start[2],start[0]]=True
    while queue:
        c=queue.popleft()
        for n in moves(c):
            if not seen[n[1],n[2],n[0]]:
                seen[n[1],n[2],n[0]]=True;queue.append(n)
    return seen


def astar(moves, start, goals, limit=1_000_000):
    goals=set(goals)
    if not goals:
        raise ValueError('No walkable goal cells')
    def h(c):
        return min(abs(c[0]-g[0])+abs(c[2]-g[2])+abs(c[1]-g[1])/3 for g in goals)
    queue=[(h(start),0,start)];dist={start:0};prev={start:None};best=start
    while queue:
        _,cost,c=heapq.heappop(queue)
        if cost != dist[c]:continue
        if h(c)<h(best):best=c
        if c in goals:
            path=[]
            while c is not None:path.append(c);c=prev[c]
            return path[::-1]
        if len(dist)>limit:break
        for n in moves(c):
            weight=1+max(0,n[1]-c[1])*3
            nc=cost+weight
            if nc<dist.get(n,float('inf')):
                dist[n]=nc;prev[n]=c;heapq.heappush(queue,(nc+h(n),nc,n))
    raise ValueError(f'No walk route: start={start}, closest={best}, remaining={h(best):.1f}, searched={len(dist)}')
