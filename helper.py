import argparse
import json
import pandas as pd

def read_topology_file(filepath):
    with open(filepath,) as f:
        data = json.load(f)
        df = pd.DataFrame(
            index=[i for i in range(data['num_servers'])],
            columns=[i for i in range(data['num_servers'])]+['ip'],
        )
        neightbors = []
        for ix, (ip, cost) in enumerate(data['ip_costs'].items()):
            df.at[ix, 'ip'] = ip
            df.at[data['id'], ix] = cost
            if cost is not None and data['id'] != ix:
                neightbors += [ix]
        df.fillna(float('inf'), inplace=True)
        return df, neightbors

if __name__ == "__main__":
    # test function
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True, type=str, help='Initial topology file')
    args = parser.parse_args()
    df = read_topology_file(args.file)
    print(df)