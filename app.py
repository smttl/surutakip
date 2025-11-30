import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date, datetime

# --- AYARLAR ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///suru.db'
app.config['SECRET_KEY'] = 'cok_gizli_anahtar_999' # Güvenlik anahtarı
app.config['UPLOAD_FOLDER'] = 'static/uploads' # Dosya yükleme yolu
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Max 16MB dosya
db = SQLAlchemy(app)

# --- LOGIN YÖNETİCİSİ ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- YARDIMCI FONKSİYON: DOSYA KAYDETME ---
def dosya_kaydet(file):
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        yeni_isim = f"{datetime.now().timestamp()}_{filename}"
        dosya_yolu = os.path.join(app.config['UPLOAD_FOLDER'], yeni_isim)
        file.save(dosya_yolu)
        return yeni_isim
    return None

# ==========================================
# VERİTABANI MODELLERİ (TABLOLAR)
# ==========================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20)) # admin, sahip, vet, calisan

class Grup(db.Model):
    """Padok veya Grupları Temsil Eder"""
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50), unique=True, nullable=False)
    aciklama = db.Column(db.String(200)) # Padok açıklaması
    hayvanlar = db.relationship('Hayvan', backref='grup', lazy=True)

class Hayvan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Kimlik
    kupe_no = db.Column(db.String(20), unique=True, nullable=False)
    padok_no = db.Column(db.String(20)) # Padok İçi Sıra No
    tur = db.Column(db.String(50), nullable=False) # Sığır, Koyun
    irk = db.Column(db.String(50))
    
    # Detaylar
    yas_ay = db.Column(db.Integer)
    dogum_sayisi = db.Column(db.Integer, default=0)
    cinsiyet = db.Column(db.String(10), default='Dişi')
    dogum_tarihi = db.Column(db.String(20))
    
    # Sağlık ve Durum
    saglik_durumu = db.Column(db.String(100), default="Sağlıklı")
    sagilabilir = db.Column(db.Boolean, default=False)
    
    # Gebelik Takibi
    gebe_mi = db.Column(db.Boolean, default=False)
    tohumlama_tarihi = db.Column(db.Date, nullable=True)

    # Konum
    grup_id = db.Column(db.Integer, db.ForeignKey('grup.id'), nullable=True)

    # İlişkiler
    sut_verileri = db.relationship('SutUretimi', backref='hayvan', lazy=True)
    saglik_kayitlari = db.relationship('SaglikKaydi', backref='hayvan', lazy=True)
    hastalik_bildirimleri = db.relationship('HastalikBildirim', backref='hayvan', lazy=True)
    asi_takvimi = db.relationship('AsiTakvimi', backref='hayvan', lazy=True)

class SaglikKaydi(db.Model):
    """Muayene, Tedavi, Aşı Geçmişi"""
    id = db.Column(db.Integer, primary_key=True)
    hayvan_id = db.Column(db.Integer, db.ForeignKey('hayvan.id'), nullable=False)
    islem_tipi = db.Column(db.String(50)) # Muayene, Tedavi, Aşı...
    aciklama = db.Column(db.Text)
    dosya = db.Column(db.String(200)) # Foto/Video
    tarih = db.Column(db.Date, default=date.today)
    vet_adi = db.Column(db.String(50)) # İşlemi yapan kişi

class AsiTakvimi(db.Model):
    """Planlanan ve Yapılan Aşılar"""
    id = db.Column(db.Integer, primary_key=True)
    hayvan_id = db.Column(db.Integer, db.ForeignKey('hayvan.id'))
    asi_adi = db.Column(db.String(100))
    notlar = db.Column(db.String(200)) # Aşıyla ilgili not
    planlanan_tarih = db.Column(db.Date)
    yapildi_mi = db.Column(db.Boolean, default=False)
    yapilma_tarihi = db.Column(db.Date)
    yapan_kisi_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class HastalikBildirim(db.Model):
    """Personel veya Sahibin Bildirdiği Acil Durumlar"""
    id = db.Column(db.Integer, primary_key=True)
    hayvan_id = db.Column(db.Integer, db.ForeignKey('hayvan.id'))
    bildiren_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    aciklama = db.Column(db.Text)
    dosya = db.Column(db.String(200))
    tarih = db.Column(db.Date, default=date.today)
    durum = db.Column(db.String(20), default='İncelenmedi')
    bildiren = db.relationship('User', backref='bildirimler')

class Gorev(db.Model):
    """Personel Görevleri"""
    id = db.Column(db.Integer, primary_key=True)
    atanan_kisi_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    aciklama = db.Column(db.String(200))
    durum = db.Column(db.String(20), default='Bekliyor')
    tarih = db.Column(db.Date, default=date.today)
    # İlişki: Görevi kime atadık?
    atanan_kisi = db.relationship('User', foreign_keys=[atanan_kisi_id])

class SutUretimi(db.Model):
    """Günlük Süt Girişleri"""
    id = db.Column(db.Integer, primary_key=True)
    hayvan_id = db.Column(db.Integer, db.ForeignKey('hayvan.id'))
    miktar = db.Column(db.Float)
    tarih = db.Column(db.Date, default=date.today)
    kaydeden_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ==========================================
# ROTALAR (ENDPOINTS)
# ==========================================

@app.route('/kurulum')
def setup():
    db.create_all()
    # Varsayılan Admin oluştur
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password=generate_password_hash('1234'), role='admin'))
        db.session.commit()
    return "Veritabanı Oluşturuldu! Admin: admin / 1234 <br><a href='/login'>Giriş Yap</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            if user.role == 'calisan': return redirect(url_for('calisan_panel'))
            return redirect(url_for('dashboard'))
        flash('Hatalı kullanıcı adı veya şifre!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.role == 'calisan': return redirect(url_for('calisan_panel'))
    
    # --- YENİ HAYVAN EKLEME ---
    if request.method == 'POST' and 'kupe_no' in request.form:
        if current_user.role in ['admin', 'sahip', 'vet']:
            try:
                secilen_grup_id = request.form.get('grup_id') or None
                yeni = Hayvan(
                    kupe_no=request.form['kupe_no'],
                    padok_no=request.form['padok_no'],
                    tur=request.form['tur'],
                    irk=request.form['irk'],
                    yas_ay=int(request.form.get('yas_ay', 0)),
                    dogum_sayisi=int(request.form.get('dogum_sayisi', 0)),
                    cinsiyet=request.form['cinsiyet'],
                    sagilabilir=(request.form.get('sagilabilir') == 'on'),
                    grup_id=secilen_grup_id
                )
                db.session.add(yeni)
                db.session.commit()
                flash('Hayvan başarıyla eklendi.')
            except Exception as e: flash(f'Hata oluştu: {e}')
    
    suru = Hayvan.query.all()
    gruplar = Grup.query.all()
    calisanlar = User.query.filter_by(role='calisan').all()
    bildirimler = HastalikBildirim.query.filter_by(durum='İncelenmedi').all()
    
    return render_template('dashboard.html', suru=suru, user=current_user, calisanlar=calisanlar, bildirimler=bildirimler, gruplar=gruplar)

# --- AŞI TAKVİMİ (PLANLAMA & LİSTELEME) ---
@app.route('/asi_takvimi', methods=['GET', 'POST'])
@login_required
def asi_takvimi():
    # POST: Planlama (Sadece Vet/Admin)
    if request.method == 'POST':
        if current_user.role not in ['vet', 'admin']:
            flash('Aşı planlama yetkiniz yok!')
            return redirect(url_for('asi_takvimi'))

        not_metni = request.form.get('notlar', '')
        
        # 1. Toplu Planlama (Gruba Göre)
        if 'grup_id' in request.form:
            hedef_grup_id = request.form['grup_id']
            hedef_hayvanlar = Hayvan.query.filter_by(grup_id=hedef_grup_id).all()
            if hedef_hayvanlar:
                for h in hedef_hayvanlar:
                    plan = AsiTakvimi(
                        hayvan_id=h.id, 
                        asi_adi=request.form['asi_adi'], 
                        notlar=not_metni,
                        planlanan_tarih=datetime.strptime(request.form['planlanan_tarih'], '%Y-%m-%d').date()
                    )
                    db.session.add(plan)
                flash(f'{len(hedef_hayvanlar)} hayvana aşı planlandı.')
            else:
                flash('Seçilen grupta hayvan yok.')

        # 2. Tekil Planlama
        elif 'hayvan_id' in request.form:
            plan = AsiTakvimi(
                hayvan_id=request.form['hayvan_id'], 
                asi_adi=request.form['asi_adi'], 
                notlar=not_metni,
                planlanan_tarih=datetime.strptime(request.form['planlanan_tarih'], '%Y-%m-%d').date()
            )
            db.session.add(plan)
            flash('Aşı takvime eklendi.')
        
        db.session.commit()
    
    # GET: Listeleme (Herkes görebilir)
    bekleyenler = AsiTakvimi.query.filter_by(yapildi_mi=False).order_by(AsiTakvimi.planlanan_tarih).all()
    hayvanlar = Hayvan.query.all()
    gruplar = Grup.query.all()
    return render_template('asi_takvimi.html', asilar=bekleyenler, hayvanlar=hayvanlar, gruplar=gruplar, bugun=date.today())

# --- AŞI YAPILDI İŞARETLEME ---
@app.route('/asi_yapildi/<int:asi_id>')
@login_required
def asi_yapildi(asi_id):
    asi = AsiTakvimi.query.get_or_404(asi_id)
    asi.yapildi_mi = True
    asi.yapilma_tarihi = date.today()
    asi.yapan_kisi_id = current_user.id
    
    # Otomatik olarak sağlık geçmişine de yaz
    db.session.add(SaglikKaydi(
        hayvan_id=asi.hayvan_id, 
        islem_tipi="Aşı (Takvim)",
        aciklama=f"{asi.asi_adi} yapıldı. (Not: {asi.notlar})", 
        vet_adi=current_user.username
    ))
    db.session.commit()
    
    if current_user.role == 'calisan': flash('Aşı yapıldı olarak işaretlendi.')
    return redirect(url_for('asi_takvimi'))

# --- PADOK EKLEME ---
@app.route('/grup_ekle', methods=['POST'])
@login_required
def grup_ekle():
    if current_user.role in ['admin', 'sahip', 'vet']:
        db.session.add(Grup(
            ad=request.form['grup_ad'], 
            aciklama=request.form.get('aciklama', '')
        ))
        db.session.commit()
    return redirect(url_for('dashboard'))

# --- GEBELİK GÜNCELLEME (YENİ) ---
@app.route('/gebelik_guncelle/<int:hayvan_id>', methods=['POST'])
@login_required
def gebelik_guncelle(hayvan_id):
    if current_user.role not in ['admin', 'vet']: return "Yetkisiz", 403
    
    hayvan = Hayvan.query.get_or_404(hayvan_id)
    durum = request.form.get('gebelik_durumu')
    
    if durum == 'Gebe':
        hayvan.gebe_mi = True
        tarih_str = request.form.get('tohumlama_tarihi')
        if tarih_str:
            hayvan.tohumlama_tarihi = datetime.strptime(tarih_str, '%Y-%m-%d').date()
        
        # Kayıt düş
        db.session.add(SaglikKaydi(
            hayvan_id=hayvan.id, islem_tipi="Tohumlama/Gebelik",
            aciklama=f"Gebe işaretlendi. Tohumlama: {tarih_str}", vet_adi=current_user.username
        ))

    elif durum == 'Bos':
        hayvan.gebe_mi = False
        hayvan.tohumlama_tarihi = None
        db.session.add(SaglikKaydi(
            hayvan_id=hayvan.id, islem_tipi="Gebelik Sonlandı",
            aciklama="Gebelik durumu kaldırıldı/Doğum gerçekleşti.", vet_adi=current_user.username
        ))

    db.session.commit()
    flash('Gebelik durumu güncellendi.')
    return redirect(url_for('vet_detay', hayvan_id=hayvan.id))

# --- PATRON RAPORLARI (TIMELINE) ---
@app.route('/islem_gecmisi')
@login_required
def islem_gecmisi():
    if current_user.role not in ['admin', 'sahip']: return "Yetkisiz", 403
    
    tum_islemler = []

    # 1. Sağlık
    sagliklar = SaglikKaydi.query.all()
    for s in sagliklar:
        tum_islemler.append({
            'tarih': s.tarih, 'kategori': 'Sağlık', 'renk': 'danger', 'ikon': '💉',
            'detay': f"{s.hayvan.kupe_no} ({s.hayvan.padok_no}) - {s.islem_tipi}: {s.aciklama}",
            'yapan': s.vet_adi
        })

    # 2. Süt
    sutler = SutUretimi.query.all()
    for s in sutler:
        yapan = User.query.get(s.kaydeden_id)
        yapan_adi = yapan.username if yapan else "?"
        tum_islemler.append({
            'tarih': s.tarih, 'kategori': 'Üretim', 'renk': 'warning', 'ikon': '🥛',
            'detay': f"{s.hayvan.kupe_no} - {s.miktar} Lt Süt",
            'yapan': yapan_adi
        })

    # 3. Görevler
    gorevler = Gorev.query.filter_by(durum='Tamamlandı').all()
    for g in gorevler:
        yapan_adi = g.atanan_kisi.username if g.atanan_kisi else "Personel"
        tum_islemler.append({
            'tarih': g.tarih, 'kategori': 'Görev', 'renk': 'success', 'ikon': '✅',
            'detay': f"Tamamlandı: {g.aciklama}",
            'yapan': yapan_adi
        })
        
    # 4. Bildirimler
    bildirimler = HastalikBildirim.query.all()
    for b in bildirimler:
         tum_islemler.append({
            'tarih': b.tarih, 'kategori': 'Bildirim', 'renk': 'dark', 'ikon': '🚨',
            'detay': f"Hastalık Bildirimi: {b.hayvan.kupe_no} - {b.aciklama}",
            'yapan': b.bildiren.username
        })

    # Tarihe göre sırala (En yeni en üstte)
    tum_islemler.sort(key=lambda x: x['tarih'], reverse=True)

    return render_template('islem_gecmisi.html', islemler=tum_islemler)

# --- DİĞER STANDART ROTALAR ---

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if current_user.role != 'admin': return "Yetkisiz", 403
    if request.method == 'POST':
        if 'sil_id' in request.form:
            u = User.query.get(request.form['sil_id'])
            if u.username != 'admin': db.session.delete(u); db.session.commit()
        else:
            db.session.add(User(username=request.form['username'], password=generate_password_hash(request.form['password']), role=request.form['role'])); db.session.commit()
    return render_template('admin_users.html', users=User.query.all())

@app.route('/vet/detay/<int:hayvan_id>', methods=['GET', 'POST'])
@login_required
def vet_detay(hayvan_id):
    if current_user.role not in ['admin', 'vet', 'sahip']: return "Yetkisiz", 403
    hayvan = Hayvan.query.get_or_404(hayvan_id)
    
    if request.method == 'POST':
        if current_user.role == 'sahip':
            flash("Sadece Veteriner Hekim veri girebilir.")
            return redirect(url_for('vet_detay', hayvan_id=hayvan_id))
            
        dosya_adi = dosya_kaydet(request.files['dosya'])
        db.session.add(SaglikKaydi(
            hayvan_id=hayvan_id, islem_tipi=request.form['islem_tipi'], 
            aciklama=request.form['aciklama'], dosya=dosya_adi, 
            tarih=datetime.strptime(request.form['tarih'], '%Y-%m-%d').date(), 
            vet_adi=current_user.username
        ))
        db.session.commit()
        return redirect(url_for('vet_detay', hayvan_id=hayvan_id))
        
    return render_template('vet_detay.html', hayvan=hayvan)

@app.route('/hastalik_bildir', methods=['GET', 'POST'])
@login_required
def hastalik_bildir():
    if request.method == 'POST':
        dosya_adi = dosya_kaydet(request.files['dosya'])
        h = Hayvan.query.get(request.form['hayvan_id'])
        h.saglik_durumu = "Hasta/Kontrol"
        db.session.add(HastalikBildirim(hayvan_id=request.form['hayvan_id'], bildiren_id=current_user.id, aciklama=request.form['aciklama'], dosya=dosya_adi)); db.session.commit()
        if current_user.role == 'calisan': return redirect(url_for('calisan_panel'))
        return redirect(url_for('dashboard'))
    return render_template('hastalik_bildir.html', hayvanlar=Hayvan.query.all())

@app.route('/gorev_ata', methods=['POST'])
@login_required
def gorev_ata():
    if current_user.role in ['admin', 'sahip', 'vet']:
        db.session.add(Gorev(atanan_kisi_id=request.form['calisan_id'], aciklama=request.form['aciklama'])); db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/calisan/panel', methods=['GET', 'POST'])
@login_required
def calisan_panel():
    if request.method == 'POST':
        if 'gorev_id' in request.form:
            g = Gorev.query.get(request.form['gorev_id'])
            if g.atanan_kisi_id == current_user.id: g.durum = 'Tamamlandı'; db.session.commit()
        elif 'sut_miktar' in request.form:
            db.session.add(SutUretimi(hayvan_id=request.form['hayvan_id'], miktar=float(request.form['sut_miktar']), kaydeden_id=current_user.id)); db.session.commit()
        return redirect(url_for('calisan_panel'))
    gorevler = Gorev.query.filter_by(atanan_kisi_id=current_user.id, durum='Bekliyor').all()
    sagmal = Hayvan.query.filter_by(sagilabilir=True).all()
    return render_template('calisan_panel.html', gorevler=gorevler, sagmal_hayvanlar=sagmal)

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)