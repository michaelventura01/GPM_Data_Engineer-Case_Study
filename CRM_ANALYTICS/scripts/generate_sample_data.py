import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Create data directory
os.makedirs('data', exist_ok=True)

# Set random seed
np.random.seed(42)
random.seed(42)

print("Generating sample CRM data...")

# Generate 1000 deals
num_deals = 1000
deals = []

for i in range(num_deals):
    deal = {
        'ID': i + 1,
        'Title': f'Deal {i+1}',
        'Value': round(np.random.exponential(5000), 2) if random.random() > 0.5 else 0,
        'Org ID': random.choice([11,12,13,14,15,16,17,474]),
        'Stage ID': random.choice([110,111,112,113,114,115,134,135]),
        'Currency': 'USD',
        'Add time': datetime.now() - timedelta(days=random.randint(1, 365)),
        'Update time': datetime.now(),
        'Status': np.random.choice(['won', 'lost', 'open'],p=[0.3, 0.3, 0.4]
),
        'Lost reason': random.choice([None, 'Price', 'Competitor', 'Timing']),
        'Close time': datetime.now() if random.random() > 0.4 else None,
        'Pipeline ID': 19,
        'Won time': datetime.now() if random.random() > 0.7 else None,
        'Lost time': datetime.now() if random.random() > 0.7 else None,
        'Stage change time': datetime.now(),
        'Is deleted': False
    }
    deals.append(deal)

df_deals = pd.DataFrame(deals)
df_deals.to_csv('data/deals.csv', index=False)
print(f">> Generated {len(df_deals)} deals")

# Generate activities
num_activities = 3000
activities = []

for i in range(num_activities):
    activity = {
        'ID': i + 1,
        'Subject': random.choice(['Call', 'Email', 'Meeting']),
        'Is deleted': False,
        'Add time': datetime.now() - timedelta(days=random.randint(1, 180)),
        'Update time': datetime.now(),
        'Deal ID': random.randint(1, num_deals),
        'Org ID': random.choice([11,12,13,14,15,16,17,474]),
        'Done': random.choice([True, False]),
        'Marked as done time': datetime.now() if random.random() > 0.3 else None,
        'Due Datetime': datetime.now() + timedelta(days=random.randint(-30, 30)),
        'Duration (Hours)': round(random.uniform(0, 2), 2),
        'Duration (Minutes)': random.randint(0, 120)
    }
    activities.append(activity)

df_activities = pd.DataFrame(activities)
df_activities.to_csv('data/activities.csv', index=False)
print(f">> Generated {len(df_activities)} activities")

# Generate stages
stages = [
    [110, "Lead In", 1, 19, 5, 1.0, False],
    [111, "Contact Made", 2, 19, 15, 2.0, False],
    [112, "Qualified", 3, 19, 35, 3.0, False],
    [113, "Proposal", 4, 19, 55, 4.0, False],
    [114, "Negotiation", 5, 19, 75, 5.0, False],
    [115, "Closed Won", 6, 19, 100, None, False],
    [134, "Closed Lost", 7, 19, 0, None, False],
]

df_stages = pd.DataFrame(stages, columns=['ID', 'Name', 'Order nr', 'Pipeline ID', 'Deal probability', 'Days to rotten', 'Is deleted'])
df_stages.to_csv('data/stages.csv', index=False)
print(f">> Generated {len(df_stages)} stages")

# Generate pipeline
pipeline = [[19, "General Inquiry", False]]
df_pipeline = pd.DataFrame(pipeline, columns=['ID', 'Name', 'Is deleted'])
df_pipeline.to_csv('data/pipeline.csv', index=False)

# Generate organizations
orgs = [
    [11, "Silver Anchor Marina"],
    [12, "Driftwood Harbor"],
    [13, "Pelican Point Marina"],
    [474, "Harborview Marina"],
]
df_orgs = pd.DataFrame(orgs, columns=['ID', 'Name'])
df_orgs.to_csv('data/organizations.csv', index=False)

print("\n>>>> Sample data generation complete!")
print(f"Data saved to ./data/ directory")