import pandas as pd

file_path='twcs.csv'
output_path='apple_support_data.csv'
chunk_size=10000

apple_tweets=[]

for chunk in pd.read_csv(file_path,chunksize=chunk_size):
    apple_chunk=chunk[(chunk['author_id']=='AppleSupport') |(chunk['text'].str.contains('@AppleSupport',na=False,case=False))]

    apple_tweets.append(apple_chunk)

df_apple=pd.concat(apple_tweets)

df_apple.to_csv(output_path,index=False)

print(f"filtered {len(df_apple)} tweets and saved in {output_path} ")