import pandas as pd 

p_inf = float("inf")

class Node():
    def __init__(self, id:str, start:pd.DataFrame):
        self.id = id
        self.table = pd.DataFrame(data = p_inf, index = ["w", "x", "y", "z"], columns  = ["w", "x", "y", "z"])
        self.table.loc[id] = start.loc[0]

    def dist(self, target, inc_node):
            cost = self.table.loc[self.id, inc_node]
            dist_to = self.table.loc[inc_node, target]
            cur_dist = self.table.loc[self.id, target]
            return( min(cost + dist_to, cur_dist) )

    def update(self, inc_node, new_table):
        #set current info to  incoming
        self.table.loc[inc_node] = new_table.loc[inc_node]
        #update info
        for c in df.columns:
            test_node.table.loc[self.id, c] = self.dist(c, inc_node)
            
        

if __name__ == "__main__":
    name = "w"
    df = pd.read_csv("./w.csv")

    test_node = Node(name, df)
    print(test_node.table)

    name2 = "x"
    df2 = pd.read_csv("./x.csv")

    test_node2 = Node(name2, df2)
    test_node.update("x", test_node2.table)
    print("-"*8)
    
    print(test_node.table)

    print(test_node2.table)


    