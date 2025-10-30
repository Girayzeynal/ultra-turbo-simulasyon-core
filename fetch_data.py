# fetch_data.py
# Çift Katmanlı Veri Toplama: SofaScore (+form/sakatlık) + Flashscore (skor/odds) → CSV
# Not: Bu endpoint'ler "resmi" değildir; değişirse try/except ile düşmeyiz.

import os, json, time, re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.parser import parse as dtparse
from rapidfuzz import process, fuzz

ALIAS_PATH = os.environ.get("ALIAS_PATH", "team_aliases.csv")
OUT_CSV    = os.environ.get("FAZ1_IN_CSV", "euroleague_faz1.csv")
UA = {"User-Agent": "Mozilla/5.0 (MK-Ultra/1.0)"}

# --- Yardımcılar -------------------------------------------------------------

def load_aliases():
    if not os.path.exists(ALIAS_PATH):
        return {}
    df = pd.read_csv(ALIAS_PATH)
    mp = {}
    for _, r in df.iterrows():
        mp[str(r["team_name"]).strip().upper()] = str(r["alias"]).strip().upper()
    return mp

def normalize_team(name:str, aliases:dict):
    base = str(name).strip().upper()
    # doğrudan eşleşme
    if base in aliases: return aliases[base]
    # fuzzy eşleşme
    cand, score, _ = process.extractOne(base, aliases.keys(), scorer=fuzz.WRatio)
    return aliases[cand] if score >= 80 else base

def coerce_date(s):
    if isinstance(s, (datetime, )):
        return s.date().isoformat()
    try:
        return dtparse(str(s)).date().isoformat()
    except Exception:
        return None

# --- SofaScore (form/sakatlık skoruna sinyal) --------------------------------
# UYARI: SofaScore'un internal endpoint yapısı değişebilir. Düşerse fetch_s sofascore try/except None döner.

def fetch_sofascore_round(date_from:str, date_to:str):
    # Basit yaklaşım: günlük Euroleague maç listesini turnuva id üzerinden çekmeye çalış (id sabit olmayabilir!).
    # Eğer başarısız olursa boş döneriz; Combined Fetcher Flashscore’dan skorları toplar.
    results = []
    start = dtparse(date_from).date()
    end   = dtparse(date_to).date()
    day = start
    # Bu id örnektir; değişirse None döneriz. (Sofascore unique-tournament id’si sıklıkla 9924/113 olarak geçer)
    tournament_ids = [113, 9924]
    while day <= end:
        ds = day.isoformat()
        ok = False
        for tid in tournament_ids:
            url = f"https://api.sofascore.com/api/v1/unique-tournament/{tid}/events/{ds}"
            try:
                r = requests.get(url, headers=UA, timeout=10)
                if r.status_code != 200:
                    continue
                data = r.json().get("events", [])
                for ev in data:
                    if ev.get("tournament", {}).get("name", "").lower().find("euroleague") == -1:
                        continue
                    home = ev["homeTeam"]["name"]
                    away = ev["awayTeam"]["name"]
                    sc   = ev.get("homeScore", {}).get("current"), ev.get("awayScore", {}).get("current")
                    results.append({
                        "date": ds,
                        "home_team": home, "away_team": away,
                        "home_score": sc[0], "away_score": sc[1],
                        "source": "sofascore"
                    })
                ok = True
                break
            except Exception:
                continue
        # Gün bazında en az 1 sonuç toplamayı dener, sonra diğer güne geçer
        day += timedelta(days=1)
    return results

# --- Flashscore (skor/odds baseline) -----------------------------------------
def fetch_flashscore_scores(date_from:str, date_to:str):
    # Flashscore HTML yapısı sık değişir; en sade yaklaşım:
    # “basketball/europe/euroleague” günlük sayfasından kartları parse etmeyi dener.
    # Tarayıcı kimliği ile 1-2 istek yapıyoruz.
    results = []
    start = dtparse(date_from).date()
    end   = dtparse(date_to).date()
    day = start
    while day <= end:
        ds = day.strftime("%Y-%m-%d")
        # Tipik lig sayfası (örnek pattern): https://www.flashscore.com/basketball/europe/euroleague/results/?d=2024-10-15
        url = f"https://www.flashscore.com/basketball/europe/euroleague/results/?d={ds}"
        try:
            html = requests.get(url, headers=UA, timeout=10).text
            soup = BeautifulSoup(html, "lxml")
            # Basit seçim: maç satırları için "event__match" vb. sınıflar
            for row in soup.select(".event__match"):
                home = row.select_one(".event__participant--home")
                away = row.select_one(".event__participant--away")
                score = row.select_one(".event__scores")
                if not (home and away and score): 
                    continue
                # skor "82:77" gibi
                m = re.search(r"(\d+)\s*[:\-]\s*(\d+)", score.get_text(strip=True))
                if not m: 
                    continue
                hs, as_ = int(m.group(1)), int(m.group(2))
                results.append({
                    "date": ds,
                    "home_team": home.get_text(strip=True),
                    "away_team": away.get_text(strip=True),
                    "home_score": hs, "away_score": as_,
                    "source": "flashscore"
                })
        except Exception:
            # engel/captcha vb. durumda boş bırak
            pass
        day += timedelta(days=1)
    return results

# --- Combine -----------------------------------------------------------------
def combine_sources(sofa_list, flash_list):
    # Önce skor doğrulama: mümkünse flashscore skoru öncelik, sofascore boşları doldurur.
    df_s = pd.DataFrame(sofa_list) if sofa_list else pd.DataFrame(columns=["date","home_team","away_team","home_score","away_score","source"])
    df_f = pd.DataFrame(flash_list) if flash_list else pd.DataFrame(columns=["date","home_team","away_team","home_score","away_score","source"])
    if df_s.empty and df_f.empty:
        return pd.DataFrame(columns=["date","home_team","away_team","home_score","away_score","source"])
    # takım isimlerini normalize etme
    aliases = load_aliases()
    for df in [df_s, df_f]:
        if not df.empty:
            df["date"] = df["date"].apply(coerce_date)
            df["home_team_norm"] = df["home_team"].apply(lambda x: normalize_team(x, aliases))
            df["away_team_norm"] = df["away_team"].apply(lambda x: normalize_team(x, aliases))
    # merge (aynı gün, aynı eşleşme)
    key = ["date","home_team_norm","away_team_norm"]
    merged = pd.merge(df_f, df_s, on=key, how="outer", suffixes=("_f","_s"))
    out = []
    for _, r in merged.iterrows():
        date = r["date"]
        ht = r.get("home_team_norm") or r.get("home_team_norm")
        at = r.get("away_team_norm") or r.get("away_team_norm")
        # skor önceliği: flashscore > sofascore
        hs = r.get("home_score_f") if pd.notna(r.get("home_score_f")) else r.get("home_score_s")
        as_ = r.get("away_score_f") if pd.notna(r.get("away_score_f")) else r.get("away_score_s")
        if pd.isna(hs) or pd.isna(as_):
            continue
        out.append({
            "season":"2024-25",
            "week": None,  # FAZ1 pipeline week kolonunu doldurmazsa tarih bazlı işler; istersen mapping ekleriz.
            "date": date,
            "home_team": ht,
            "away_team": at,
            "home_score": int(hs),
            "away_score": int(as_),
            # eFG/TOV/ORB/FTr opsiyonel, boş bırakıyoruz → FAZ1 kendi normalize akışını çalıştırır
            "home_eFG":"", "away_eFG":"", "home_TOVp":"", "away_TOVp":"", "home_ORBp":"", "away_ORBp":"", "home_FTr":"", "away_FTr":"",
            "home_rest_days":"", "away_rest_days":"",
            "home_travel_km":"", "away_travel_km":"",
            "injuries_home":"", "injuries_away":"",
            "book_line_home":"", "closing_total":"", "home_odds":"", "away_odds":""
        })
    return pd.DataFrame(out)

def save_csv(df, path):
    cols = [
        "season","week","date","home_team","away_team","home_score","away_score",
        "possessions","pace","home_eFG","away_eFG","home_TOVp","away_TOVp",
        "home_ORBp","away_ORBp","home_FTr","away_FTr",
        "home_rest_days","away_rest_days","home_travel_km","away_travel_km",
        "injuries_home","injuries_away","book_line_home","closing_total","home_odds","away_odds"
    ]
    # opsiyonelleri ekle
    for c in ["possessions","pace","home_eFG","away_eFG","home_TOVp","away_TOVp","home_ORBp","away_ORBp","home_FTr","away_FTr","home_rest_days","away_rest_days","home_travel_km","away_travel_km","injuries_home","injuries_away","book_line_home","closing_total","home_odds","away_odds"]:
        if c not in df.columns:
            df[c] = ""
    df = df[cols]
    df.to_csv(path, index=False)

def fetch_and_build(date_from:str, date_to:str):
    sofas = fetch_sofascore_round(date_from, date_to)
    flash = fetch_flashscore_scores(date_from, date_to)
    df = combine_sources(sofas, flash)
    if df.empty:
        return False, "Kaynaklardan veri toplanamadı."
    save_csv(df, OUT_CSV)
    return True, f"Yazıldı: {OUT_CSV} | Kayıt: {len(df)}"

if __name__ == "__main__":
    d1 = os.environ.get("FETCH_FROM")
    d2 = os.environ.get("FETCH_TO")
    if not (d1 and d2):
        print("Kullanım: FETCH_FROM=YYYY-MM-DD FETCH_TO=YYYY-MM-DD python fetch_data.py")
    else:
        ok, msg = fetch_and_build(d1, d2)
        print(("OK: " if ok else "ERR: ") + msg)
