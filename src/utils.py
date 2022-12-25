from typing import List

import numpy


def lev_dist(token1, token2):
    distances = numpy.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2

    a = 0
    b = 0
    c = 0

    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if token1[t1 - 1] == token2[t2 - 1]:
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]

                if a <= b and a <= c:
                    distances[t1][t2] = a + 1
                elif b <= a and b <= c:
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1

    return distances[len(token1)][len(token2)]


def arxiv_author_match(query_author: str, author_list: List[str]):
    for auth in author_list:
        if lev_dist(query_author, auth) < 3:
            return True
    return False


def arxiv_abstract_match(query_abstract, target_abstract):
    list_query = query_abstract.split(" ")
    list_target = target_abstract.split(" ")
    list_query = [f.lower() for f in list_query]
    list_target = [f.lower() for f in list_target]

    list_inter = list(set(list_query) & set(list_target))
    if bool(list_inter):
        return True
    else:
        return False
