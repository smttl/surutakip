# 🐄 Sürü Takip ve Yönetim Sistemi

Modern çiftlikler için geliştirilmiş; hayvan sağlığı, süt verimi, personel görev yönetimi ve finansal takibi tek bir noktadan yönetmenizi sağlayan **Flask tabanlı web uygulaması**.

Tamamen **mobil uyumlu** (responsive) tasarımı sayesinde ahırda, padokta veya ofiste kolayca kullanılabilir.

![Status](https://img.shields.io/badge/Durum-Aktif-success)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Özellikler

Bu sistem 4 farklı kullanıcı rolü (Admin, Sahip, Veteriner, Çalışan) üzerine kurulmuştur:

### 🏥 Sağlık ve Veteriner İşlemleri
* **Dijital Sağlık Karnesi:** Her hayvan için geçmiş muayene, tedavi ve ilaç kayıtları.
* **Aşı Takvimi:** Tekil veya toplu (padok bazlı) aşı planlama. Uygulama takibi ve not ekleme.
* **Gebelik Takibi:** Tohumlama tarihi, gebelik durumu (Gebe/Boş) ve listede görsel uyarılar.
* **Medya Yükleme:** Hasta hayvanlar için fotoğraf veya video yükleyerek dosya oluşturma.

### 📊 Çiftlik Yönetimi
* **Detaylı Sürü Takibi:** Küpe no, padok no (Sıra no), ırk, yaş (aylık), cinsiyet ve doğum sayısı takibi.
* **Akıbet Yönetimi:** Kesim, satış veya ölüm durumlarının arşivlenmesi ve aktif listeden düşülmesi.
* **Padok/Grup Sistemi:** Hayvanları padoklara ayırma, padoklara özel notlar ekleme.
* **Süt Takibi:** Günlük süt verimi girişi (Sadece sağmal hayvanlar için).

### 👷 Personel ve Görevler
* **Görev Atama:** Yönetimin çalışanlara özel görev ataması ve personelin "Tamamlandı" onayı vermesi.
* **Hastalık Bildirimi:** Çalışanların sahadan fotoğraf çekerek anlık acil durum bildirmesi.
* **Kısıtlı Yetki:** Çalışanlar sadece kendi görevlerini ve basit veri girişlerini görür, yönetim paneline erişemez.

### 📈 Raporlama (Patron Ekranı)
* **Timeline (Zaman Çizelgesi):** Çiftlikte bugün kim ne yaptı? (Kronolojik akış: Süt, Sağlık, Görev).
* **Özet Raporlar:** Tamamlanan işler, yapılan aşılar ve toplanan süt miktarı.

## 📱 Ekran Görüntüleri

| Masaüstü Görünümü | Mobil Görünüm |
|-------------------|---------------|
| *Dashboard ve Tablo Yönetimi* | *Kart Görünümü ve Hızlı İşlemler* |
| ![Desktop](https://via.placeholder.com/600x300?text=Dashboard+Ekranı) | ![Mobile](https://via.placeholder.com/300x600?text=Mobil+Arayüz) |

## 🛠️ Kurulum ve Çalıştırma

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin.

### 1. Projeyi Kopyalayın
```bash
git clone [https://github.com/KULLANICI_ADINIZ/suru-takip-sistemi.git](https://github.com/KULLANICI_ADINIZ/suru-takip-sistemi.git)
cd suru-takip-sistemi

2. Sanal Ortam Oluşturun (Önerilen)
Bash

# Windows için
python -m venv venv
venv\Scripts\activate

# Mac/Linux için
python3 -m venv venv
source venv/bin/activate
3. Gerekli Paketleri Yükleyin
Bash

pip install -r requirements.txt
(Not: requirements.txt dosyanız yoksa pip install Flask Flask-SQLAlchemy Flask-Login komutunu çalıştırın.)

4. Uygulamayı Başlatın
Bash

python app.py
5. Veritabanı Kurulumu
Tarayıcınızda şu adrese giderek veritabanını ve admin kullanıcısını oluşturun: http://127.0.0.1:5000/kurulum

🔑 Varsayılan Giriş Bilgileri
Kurulum sonrası oluşan yönetici hesabı:

Kullanıcı Adı: admin

Şifre: 1234

Veteriner, Sahip ve Çalışan hesapları admin paneli üzerinden eklenmelidir.
