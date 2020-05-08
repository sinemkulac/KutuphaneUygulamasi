from flask import Flask,send_from_directory,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from passlib.hash import sha256_crypt
import os
from werkzeug.utils import secure_filename
import datetime
import time
from functools import wraps
from cv2 import cv2
import pytesseract
import matplotlib.pyplot as plt 

from PIL import Image
import numpy as np
import re


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
          return f(*args, **kwargs)
        else:
          flash("Bu sayfayı görüntülemek için giriş yapın","danger")
          return redirect(url_for("login"))
    return decorated_function

UPLOAD_FOLDER = 'E:/user/flask_app/uploads'
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg'}

#Global değişkenler
userName = ""
zaman=""

#global fonksiyonlar
class  Zaman():
  zaman=""
class Record():
    userName = ""
    bookName = ""
    
nesne = Record()
zaman_degiskeni=Zaman()
zaman_degiskeni.zaman=datetime.date.today()
app = Flask(__name__)
app.secret_key="app"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
class AddBook(Form):
  book_name=StringField('Kitap İsmi :',validators=[validators.Length(min=4,max=30)])
  ISBN=StringField('ISBN:')
class Login(Form):
  name=StringField('Kullanıcı İsmi :')
  password=PasswordField('Parola:')
  
  confirm=PasswordField("Parola Doğrula")
class Login_admin(Form):
  password=PasswordField('Parola:')
  
  confirm=PasswordField("Parola Doğrula")
    
app=Flask(__name__ )
app.secret_key="app"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="library"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)

def resim_oku(kitap_adi):
  print("resim okunuyor")
  kitap_adi = kitap_adi
  img = cv2.imread('E:\\user\\flask_app\\uploads\\'+kitap_adi)
  #otsu işleme
  img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
  cv2.imwrite('E:\\user\\flask_app\\uploads\\'+"otsu.png", img)
  #gürültü azaltma
  dst = cv2.imread('E:\\user\\flask_app\\uploads\\'+"otsu.png")
  dst = cv2.fastNlMeansDenoisingColored(dst,None,10,10,7,15)
  cv2.imwrite('E:\\user\\flask_app\\uploads\\'+"remove.png", dst)
  #harf kalınşaştırma
  kernel = np.ones((2,2), np.uint8)
  ds = cv2.erode(dst, kernel, iterations=1) 
  cv2.imwrite('E:\\user\\flask_app\\uploads\\'+"erode.png", ds)
  #tesseract okuma
  pytesseract.pytesseract.tesseract_cmd = 'E:\\Program Files\\Tesseract-OCR\\tesseract.exe'
  sonuc = pytesseract.image_to_string(ds, lang = "tur")
  print(sonuc)
  print("\n\n\n şimdi arasından ISBN yi çekicez\n\n\n")
  src = re.split("\n",sonuc)
  isbn = ""
  isbn_dizi = []
  for i in src:
    reg = re.search("ISBN", i)
    if(reg):
      print("isbn burda yazıyor:",i)
      isbn_dizi = re.findall("[0-9]", i)
      for j in isbn_dizi:
        isbn = isbn +j
  print("son isbn budur:",isbn)
  return(isbn)


@app.route("/")
def index():
  return render_template("index.html")

@app.route("/admin",methods= ["GET" , "POST"])
def kitap_ekle():
  session["kullanici"]="Admin"
  session["zaman"]=zaman_degiskeni.zaman
  form= AddBook(request.form)
  if request.method == 'POST' and form.validate():
    book_name=form.book_name.data
    print("burada nesne.bookname kontrol ediliyor",nesne.bookName)
    ISBN=resim_oku(nesne.bookName)   #resimden isbn okuma
    print("\n\n\nburda ISBN yaziyor:",ISBN)
    cursor=mysql.connection.cursor()
    sorgu="Insert into kitap(ISBN,kitap_ad) VALUES (%s,%s)"
    flash("Kitap veri tabanına başarıyla eklendi.","success")
    cursor.execute(sorgu,(ISBN,book_name))
    mysql.connection.commit()
    cursor.close()
  #  if 'file' not in request.files:
  #     flash('No file part')
  #     return redirect(request.url)
  #  file = request.files['file']
  #  if file and allowed_file(file.filename):
  #    filename = secure_filename(file.filename)
  #    file.save(os.path.join(UPLOAD_FOLDER, filename))
  #    flash("Kitap başarıyla veritabanına eklendi.","success")
  #    return redirect(url_for('kitap_ekle',filename=filename))        

    return redirect(url_for("kitap_ekle"))
  else:
    return render_template("admin.html",form=form)

@app.route("/upload_image",methods= ["GET" , "POST"])
def upload_image():
  if request.method=="POST":
    if 'file' not in request.files:
      flash('No file part')
      return redirect(request.url)
    file = request.files['file']
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      nesne.bookName = filename
      print("burada dosya adı var: ", nesne.bookName)
      session["filename"]=filename
      file.save(os.path.join(UPLOAD_FOLDER, filename))
      flash("Kitap fotoğrafı dosyaya eklendi.","success")
      return redirect(url_for("upload_image",filename=filename))   
      
    return redirect(url_for("kitap_ekle"))
  else:
    return redirect(url_for("kitap_ekle"))
     
#  return render_template("upload_image.html",message="upload")  
#@app.route("/upload_image",methods= ["GET" , "POST"])
#def upload_image():
#  if request.method=="POST":
#    if request.files:
#      image=request.files["image "]
#      image.save(os.path.join(app.config["IMAGE_UPLOADS"], image.filename))
#      print("image saved")
#      return redirect(request.url)
#  return render_template("admin/upload_image.html")


@app.route("/admin/liste")
def liste():
  cursor=mysql.connection.cursor()
  sorgu="SELECT k.ISBN,k.kullanici_ad,y.kitap_ad FROM kitap_kayit k,kitap y WHERE k.ISBN=y.ISBN"
  result=cursor.execute(sorgu)
  if result > 0:
    liste=cursor.fetchall()
    return render_template("liste.html",liste=liste) 
  else:
     return render_template("liste.html") 

@app.route("/admin_giris",methods= ["GET" , "POST"])
def login_admin():
  form= Login_admin(request.form)
  if request.method == "POST":
    password_entered=form.password.data
    if password_entered=="yazlab1":
      flash("Başarılı Giriş Yapıldı","success")
      session["logged_in_admin"] = True
      return redirect(url_for("kitap_ekle"))
    else:
      #parola yanlış 
      flash("Parola yanlış","danger")
      return redirect(url_for("login_admin"))  
  return render_template("admin_giris.html",form=form)     
  

@app.route("/user",methods= ["GET" , "POST"])
def login():
  form= Login(request.form)
  if request.method == "POST":
    name=form.name.data
    nesne.userName = name
    password_entered=form.password.data
    cursor=mysql.connection.cursor()
    sorgu="Select * From kullanici  where kullanici_ad=%s "
    result=cursor.execute(sorgu,(name,))
  
    if result > 0:
      #böyle bir kullanıcı varsa
      data=cursor.fetchone()
      real_password=data["parola"]
      if password_entered==real_password:
        session["logged_in"] = True
        session["username"] = name
        #parolalar dogru
        flash("Başarılı Giriş Yapıldı","success")
        return redirect(url_for("usr"))
      else:
        #parola yanlış 
          flash("Parola yanlış","danger")
          return redirect(url_for("login"))
    else:
      #boyle bir kullanıcı  bulunmuyor
      flash("boyle bir kullanıcı  bulunmuyor","danger")
      return redirect(url_for("login"))
  return render_template("user.html",form=form)     

@app.route("/usr")
@login_required
def usr():
    return render_template("usr1.html", deneme = nesne.userName)


#kitap arama
@app.route("/usrkitapara", methods = ["GET", "POST"])
def kitapAra():
    
    
  if request.method == "POST":
    book_name = request.form.get("kitapAdı")
        
    cursor=mysql.connection.cursor()
    result = cursor.execute("select * from kitap where kitap_ad =  %s or ISBN = %s", (book_name, book_name))
        
    #aranan Kitap sistemde varsa
    if result > 0:
      data = cursor.fetchone()
      #kitabın sistemdeki durumu 
            
            
      #kitap sistemde bir kullanıcıdaysa 
      if data["bulunma_durumu"] == 0:
        cursor.close()
        return render_template("usr1.html",KİTAP =data["kitap_ad"], ISBN = data["ISBN"], BULUNMA_DURUMU = "bir kullanıcıda",deneme = nesne.userName  )
            
            #kitap sistemde bir kullanıcıdaysa 
            #if result2 > 0:
            #    teslimTarihi = kayitData[0][2]
            #    return render_template("usr1.html",KİTAP =data[0][1], ISBN = data[0][0], BULUNMA_DURUMU = "bir kullanıcıda", TESLİM_TARİHİ = teslimTarihi    )                    

        
            #kitap kütüphanede duruyorsa
      else:
        cursor.close()
        return render_template("usr1.html",KİTAP =data["kitap_ad"], ISBN = data["ISBN"],  BULUNMA_DURUMU = "kitap sistemde", deneme = nesne.userName)
    #aranan kitap sistemde yoksa
    else:
      return render_template("usr1.html",BULUNMA_DURUMU = "aradığınız kitap bulunmamaktadır", deneme = nesne.userName)
   
   #get isteği olursa
  else:
    return redirect(url_for("usr"))  #fonksiyonun ilişkili olduğu adrese git
    
#kitap alma
@app.route("/usrkitapal",  methods = ["GET", "POST"])
def kitapAl():
    
    if request.method == "POST":
        book_name = request.form.get("kitapAdı")
        
        cursor=mysql.connection.cursor()
        result = cursor.execute("select * from kitap where kitap_ad = %s or ISBN = %s",(book_name, book_name))
         
        #sistemde öyle bir kitap varsa 
        if result > 0:
            
            data = cursor.fetchone()
             
            #kitabı bir kullanıcı aldıysa
            if data["bulunma_durumu"] == 0:    
                cursor.close()
                return render_template("usr1.html", BULUNMA_DURUMU = "bir kullanıcıda", deneme = nesne.userName)
            
            
            #kitap sistemdeyse kitabı kullanıcı alır
            #ve eğer kullanıcının 3den fazla kitabı yoksa tarihi geçen vermediği bir kitap yoksa
            else :
                    
                cursor.execute("select * from kullanici where kullanici_ad = %s ",(nesne.userName,))
                kullaniciData = cursor.fetchone()
                if kullaniciData["kitap_sayisi"] == 0:
                    
                    
                    
                  cursor.execute("update kitap set bulunma_durumu = %s where ISBN = %s", (False, data["ISBN"]))
                  cursor.execute("insert into kitap_kayit (ISBN, kullanici_ad, tarih ) values(%s, %s, %s) ",(data["ISBN"], nesne.userName,zaman_degiskeni.zaman))
                
                  kitapSayisi= kullaniciData["kitap_sayisi"]
                  kitapSayisi= kitapSayisi+1
                
                  cursor.execute("update kullanici set kitap_sayisi = %s where kullanici_ad = %s ",(kitapSayisi, nesne.userName))                
                  flash("Kitap başarıyla eklendi ","success")
                  mysql.connection.commit()
                  cursor.close()
                
                  return redirect(url_for("usr"))
                
                #buraya bir tane if komutu kullanıcı eğer 3 kitap aldıysa kitap alamaz
                if kullaniciData["kitap_sayisi"] == 3:
                    
                    cursor.close()
                    return render_template("usr1.html", BULUNMA_DURUMU = "fazla istek", deneme = nesne.userName)
                cursor.execute("select * from kitap_kayit where kullanici_ad = %s ",(nesne.userName,)) 
                kullanici_ad_data = cursor.fetchone() 
                teslim_tarih=kullanici_ad_data["tarih"]+datetime.timedelta(days=7)
               
                if zaman_degiskeni.zaman> teslim_tarih:
                  cursor.close()
                  flash("Öncelikle teslim tarihi geçen kitabı iade ediniz ","danger")
                  return render_template("usr1.html", BULUNMA_DURUMU = "Teslim tarihi geçmiş kitap bulunmaktadır", deneme = nesne.userName)
                  
                else:
                   
                    #bugünün tarihini alıyoruz
                    
                    
                    cursor.execute("update kitap set bulunma_durumu = %s where ISBN = %s", (False, data["ISBN"]))
                    cursor.execute("insert into kitap_kayit (ISBN, kullanici_ad, tarih ) values(%s, %s, %s) ",(data["ISBN"], nesne.userName,zaman_degiskeni.zaman))
                
                    kitapSayisi= kullaniciData["kitap_sayisi"]
                    kitapSayisi= kitapSayisi+1
                
                    cursor.execute("update kullanici set kitap_sayisi = %s where kullanici_ad = %s ",(kitapSayisi, nesne.userName))                
                    flash("Kitap başarıyla eklendi ","success")
                    mysql.connection.commit()
                    cursor.close()
                
                    return redirect(url_for("usr"))
        
        #sistemde öyle bir kitap yoksa
        else :
            return render_template("usr1.html", BULUNMA_DURUMU = "aradğınız kitap bulunamamaktadır", deneme = nesne.userName)
      
        
@app.route("/usrkitapbırak",  methods = ["GET", "POST"])
def kitapBırak():
  if request.method=="POST":
    if 'file' not in request.files:
      flash('No file part')
      return redirect(request.url)
    file = request.files['file']
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
            
      print("çalışıtı printler")
      print("dosya adı nedir: ", filename)
            
            
      file.save(os.path.join(UPLOAD_FOLDER, "geri.jpeg"))
      #kitabu resmini yükledik şimdi resmi okuyup ısbn çıkartalım
      flash("Kitap görüntüsü işleniyor","info")
      isbn = resim_oku("geri.jpeg")
      print("kullanıcının bırakacağı resimden okunan ısbn budur bu: ",isbn)
            
            
    
            
      #kitap resmini sisteme yükledik şimdi resmi okuyup ısbn çıkartcaz
      print(" dosya türü nedir ", type(file))
            
      #ısbn çıkartıldı mysql sorguları ile sistemde gerekli işlemler yapılacak
            
      cursor=mysql.connection.cursor()
      result = cursor.execute("select * from kitap_kayit where ISBN = %s and kullanici_ad = %s", (isbn, nesne.userName))
            
        #kitap kullanıcıda mi
      if result > 0:
        data_kayit = cursor.fetchone()
        cursor.execute("update kitap set bulunma_durumu = %s where ISBN = %s ",(True, isbn))
        cursor.execute("delete from kitap_kayit where ISBN = %s",(isbn,))
                
        cursor.execute("select * from kullanici where kullanici_ad = %s", (nesne.userName, ))
                
        kullaniciData = cursor.fetchone()
        kitapSayisi = kullaniciData["kitap_sayisi"]
        kitapSayisi = kitapSayisi-1
                
        cursor.execute("update kullanici set kitap_sayisi = %s where kullanici_ad = %s", (kitapSayisi, nesne.userName))
        flash("Kitap başarıyla bırakıldı ","success")
        mysql.connection.commit()
        cursor.close()
                
        return render_template("usr1.html", filename = filename, deneme = nesne.userName) 
      else:
        flash("Kitap kullanıcıda bulunmuyor ","danger")
        cursor.close()
        return redirect(url_for("usr"))
        
    return redirect(url_for("usr"))
  else:
    return redirect(url_for("usr"))
    
 
    
@app.route("/usr/logout")
def logout():
  session.clear()
  return redirect(url_for("login"))   

@app.route("/admin/logout")
def logout_admin():
  session.clear()
  return redirect(url_for("login_admin"))   

@app.route("/admin/ertele")
def ertele():
  zaman_degiskeni.zaman=zaman_degiskeni.zaman+ datetime.timedelta(days=20)
  flash("Zaman 20 gün ertelendi ","success")
  return redirect(url_for("kitap_ekle")) 

if __name__=="__main__":
  app.run(debug=True)
  
  