# scripts/inspect_panel.py
import pandas as pd

def main():
    # 1) load the parquet
    df = pd.read_parquet("data/panel.parquet")
    
    # 2) basic info
    print("DataFrame shape:", df.shape)
    print(df.info(), "\n")
    
    # 3) peek at the edges
    print("First 5 rows:\n", df.head(), "\n")
    print("Last 5 rows:\n", df.tail(), "\n")
    
    # 4) count non-null per column
    print("Non-null counts per contract:\n", df.count())

if __name__ == "__main__":
    main()
