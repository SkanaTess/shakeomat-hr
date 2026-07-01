import json, os, urllib.request, urllib.parse
try:
    os.remove("/opt/ava/posted_days.json")
except OSError:
    pass
tok = ""
for ln in open("/opt/ava/.env"):
    if ln.startswith("TELEGRAM_BOT_TOKEN="):
        tok = ln.split("=", 1)[1].strip().strip('"').strip("'")
        break
rec = {
    "datum_objave": "2026-07-01",
    "naslov": "Više proteina = više mišića? NE.",
    "verdikt": "WINNER", "score": 88, "asset_status": "spreman",
    "fajl": "kinetic_0_A3_ivan_vise",
    "caption": ("Više proteina = više mišića? Ne.\n\n"
                "~20–40 g po obroku je otprilike maksimum koji tijelo iskoristi za izgradnju. Višak ne gradi više — samo prođe.\n\n"
                "Optimalno, ne natrpano. Tijelo nije skladište.\n\n"
                "Pošalji ovo nekome tko trpa tri mjerice u svaki shake.\n\n"
                "Nije lijek. Nije magic. Je besramno dobar shake."),
    "hashtags": "#shakeomat #nemorasznati #protein #besramnodobar",
    "video_url": "https://shakeomat.hr/social/kinetic_0_A3_ivan_vise.mp4",
}
json.dump(rec, open("/opt/ava/content_today.json", "w"), ensure_ascii=False)
text = ("🥤 DANAŠNJI POST — WINNER 88/100\n" + rec["naslov"] + "\n\n"
        + rec["caption"][:380] + "\n\n" + rec["hashtags"])
mk = {"inline_keyboard": [[
    {"text": "✅ Objavi", "callback_data": "pub:go"},
    {"text": "🗑 Kill", "callback_data": "pub:kill"},
]]}
data = urllib.parse.urlencode({
    "chat_id": "8778896044", "text": text,
    "reply_markup": json.dumps(mk), "disable_web_page_preview": "true",
}).encode()
try:
    vid = urllib.request.urlopen(rec["video_url"], timeout=15).status
except Exception as e:
    vid = "ERR:" + repr(e)[:40]
try:
    r = urllib.request.urlopen("https://api.telegram.org/bot" + tok + "/sendMessage", data=data, timeout=20)
    print("tok_len", len(tok), "| video", vid, "| resp", r.read().decode()[:180])
except Exception as e:
    print("tok_len", len(tok), "| video", vid, "| SEND ERROR", repr(e)[:200])
