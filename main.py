import flet as ft
import sqlite3
from datetime import datetime, timedelta

# --- VERİTABANI ---
def veritabani_kur():
    conn = sqlite3.connect("enes_otoyikama.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                   (tarih TEXT PRIMARY KEY, araba_sayisi INTEGER, fiyat REAL, eleman REAL, masraf REAL)''')
    conn.commit()
    return conn

def main(page: ft.Page):
    # --- PENCERE BOYUTLANDIRMA ---
    page.window.width = 400
    page.window.height = 800
    page.window.resizable = False
    
    page.title = "Enes Oto Yıkama"
    page.theme_mode = "dark"
    page.scroll = "auto"
    
    db = veritabani_kur()
    cur = db.cursor()

    # --- EKRANLARI TANIMLA ---
    view_giris = ft.Column(visible=True, horizontal_alignment="center")
    view_takvim = ft.Column(visible=False)
    view_hesap = ft.Column(visible=False)

    # --- 1. GİRİŞ EKRANI ---
    def giris_yap(e):
        if sifre_kutusu.value == "oto05":
            view_giris.visible = False
            view_takvim.visible = True
            page.update()
        else:
            sifre_kutusu.error_text = "Şifre Yanlış!"
            page.update()

    sifre_kutusu = ft.TextField(
        label="Giriş Şifresi", 
        password=True, 
        can_reveal_password=True,
        text_align="center",
        hint_text="", 
        on_submit=giris_yap
    )
    
    view_giris.controls = [
        ft.Container(height=100),
        ft.Text("ADMİN GİRİŞİ", size=30, weight="bold", color="blue"),
        ft.Divider(height=20, color="transparent"),
        sifre_kutusu,
        ft.ElevatedButton(
            content=ft.Text("GİRİŞ YAP"),
            on_click=giris_yap,
            width=200,
            height=50
        )
    ]

    # --- 2. TAKVİM EKRANI ---
    takvim_liste = ft.Column(spacing=10)
    baslangic = datetime(2026, 2, 22)
    bitis = datetime(2027, 12, 31)
    gun_sayisi = (bitis - baslangic).days + 1

    def tarih_sec(t_str):
        hesap_ekrani_kur(t_str)
        view_takvim.visible = False
        view_hesap.visible = True
        page.update()

    for i in range(gun_sayisi):
        t_obj = baslangic + timedelta(days=i)
        t_str = t_obj.strftime("%d-%m-%Y")
        takvim_liste.controls.append(
            ft.Container(
                content=ft.Text(t_str, size=18, weight="bold"),
                padding=20, bgcolor="white10", border_radius=12,
                on_click=lambda e, t=t_str: tarih_sec(t)
            )
        )

    view_takvim.controls = [
        ft.Text("AJANDA", size=25, color="red", weight="bold"),
        ft.Divider(),
        takvim_liste
    ]

    # --- 3. HESAP EKRANI ---
    def hesap_ekrani_kur(secili_tarih):
        view_hesap.controls.clear()
        cur.execute("SELECT * FROM kayitlar WHERE tarih=?", (secili_tarih,))
        data = cur.fetchone()
        
        v = {
            "sayi": data[1] if data else 0,
            "fiyat": data[2] if data else 350,
            "eleman": data[3] if data else 0,
            "masraf": data[4] if data else 0
        }

        sayac_text = ft.Text(f"Yıkanan: {v['sayi']}", size=20, weight="bold")
        gider_toplam_text = ft.Text("Toplam Gider: 0 TL", color="orange", size=18)
        net_text = ft.Text(size=25, weight="bold")

        def kaydet(e=None):
            try:
                f = float(f_in.value) if f_in.value else 0
                el = float(el_in.value) if el_in.value else 0
                ms = float(ms_in.value) if ms_in.value else 0
                gider = el + ms
                ciro = v["sayi"] * f
                net = ciro - gider
                
                sayac_text.value = f"Yıkanan Araç: {v['sayi']}"
                gider_toplam_text.value = f"Toplam Gider: {gider:,.0f} TL"
                net_text.value = f"NET: {net:,.0f} TL"
                net_text.color = "green" if net >= 0 else "red"
                
                cur.execute("INSERT OR REPLACE INTO kayitlar VALUES (?, ?, ?, ?, ?)", 
                           (secili_tarih, v["sayi"], f, el, ms))
                db.commit()
                page.update()
            except: pass

        f_in = ft.TextField(label="Birim Fiyat", value=str(v["fiyat"]), on_change=kaydet)
        el_in = ft.TextField(label="Eleman Ödemesi", value=str(v["eleman"]), on_change=kaydet)
        ms_in = ft.TextField(label="Dükkan Masrafı", value=str(v["masraf"]), on_change=kaydet)

        def kutu_islem(e, idx):
            if e.control.bgcolor == "red":
                e.control.bgcolor = "green"
                v["sayi"] += 1
                e.control.content.value = str(v["sayi"])
            else:
                e.control.bgcolor = "red"
                v["sayi"] -= 1
                e.control.content.value = ""
            kaydet()
            e.control.update()

        grid = ft.Row(wrap=True, spacing=10)
        for i in range(20):
            renk = "green" if i < v["sayi"] else "red"
            txt = str(i+1) if i < v["sayi"] else ""
            grid.controls.append(
                ft.Container(
                    content=ft.Text(txt, weight="bold"),
                    width=65, height=65, 
                    bgcolor=renk, 
                    border_radius=10,
                    # Hata veren alignment satırı tamamen silindi.
                    on_click=lambda e, idx=i: kutu_islem(e, idx)
                )
            )

        view_hesap.controls = [
            ft.ElevatedButton(content=ft.Text("GERİ DÖN"), on_click=lambda _: geri_don()),
            ft.Text(secili_tarih, size=28, color="red", weight="bold"),
            f_in,
            grid,
            sayac_text,
            ft.Divider(),
            el_in, ms_in, gider_toplam_text,
            ft.Container(content=net_text, padding=15, bgcolor="white10", border_radius=10)
        ]
        kaydet()

    def geri_don():
        view_hesap.visible = False
        view_takvim.visible = True
        page.update()

    page.add(view_giris, view_takvim, view_hesap)

ft.app(target=main)