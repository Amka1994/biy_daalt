# %%
import pandas as pd
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    charset="utf8mb4"
)

df = pd.read_sql("SELECT * FROM unegui_zar", conn)
conn.close()

print(df.head())


# %%
df.info()


# %%
df.duplicated(subset=['id']).sum()


#%%
print(df.isnull().sum())

df = df.dropna(subset=['latitude', 'longitude'])
print(df.isnull().sum())


#%%
pd.set_option("display.float_format", "{:,.0f}".format)
print(df['une'].describe())

df[df["une"] == df["une"].min()]

df = df[df["une"] > 20_000_000]

print(df['une'].describe())

# %%

print(df['uruu_too'].describe())
print(df['hemjee'].describe())

print(df[df["hemjee"] > 1000][["title", "hemjee", "une"]])
print(df[df["hemjee"] == 0][["title", "hemjee"]])

# Хэдэн буруу утга байна?
буруу = df[(df["hemjee"] <= 10) | (df["hemjee"] > 1000)]
print(f"Буруу утга: {len(буруу)} ({len(буруу)/len(df)*100:.1f}%)")


df = df[(df["hemjee"] > 10) & (df["hemjee"] <= 1000)]

print(df['hemjee'].describe())


#%%

print(df['ashiglalt_year'].describe())
#%%
print(df['barilgiin_dawhar'].describe())

df['barilgiin_dawhar'] = df["barilgiin_dawhar"].astype(int)

print(df['barilgiin_dawhar'].describe())

print(df[df["barilgiin_dawhar"] < 2])


#%%

df["created_dt"] = pd.to_datetime(df["created_dt"])
df["created_dt"] = df["created_dt"].dt.strftime("%Y-%m-%d")
print(df["created_dt"].head())


#%%

df["year"] = pd.to_datetime(df["created_dt"]).dt.year
print(df["year"].head())



#%%

df['mkv_dundaj_price'] = df['une'] / df['hemjee']
print(df['mkv_dundaj_price'].describe())


df[df["mkv_dundaj_price"] == df["mkv_dundaj_price"].min()]



Q1 = df["mkv_dundaj_price"].quantile(0.25)
Q3 = df["mkv_dundaj_price"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

print(f"Q1:             {Q1:,.0f}")
print(f"Q3:             {Q3:,.0f}")
print(f"IQR:            {IQR:,.0f}")
print(f"Доод хязгаар:   {lower:,.0f}")
print(f"Дээд хязгаар:   {upper:,.0f}")

# Outlier тоо
outliers = df[(df["mkv_dundaj_price"] < lower) | (df["mkv_dundaj_price"] > upper)]
print(f"\nOutlier тоо:    {len(outliers)}")
print(f"Нийт:           {len(df)}")
print(f"Хувь:           {len(outliers)/len(df)*100:.1f}%")

df = df[df["mkv_dundaj_price"] >= lower]

print(df['mkv_dundaj_price'].describe())


# %% cleaned_data table-д хадгалах
conn_clean = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    charset="utf8mb4"
)

clean_cols = ['une', 'duureg', 'khoroo', 'bairshil', 'horoolol',
              'latitude', 'longitude', 'uruu_too', 'ashiglalt_year',
              'barilgiin_dawhar', 'heden_dawhar', 'hemjee', 'tsonh_too', 'created_dt', 'year', 'mkv_dundaj_price']

df_clean = df[clean_cols].dropna(subset=['duureg']).copy()

with conn_clean.cursor() as cur:
    cur.execute("DROP TABLE IF EXISTS cleaned_data")
    cur.execute("""
        CREATE TABLE cleaned_data (
            une              BIGINT,
            duureg           VARCHAR(100),
            khoroo           VARCHAR(100),
            bairshil         VARCHAR(200),
            horoolol         VARCHAR(100),
            latitude         DOUBLE,
            longitude        DOUBLE,
            uruu_too         INT,
            ashiglalt_year   INT,
            barilgiin_dawhar INT,
            heden_dawhar     VARCHAR(50),
            hemjee           FLOAT,
            tsonh_too        VARCHAR(50),
            created_dt       VARCHAR(50),
            year             INT,
            mkv_dundaj_price FLOAT
        ) CHARACTER SET utf8mb4
    """)

rows_clean = [tuple(None if (isinstance(v, float) and pd.isna(v)) else v for v in row)
              for row in df_clean.itertuples(index=False)]

with conn_clean.cursor() as cur:
    cur.executemany("""
        INSERT INTO cleaned_data VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows_clean)

conn_clean.commit()

with conn_clean.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM cleaned_data")
    print("cleaned_data rows:", cur.fetchone()[0])

conn_clean.close()
