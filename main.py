import flet as ft
import sqlite3
import os
from datetime import datetime, timedelta

# --- VERİTABANI ---
if os.name == "nt":
    db_path = os.path.join(os.path.expanduser("~"), "otoyikama_clean.db")
else:
    db_path = os.path.join(os.path.expanduser("~"), "otoyikama_clean.db")

def get_db():
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kayitlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT,
            secilen_gun TEXT UNIQUE,
            arac_sayi INTEGER,
            gelir INTEGER,
            eleman INTEGER,
            malzeme INTEGER,
            net_gelir INTEGER
        )
    """)
    conn.commit()
    return conn

db = get_db()

# --- GLOBAL DEĞİŞKENLER ---
global_arac_sayi = 0
global_toplam_gelir = 0
secilen_gun = ""

def main(page: ft.Page):
    global global_arac_sayi, global_toplam_gelir, secilen_gun
    page.title = "Enes Oto Yıkama"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 500
    page.window_height = 700

    # --- GİRİŞ EKRANI ---
    sifre_input = ft.TextField(label="Şifre", password=True, width=250)

    def giris_yap(e):
        if sifre_input.value == "oto05":
            page.controls.clear()
            ajanda_ekrani()
        else:
            sifre_input.error_text = "Hatalı Şifre!"
            page.update()

    page.add(
        ft.Column(
            [
                ft.Icon(ft.Icons.LOCK, size=60, color=ft.Colors.RED),
                ft.Text("SİSTEME GİR", size=24, weight=ft.FontWeight.BOLD),
                sifre_input,
                ft.ElevatedButton("GİRİŞ", width=250, on_click=giris_yap, bgcolor=ft.Colors.RED)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )

    # --- AJANDA EKRANI ---
    def ajanda_ekrani():
        global secilen_gun, global_arac_sayi, global_toplam_gelir
        page.controls.clear()
        secilen_gun = ""
        global_arac_sayi = 0
        global_toplam_gelir = 0

        today = datetime(2026, 2, 23)
        gun_sayisi = 60  # 2 ay
        gunler = [today + timedelta(days=i) for i in range(gun_sayisi)]

        gun_butonlari = []
        def gun_sec(e):
            global secilen_gun, global_arac_sayi, global_toplam_gelir
            secilen_gun = e.control.data
            cursor = db.cursor()
            cursor.execute("SELECT arac_sayi, eleman, malzeme FROM kayitlar WHERE secilen_gun=?", (secilen_gun,))
            row = cursor.fetchone()
            if row:
                global_arac_sayi, eleman_val, malzeme_val = row
            else:
                global_arac_sayi, eleman_val, malzeme_val = 0, 0, 0
            global_toplam_gelir = global_arac_sayi * 350
            hesap_ekrani(eleman_val, malzeme_val)

        for g in gunler:
            gun_str = g.strftime("%d/%m/%Y")
            gun_butonlari.append(ft.ElevatedButton(gun_str, data=gun_str, on_click=gun_sec, width=100, height=40))

        satirlar = []
        for i in range(0, len(gun_butonlari), 7):
            satirlar.append(ft.Row(gun_butonlari[i:i+7], spacing=5))

        page.add(
            ft.Column(
                [
                    ft.Text("AJANDA", size=30, color=ft.Colors.RED, weight=ft.FontWeight.BOLD),
                    *satirlar
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        page.update()

    # --- HESAP EKRANI ---
    def hesap_ekrani(eleman_val=0, malzeme_val=0):
        global global_arac_sayi, global_toplam_gelir, secilen_gun
        page.controls.clear()

        arac_display = ft.Text(str(global_arac_sayi), size=50, color=ft.Colors.GREEN)
        gelir_display = ft.Text(f"Toplam Gelir: {global_toplam_gelir}₺", size=20, color=ft.Colors.GREEN)
        net_gelir_display = ft.Text(f"Net Gelir: {global_toplam_gelir - (eleman_val + malzeme_val)}₺", size=20, color=ft.Colors.YELLOW)

        # Araç butonları
        def arac_sec(e):
            global global_arac_sayi, global_toplam_gelir
            global_arac_sayi += int(e.control.data)
            global_toplam_gelir = global_arac_sayi * 350
            arac_display.value = str(global_arac_sayi)
            gelir_display.value = f"Toplam Gelir: {global_toplam_gelir}₺"
            net_gelir_guncelle()
            otomatik_kayit()
            page.update()

        butonlar = []
        for i in range(1, 15):
            butonlar.append(ft.ElevatedButton(str(i), data=str(i), on_click=arac_sec,
                                               bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, width=50, height=50))
        ust_satir = ft.Row(butonlar[:7], spacing=10)
        alt_satir = ft.Row(butonlar[7:], spacing=10)

        # Giderler
        eleman_input = ft.TextField(label="ELEMAN", value=str(eleman_val), width=100, keyboard_type=ft.KeyboardType.NUMBER)
        malzeme_input = ft.TextField(label="MALZEME", value=str(malzeme_val), width=100, keyboard_type=ft.KeyboardType.NUMBER)

        def net_gelir_guncelle(e=None):
            try:
                eleman = int(eleman_input.value)
            except:
                eleman = 0
            try:
                malzeme = int(malzeme_input.value)
            except:
                malzeme = 0
            net = global_toplam_gelir - (eleman + malzeme)
            net_gelir_display.value = f"Net Gelir: {net}₺"
            otomatik_kayit()
            page.update()

        eleman_input.on_change = net_gelir_guncelle
        malzeme_input.on_change = net_gelir_guncelle

        # Otomatik kayıt (UPSERT)
        def otomatik_kayit():
            try:
                if secilen_gun == "":
                    return
                tarih = datetime.now().strftime("%d/%m/%Y %H:%M")
                eleman = int(eleman_input.value)
                malzeme = int(malzeme_input.value)
                net = global_toplam_gelir - (eleman + malzeme)
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO kayitlar (tarih, secilen_gun, arac_sayi, gelir, eleman, malzeme, net_gelir)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(secilen_gun) DO UPDATE SET
                        tarih=excluded.tarih,
                        arac_sayi=excluded.arac_sayi,
                        gelir=excluded.gelir,
                        eleman=excluded.eleman,
                        malzeme=excluded.malzeme,
                        net_gelir=excluded.net_gelir
                """, (tarih, secilen_gun, global_arac_sayi, global_toplam_gelir, eleman, malzeme, net))
                db.commit()
            except Exception as ex:
                print("Otomatik kayıt hatası:", ex)

        geri_btn = ft.ElevatedButton("← Ajanda", on_click=lambda e: ajanda_ekrani(), bgcolor=ft.Colors.RED)

        page.add(
            ft.Column(
                [
                    ft.Row([geri_btn]),
                    ft.Text(f"HESAP ({secilen_gun})", size=30, color=ft.Colors.RED, weight=ft.FontWeight.BOLD),
                    arac_display,
                    ust_satir,
                    alt_satir,
                    gelir_display,
                    ft.Row([eleman_input, malzeme_input], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                    net_gelir_display
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        page.update()

ft.app(target=main)
