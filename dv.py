import pandas as pd 

p_inf = float("inf")


class Node:
    def __init__(self, id: str, start: pd.DataFrame):
        self.id = id
        self.table = pd.DataFrame(data=p_inf, index=[1, 2, 3, 4], columns=[1, 2, 3, 4])
        print(start)

        self.table.loc[id] = start.loc[id]

    def _dist(self, target):
        new_dist = []
        for n in self.table.columns:
            cost = self.table.loc[n, self.id]
            dist_to = self.table.loc[n, target]
            new_dist.append(cost + dist_to)
        return min(new_dist)

    def update(self, inc_node, new_table):
        # set current info to  incoming
        self.table.loc[inc_node] = new_table.loc[inc_node]
        # update info
        for c in self.table.columns:
            self.table.loc[self.id, c] = self._dist(c)
            

if __name__ == "__main__":
    name = "w"
    df = pd.read_csv("./w.csv", index_col='id')

    test_node = Node(name, df)
    print(test_node.table)

    name2 = "x"
    df2 = pd.read_csv("./x.csv", index_col='id')

    test_node2 = Node(name2, df2)
    test_node.update(name2, test_node2.table)

    print(test_node.table)

    print(test_node2.table)
