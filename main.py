import flet as ft
import sqlite3
import os
import asyncio
from datetime import datetime

# --- VERİTABANI AYARLARI (GARANTİ YOL) ---
def get_db():
    # Telefonun yazma izni olan klasörü bulur
    path = os.path.join(os.getcwd(), "enes_otoyikama.db")
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
                   (tarih TEXT PRIMARY KEY, araba_sayisi INTEGER, fiyat REAL, eleman REAL, masraf REAL)''')
    conn.commit()
    return conn

db = get_db()

async def main(page: ft.Page):
    # Uygulama açılış ayarları
    page.title = "Enes Oto Yıkama"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    
    # 5 Saniyelik gecikmeyi önlemek için sayfa yenileme optimizasyonu
    page.browser_context_menu = ft.BrowserContextMenuMode.HIDDEN

    # --- HIZLI GİRİŞ FONKSİYONU ---
    async def giris_yap(e):
        if sifre_kutusu.value == "oto05":
            await ana_ekran_yukle()
        else:
            sifre_kutusu.error_text = "Hatalı Şifre!"
            await page.update_async()

    # --- ANA EKRAN (HIZLI YÜKLENEN) ---
    async def ana_ekran_yukle():
        page.controls.clear()
        
        # Basit bir sayaç ve giriş alanı örneği
        araba_sayisi = ft.TextField(label="Araba Sayısı", value="0", keyboard_type=ft.KeyboardType.NUMBER)
        
        async def kaydet_btn(e):
            # Tıklama anında görsel tepki (Hemen tepki vermesi için)
            e.control.disabled = True
            e.control.text = "Kaydediliyor..."
            await e.control.update_async()
            
            try:
                # Veritabanı işlemini arka planda (async) yap
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor = db.cursor()
                cursor.execute("INSERT OR REPLACE INTO kayitlar (tarih, araba_sayisi) VALUES (?, ?)", 
                             (tarih, araba_sayisi.value))
                db.commit()
                
                # Başarı mesajı
                page.snack_bar = ft.SnackBar(ft.Text("Kayıt Başarılı!"))
                page.snack_bar.open = True
            except Exception as ex:
                print(f"Hata: {ex}")
            
            e.control.disabled = False
            e.control.text = "Kaydet"
            await page.update_async()

        page.add(
            ft.Text("Enes Oto Yıkama Takip", size=25, weight="bold"),
            araba_sayisi,
            ft.ElevatedButton("Kaydet", on_click=kaydet_btn, bgcolor="blue", color="white")
        )
        await page.update_async()

    # --- İLK AÇILIŞ EKRANI (ŞİFRE) ---
    sifre_kutusu = ft.TextField(label="Şifre Giriniz", password=True, can_reveal_password=True)
    page.add(
        ft.Column([
            ft.Icon(ft.icons.CAR_REPAIR, size=50, color="blue"),
            ft.Text("Dükkan Yönetimi v2.0", size=20),
            sifre_kutusu,
            ft.ElevatedButton("Giriş Yap", on_click=giris_yap, width=200)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    
    await page.update_async()

# Web ve Mobil uyumluluğu için
if __name__ == "__main__":
    ft.app(target=main)
