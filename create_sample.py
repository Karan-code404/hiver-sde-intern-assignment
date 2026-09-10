import pandas as pd

df=pd.read_csv('apple_support_data.csv')

customer_tweets=df[df['inbound']==True]

sample_200=customer_tweets.sample(n=200,random_state=42)

sample_200['Intent']=""
sample_200['Ideal_Reply'] = ""
sample_200['Escalate_Yes_No'] = ""
sample_200['Escalate_Reason'] = ""

final_dataset = sample_200[['tweet_id', 'text', 'Intent', 'Ideal_Reply', 'Escalate_Yes_No', 'Escalate_Reason']]

final_dataset.to_csv('golden_dataset_empty.csv', index=False)

print("new small data set is ready")