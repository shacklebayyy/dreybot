import os
import pandas as pd

folder = r'c:\Users\shackle\Desktop\Django Water Management System\backend\old'
files = os.listdir(folder)

for f in files:
    if f.lower().endswith('.xls') or f.lower().endswith('.xlsx'):
        path = os.path.join(folder, f)
        try:
            df = pd.read_excel(path, engine='xlrd', nrows=3)
            print('---', f, '---')
            print(df.columns.tolist())
            print()
        except Exception as e:
            print('---', f, '--- Error:', e)
