import cloudscraper
from bs4 import BeautifulSoup
import pymysql
import time
import re
from dotenv import load_dotenv

load_dotenv()

scraper = cloudscraper.create_scraper()

##################
BASE = "https://www.unegui.mn"
LIST_URL = BASE + "/l-hdlh/l-hdlh-zarna/oron-suuts-zarna/"
API_ITEM_URL = BASE + "/api/items/{}/"

import os
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "charset": "utf8mb4",
}

##################

def get_connection():
    return pymysql.connect(**DB_CONFIG)


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS unegui_zar (
                id            BIGINT PRIMARY KEY,
                title         TEXT,
                une           BIGINT,
                duureg        VARCHAR(100),
                khoroo        VARCHAR(100),
                bairshil      VARCHAR(200),
                latitude      DOUBLE,
                longitude     DOUBLE,
                uruu_too      INT,
                ashiglalt_year INT,
                barilgiin_dawhar VARCHAR(50),
                heden_dawhar  VARCHAR(50),
                hemjee        FLOAT,
                tsonh_too     VARCHAR(50),
                created_dt    VARCHAR(100)
            ) CHARACTER SET utf8mb4;
        """)
    conn.commit()


def insert_row(conn, row):
    sql = """
        INSERT IGNORE INTO unegui_zar
            (id, title, une, duureg, khoroo, bairshil, latitude, longitude,
             uruu_too, ashiglalt_year, barilgiin_dawhar, heden_dawhar,
             hemjee, tsonh_too, created_dt)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        cur.execute(sql, (
            row["id"], row["title"], row["une"],
            row["duureg"], row["khoroo"], row["bairshil"],
            row["latitude"], row["longitude"],
            row["uruu_too"],
            row["ashiglalt_year"], row["barilgiin_dawhar"],
            row["heden_dawhar"], row["hemjee"],
            row["tsonh_too"], row["created_dt"],
        ))
    conn.commit()


###################

def get_ids(page_num):
    r = scraper.get(LIST_URL, params={"page": page_num})
    soup = BeautifulSoup(r.text, "html.parser")

    ids = []
    seen = set()
    for a in soup.find_all("a", href=True):
        match = re.search(r"/adv/(\d+)_", a["href"])
        if match:
            ann_id = match.group(1)
            if ann_id not in seen:
                seen.add(ann_id)
                ids.append(ann_id)
    return ids


def get_detail(ann_id):
    r = scraper.get(API_ITEM_URL.format(ann_id))
    if r.status_code != 200:
        return None

    d = r.json()
    attrs = d.get("attrs", {})

    # Байршил: detail хуудасны address class-аас авах
    duureg, khoroo, bairshil = None, None, None
    slug = d.get("slug", "")
    if slug:
        page_r = scraper.get(BASE + "/adv/{}_{}/".format(ann_id, slug))
        if page_r.status_code == 200:
            # address span: "Сонгинохайрхан, Сонгинохайрхан, Хороо 29"
            addr_match = re.search(r'class="address"[^>]*>(.*?)</span>', page_r.text, re.DOTALL)
            if addr_match:
                addr = addr_match.group(1).strip()
                parts = [p.strip() for p in addr.split(",")]
                if len(parts) >= 1:
                    duureg = parts[0]
                if len(parts) >= 3:
                    raw = parts[2]  # "Хороо 29" эсвэл "Яармаг" г.м.
                    m = re.search(r"(\d+)", raw)
                    if "Хороо" in raw and m:
                        khoroo = m.group(1) + "-р хороо"
                    else:
                        bairshil = raw
            else:
                # map-location fallback
                loc_match = re.search(
                    r'map-location[^>]+>.*?<span[^>]+>.*?</span>(.*?)</div>',
                    page_r.text, re.DOTALL
                )
                if loc_match:
                    loc_parts = [p.strip() for p in loc_match.group(1).strip().split("—")]
                    if len(loc_parts) >= 2:
                        duureg = loc_parts[1]
                    if len(loc_parts) >= 3:
                        raw = loc_parts[2]
                        if re.match(r"^\d+-р хороо$", raw):
                            khoroo = raw
                        else:
                            bairshil = raw

    coords = d.get("coordinates") or {}

    # Өрөөний тоо breadcrumbs-аас авах ("1 өрөө", "2 өрөө" г.м.)
    uruu_too = None
    for bc in d.get("breadcrumbs", []):
        m = re.search(r"(\d+)\+?\s*өрөө", bc.get("name", ""))
        if m:
            uruu_too = int(m.group(1))
            break

    return {
        "id": d.get("id"),
        "title": d.get("title"),
        "une": d.get("price"),
        "duureg": duureg,
        "khoroo": khoroo,
        "bairshil": bairshil,
        "latitude": coords.get("latitude"),
        "longitude": coords.get("longitude"),
        "uruu_too": uruu_too,
        "ashiglalt_year": attrs.get("attrs__ashon"),
        "barilgiin_dawhar": attrs.get("attrs__davhar"),
        "heden_dawhar": attrs.get("attrs__davhar1"),
        "hemjee": attrs.get("attrs__talbai"),
        "tsonh_too": attrs.get("attrs__tsonhtoo"),
        "created_dt": d.get("created_dt"),
    }


################################

def get_total_pages():
    r = scraper.get(LIST_URL, params={"page": 1})
    soup = BeautifulSoup(r.text, "html.parser")
    pages = soup.find_all("a", class_="page-number")
    nums = [int(p.get_text(strip=True)) for p in pages if p.get_text(strip=True).isdigit()]
    return max(nums) if nums else 9999


def get_existing_ids(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM unegui_zar")
        return set(row[0] for row in cur.fetchall())


def scrape(max_pages=None):
    conn = get_connection()
    create_table(conn)

    if max_pages is None:
        max_pages = get_total_pages()
        print(f"Total {max_pages} pages found")

    # DB-д байгаа ID-уудыг санах
    existing_ids = get_existing_ids(conn)
    print(f"Existing IDs in DB: {len(existing_ids)}")

    total_inserted = 0

    for page in range(1, max_pages + 1):
        ids = get_ids(page)
        print(f"Page {page}/{max_pages}: {len(ids)} ads")

        new_ids = [aid for aid in ids if int(aid) not in existing_ids]

        # Хуудасны бүх ID давтагдсан бол зогсоох
        if len(new_ids) == 0:
            print(f"  -> All IDs already exist, stopping.")
            break

        for ann_id in new_ids:
            detail = get_detail(ann_id)
            if detail:
                insert_row(conn, detail)
                existing_ids.add(int(ann_id))
                total_inserted += 1
            time.sleep(0.5)

        print(f"  -> Total inserted: {total_inserted}")

    conn.close()
    print(f"Done! {total_inserted} rows saved to MySQL.")


if __name__ == "__main__":
    scrape(max_pages=None)
