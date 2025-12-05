import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date, datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///suru.db'
app.config['SECRET_KEY'] = 'gizli_anahtar_999'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def dosya_kaydet(file):
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        yeni_isim = f"{datetime.now().timestamp()}_{filename}"
        dosya_yolu = os.path.join(app.config['UPLOAD_FOLDER'], yeni_isim)
        file.save(dosya_yolu)
        return yeni_isim
    return None

# --- MODELLER ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20)) # admin, sahip, vet, calisan

class Grup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50), unique=True, nullable=False)
    aciklama = db.Column(db.String(200)) 
    hayvanlar = db.relationship('Hayvan', backref='grup', lazy=True)

class Hayvan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kupe_no = db.Column(db.String(20), unique=True, nullable=False)
    padok_no = db.Column(db.String(20))
    tur = db.Column(db.String(50), nullable=False)
    irk = db.Column(db.String(50))
    yas_ay = db.Column(db.Integer)
    dogum_sayisi = db.Column(db.Integer, default=0)
    cinsiyet = db.Column(db.String(10), default='Dişi')
    
    gebe_mi = db.Column(db.Boolean, default=False)
    tohumlama_tarihi = db.Column(db.Date, nullable=True)
    
    dogum_tarihi = db.Column(db.String(20))
    saglik_durumu = db.Column(db.String(100), default="Sağlıklı")
    sagilabilir = db.Column(db.Boolean, default=False)
    
    # Akıbet: Mevcut, Kesim, Ölüm, Satış
    akibet = db.Column(db.String(20), default='Mevcut') 
    grup_id = db.Column(db.Integer, db.ForeignKey('grup.id'), nullable=True)

    sut_verileri = db.relationship('SutUretimi', backref='hayvan', lazy=True, cascade="all, delete-orphan")
    saglik_kayitlari = db.relationship('SaglikKaydi', backref='hayvan', lazy=True, cascade="all, delete-orphan")
    hastalik_bildirimleri = db.relationship('HastalikBildirim', backref='hayvan', lazy=True, cascade="all, delete-orphan")
    asi_takvimi = db.relationship('AsiTakvimi', backref='hayvan', lazy=True, cascade="all, delete-orphan")

class SaglikKaydi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hayvan_id = db.Column(db.Integer, db.ForeignKey('hayvan.id'), nullable=False)
    islem_tipi = db.Column(db.String(50))
    aciklama = db.Column(db.Text)
    dosya = db.Column(db.String(200))
    tarih = db.Column(db.Date, default=date.today)
    vet_adi = db.Column(db.String(50))

class AsiTakvimi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hayvan_id = db.Column(db.Integer, db.ForeignKey('hayvan.id'))
    asi_adi = db.Column(db.String(100))
    notlar = db.Column(db.String(200))
    planlanan_tarih = db.Column(db.Date)
    yapildi_mi = db.Column(db.Boolean, default=False)
    yapilma_tarihi = db.Column(db.Date)
    yapan_kisi_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class HastalikBildirim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hayvan_id = db.Column(db.Integer, db.ForeignKey('hayvan.id'))
    bildiren_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    aciklama = db.Column(db.Text)
    dosya = db.Column(db.String(200))
    tarih = db.Column(db.Date, default=date.today)
    durum = db.Column(db.String(20), default='İncelenmedi')
    bildiren = db.relationship('User', backref='bildirimler')

class Gorev(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    atanan_kisi_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    aciklama = db.Column(db.String(200))
    durum = db.Column(db.String(20), default='Bekliyor')
    tarih = db.Column(db.Date, default=date.today)
    atanan_kisi = db.relationship('User', foreign_keys=[atanan_kisi_id])

class SutUretimi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hayvan_id = db.Column(db.Integer, db.ForeignKey('hayvan.id'))
    miktar = db.Column(db.Float)
    tarih = db.Column(db.Date, default=date.today)
    kaydeden_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# --- ROTALAR ---

@app.route('/kurulum')
def setup():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password=generate_password_hash('1234'), role='admin'))
        db.session.commit()
    return "Kurulum Tamam! Admin: admin / 1234. <br><a href='/login'>Giriş</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            if user.role == 'calisan': return redirect(url_for('calisan_panel'))
            return redirect(url_for('dashboard'))
        flash('Hatalı giriş!')
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
    
    if request.method == 'POST' and 'kupe_no' in request.form:
        if current_user.role in ['admin', 'sahip', 'vet']:
            try:
                grup = request.form.get('grup_id') or None
                yeni = Hayvan(
                    kupe_no=request.form['kupe_no'], padok_no=request.form['padok_no'],
                    tur=request.form['tur'], irk=request.form['irk'],
                    yas_ay=int(request.form.get('yas_ay', 0)),
                    dogum_sayisi=int(request.form.get('dogum_sayisi', 0)),
                    cinsiyet=request.form['cinsiyet'],
                    sagilabilir=(request.form.get('sagilabilir') == 'on'),
                    grup_id=grup, akibet='Mevcut'
                )
                db.session.add(yeni)
                db.session.commit()
                flash('Hayvan eklendi.')
            except Exception as e: flash(f'Hata: {e}')
    
    # Sadece Mevcut Hayvanlar
    suru = Hayvan.query.filter_by(akibet='Mevcut').all()
    gruplar = Grup.query.all()
    calisanlar = User.query.filter_by(role='calisan').all()
    bildirimler = HastalikBildirim.query.filter_by(durum='İncelenmedi').all()
    return render_template('dashboard.html', suru=suru, user=current_user, calisanlar=calisanlar, bildirimler=bildirimler, gruplar=gruplar)

@app.route('/hayvan_cikar/<int:hayvan_id>', methods=['POST'])
@login_required
def hayvan_cikar(hayvan_id):
    if current_user.role not in ['admin', 'sahip', 'vet']: return "Yetkisiz", 403
    h = Hayvan.query.get_or_404(hayvan_id)
    sebep = request.form.get('sebep')
    if sebep == 'Sil':
        db.session.delete(h)
        flash('Kayıt silindi.')
    else:
        h.akibet = sebep
        db.session.add(SaglikKaydi(hayvan_id=h.id, islem_tipi="Ayrılış", aciklama=f"Sebep: {sebep}", vet_adi=current_user.username))
        flash(f'Hayvan {sebep} olarak işaretlendi.')
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/asi_takvimi', methods=['GET', 'POST'])
@login_required
def asi_takvimi():
    if request.method == 'POST':
        if current_user.role not in ['vet', 'admin']:
            flash('Planlama yetkiniz yok.'); return redirect(url_for('asi_takvimi'))
        
        notu = request.form.get('notlar', '')
        tarih = datetime.strptime(request.form['planlanan_tarih'], '%Y-%m-%d').date()
        
        if 'grup_id' in request.form:
            targets = Hayvan.query.filter_by(grup_id=request.form['grup_id'], akibet='Mevcut').all()
            for h in targets:
                db.session.add(AsiTakvimi(hayvan_id=h.id, asi_adi=request.form['asi_adi'], notlar=notu, planlanan_tarih=tarih))
            flash(f'{len(targets)} hayvana planlandı.')
        elif 'hayvan_id' in request.form:
            db.session.add(AsiTakvimi(hayvan_id=request.form['hayvan_id'], asi_adi=request.form['asi_adi'], notlar=notu, planlanan_tarih=tarih))
            flash('Aşı eklendi.')
        db.session.commit()
    
    bekleyenler = AsiTakvimi.query.filter_by(yapildi_mi=False).order_by(AsiTakvimi.planlanan_tarih).all()
    hayvanlar = Hayvan.query.filter_by(akibet='Mevcut').all()
    gruplar = Grup.query.all()
    return render_template('asi_takvimi.html', asilar=bekleyenler, hayvanlar=hayvanlar, gruplar=gruplar, bugun=date.today())

@app.route('/asi_yapildi/<int:asi_id>')
@login_required
def asi_yapildi(asi_id):
    asi = AsiTakvimi.query.get_or_404(asi_id)
    asi.yapildi_mi = True
    asi.yapilma_tarihi = date.today()
    asi.yapan_kisi_id = current_user.id
    db.session.add(SaglikKaydi(hayvan_id=asi.hayvan_id, islem_tipi="Aşı", aciklama=f"{asi.asi_adi} yapıldı. {asi.notlar}", vet_adi=current_user.username))
    db.session.commit()
    return redirect(url_for('asi_takvimi'))

@app.route('/gebelik_guncelle/<int:hayvan_id>', methods=['POST'])
@login_required
def gebelik_guncelle(hayvan_id):
    if current_user.role not in ['admin', 'vet']: return "Yetkisiz", 403
    h = Hayvan.query.get(hayvan_id)
    durum = request.form.get('gebelik_durumu')
    if durum == 'Gebe':
        h.gebe_mi = True
        if request.form.get('tohumlama_tarihi'): h.tohumlama_tarihi = datetime.strptime(request.form.get('tohumlama_tarihi'), '%Y-%m-%d').date()
        db.session.add(SaglikKaydi(hayvan_id=h.id, islem_tipi="Tohumlama", aciklama="Gebe işaretlendi", vet_adi=current_user.username))
    else:
        h.gebe_mi = False
        h.tohumlama_tarihi = None
        db.session.add(SaglikKaydi(hayvan_id=h.id, islem_tipi="Gebelik Bitti", aciklama="Boş/Doğum", vet_adi=current_user.username))
    db.session.commit()
    return redirect(url_for('vet_detay', hayvan_id=h.id))

@app.route('/grup_ekle', methods=['POST'])
@login_required
def grup_ekle():
    if current_user.role in ['admin', 'sahip', 'vet']:
        db.session.add(Grup(ad=request.form['grup_ad'], aciklama=request.form.get('aciklama', '')))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/islem_gecmisi')
@login_required
def islem_gecmisi():
    if current_user.role not in ['admin', 'sahip']: return "Yetkisiz", 403
    tum = []
    for s in SaglikKaydi.query.all(): tum.append({'t': s.tarih, 'kat': 'Sağlık', 'd': f"{s.hayvan.kupe_no} - {s.islem_tipi}", 'y': s.vet_adi, 'c': 'danger', 'i': '💉'})
    for s in SutUretimi.query.all(): u = User.query.get(s.kaydeden_id); tum.append({'t': s.tarih, 'kat': 'Süt', 'd': f"{s.hayvan.kupe_no} - {s.miktar}Lt", 'y': u.username if u else '?', 'c': 'warning', 'i': '🥛'})
    for g in Gorev.query.filter_by(durum='Tamamlandı').all(): tum.append({'t': g.tarih, 'kat': 'Görev', 'd': g.aciklama, 'y': g.atanan_kisi.username if g.atanan_kisi else '?', 'c': 'success', 'i': '✅'})
    for b in HastalikBildirim.query.all(): tum.append({'t': b.tarih, 'kat': 'Bildirim', 'd': f"{b.hayvan.kupe_no} - {b.aciklama}", 'y': b.bildiren.username, 'c': 'dark', 'i': '🚨'})
    tum.sort(key=lambda x: x['t'], reverse=True)
    return render_template('islem_gecmisi.html', islemler=tum)

@app.route('/vet/detay/<int:hayvan_id>', methods=['GET', 'POST'])
@login_required
def vet_detay(hayvan_id):
    if current_user.role not in ['admin', 'vet', 'sahip']: return "Yetkisiz", 403
    hayvan = Hayvan.query.get_or_404(hayvan_id)
    if request.method == 'POST':
        if current_user.role == 'sahip': flash("Veri girişi yetkiniz yok."); return redirect(request.url)
        dosya = dosya_kaydet(request.files['dosya'])
        db.session.add(SaglikKaydi(hayvan_id=hayvan_id, islem_tipi=request.form['islem_tipi'], aciklama=request.form['aciklama'], dosya=dosya, tarih=datetime.strptime(request.form['tarih'], '%Y-%m-%d').date(), vet_adi=current_user.username))
        db.session.commit()
        return redirect(url_for('vet_detay', hayvan_id=hayvan_id))
    return render_template('vet_detay.html', hayvan=hayvan)

@app.route('/hastalik_bildir', methods=['GET', 'POST'])
@login_required
def hastalik_bildir():
    if request.method == 'POST':
        dosya = dosya_kaydet(request.files['dosya'])
        h = Hayvan.query.get(request.form['hayvan_id'])
        h.saglik_durumu = "Hasta/Kontrol"
        db.session.add(HastalikBildirim(hayvan_id=h.id, bildiren_id=current_user.id, aciklama=request.form['aciklama'], dosya=dosya))
        db.session.commit()
        if current_user.role == 'calisan': return redirect(url_for('calisan_panel'))
        return redirect(url_for('dashboard'))
    return render_template('hastalik_bildir.html', hayvanlar=Hayvan.query.filter_by(akibet='Mevcut').all())

@app.route('/gorev_ata', methods=['POST'])
@login_required
def gorev_ata():
    if current_user.role in ['admin', 'sahip', 'vet']:
        db.session.add(Gorev(atanan_kisi_id=request.form['calisan_id'], aciklama=request.form['aciklama']))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/calisan/panel', methods=['GET', 'POST'])
@login_required
def calisan_panel():
    if request.method == 'POST':
        if 'gorev_id' in request.form:
            g = Gorev.query.get(request.form['gorev_id'])
            if g.atanan_kisi_id == current_user.id: g.durum='Tamamlandı'; db.session.commit()
        elif 'sut_miktar' in request.form:
            db.session.add(SutUretimi(hayvan_id=request.form['hayvan_id'], miktar=float(request.form['sut_miktar']), kaydeden_id=current_user.id)); db.session.commit()
        return redirect(url_for('calisan_panel'))
    gorevler = Gorev.query.filter_by(atanan_kisi_id=current_user.id, durum='Bekliyor').all()
    sagmal = Hayvan.query.filter_by(sagilabilir=True, akibet='Mevcut').all()
    return render_template('calisan_panel.html', gorevler=gorevler, sagmal_hayvanlar=sagmal)

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

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000, debug=True)