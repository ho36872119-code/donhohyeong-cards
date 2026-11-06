#!/usr/bin/env python3
"""인스타그램 캐러셀 게시 (통합 로그인 시스템 사용자 토큰, graph.facebook.com)
사용법: IG_TOKEN=... IG_USER_ID=... python3 ig_publish.py caption.txt URL1 URL2 ...
"""
import json, os, sys, time, urllib.parse, urllib.request

API = "https://graph.facebook.com/v23.0"
TOKEN, UID = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{API}/{path}?{data.decode()}")
    else:
        req = urllib.request.Request(f"{API}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API 오류 {path}: {e.read().decode()[:500]}")


def wait_ready(cid, label):
    for _ in range(30):
        st = call("GET", cid, fields="status_code,status").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"{label} 처리 실패: {st}")
        time.sleep(4)
    sys.exit(f"{label} 처리 시간 초과")


def main(caption_file, urls):
    caption = open(caption_file, encoding="utf-8").read().strip()
    if not 2 <= len(urls) <= 10:
        sys.exit("캐러셀은 2~10장이어야 해요")
    kids = []
    for i, u in enumerate(urls, 1):
        cid = call("POST", f"{UID}/media", image_url=u, is_carousel_item="true")["id"]
        wait_ready(cid, f"{i}번 이미지")
        kids.append(cid)
        print(f"{i}번 이미지 준비 완료")
    car = call("POST", f"{UID}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)["id"]
    wait_ready(car, "캐러셀")
    mid = call("POST", f"{UID}/media_publish", creation_id=car)["id"]
    link = call("GET", mid, fields="permalink").get("permalink", "")
    print(f"게시 완료: media_id={mid} {link}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
