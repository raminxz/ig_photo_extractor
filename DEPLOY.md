# 🚀 راهنمای دیپلوی پروژه Flask از GitHub روی Render

این راهنما نحوه انتشار (Deploy) یک پروژه **Python Flask** را از **GitHub** روی **Render** به‌صورت گام‌به‌گام توضیح می‌دهد تا برنامه به‌صورت آنلاین اجرا شود.

---

# 📋 پیش‌نیازها

قبل از شروع، موارد زیر را آماده کنید:

- Python 3.10 یا بالاتر
- Git
- حساب GitHub
- حساب Render
- پروژه Flask که در GitHub قرار گرفته باشد

---

# 📁 ساختار پیشنهادی پروژه

```text
ig_photo_extractor/
│
├── app.py
├── requirements.txt
├── Procfile
├── runtime.txt          # اختیاری
├── static/
├── templates/
├── downloads/
├── README.md
└── .gitignore
```

---

# 📦 مرحله ۱ — ایجاد فایل requirements.txt

تمام کتابخانه‌های موردنیاز پروژه را در این فایل قرار دهید.

اگر پروژه روی سیستم شما اجرا می‌شود، دستور زیر را اجرا کنید:

```bash
pip freeze > requirements.txt
```

نمونه:

```txt
Flask
gunicorn
instaloader
```

---

# ⚙️ مرحله ۲ — ایجاد فایل Procfile

در ریشه پروژه فایلی با نام زیر ایجاد کنید:

```text
Procfile
```

محتوای فایل:

```text
web: gunicorn app:app
```

> اگر نام فایل اصلی یا متغیر Flask متفاوت است، مقدار `app:app` را متناسب با پروژه خود تغییر دهید.

---

# 🐍 مرحله ۳ — ایجاد فایل runtime.txt (اختیاری)

برای مشخص کردن نسخه پایتون:

```text
python-3.12
```

---

# 📝 مرحله ۴ — ویرایش فایل app.py

اگر در انتهای فایل دارید:

```python
app.run(debug=True, port=5000)
```

بهتر است آن را به شکل زیر تغییر دهید:

```python
if __name__ == "__main__":
    app.run(host="0.0.0.0")
```

---

# 🔒 مرحله ۵ — ایجاد فایل .gitignore

```gitignore
venv/
__pycache__/
*.pyc
.env
downloads/
*.zip
```

این فایل باعث می‌شود فایل‌های غیرضروری وارد GitHub نشوند.

---

# 📤 مرحله ۶ — ارسال پروژه به GitHub

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

---

# ☁️ مرحله ۷ — ساخت حساب در Render

وارد سایت زیر شوید:

https://render.com

با حساب GitHub خود وارد شوید و دسترسی لازم را به Render بدهید.

---

# 🌐 مرحله ۸ — ایجاد Web Service

از داشبورد Render مسیر زیر را انتخاب کنید:

```text
Dashboard
    ↓
New +
    ↓
Web Service
```

---

# 🔗 مرحله ۹ — اتصال مخزن GitHub

مخزن پروژه خود را انتخاب کنید.

نمونه:

```text
raminxz/ig_photo_extractor
```

---

# ⚙️ مرحله ۱۰ — تنظیمات سرویس

## نام سرویس

```text
ig-photo-extractor
```

## محیط اجرا

```text
Python
```

## Build Command

```bash
pip install -r requirements.txt
```

## Start Command

```bash
gunicorn app:app
```

---

# 🚀 مرحله ۱۱ — دیپلوی پروژه

روی گزینه **Deploy Web Service** کلیک کنید.

Render به‌صورت خودکار:

- وابستگی‌ها را نصب می‌کند.
- پروژه را Build می‌کند.
- Gunicorn را اجرا می‌کند.
- یک آدرس عمومی (Public URL) در اختیار شما قرار می‌دهد.

نمونه:

```text
https://ig-photo-extractor.onrender.com
```

---

# 🔄 مرحله ۱۲ — بروزرسانی خودکار

هر زمان که پروژه را تغییر دادید:

```bash
git add .
git commit -m "Update project"
git push
```

Render به‌صورت خودکار نسخه جدید را دریافت و مجدداً منتشر (Deploy) می‌کند.

---

# 📚 منابع مفید

## GitHub

وب‌سایت:

https://github.com/

مستندات:

https://docs.github.com/

---

## Render

وب‌سایت:

https://render.com/

مستندات:

https://render.com/docs

---

## Flask

https://flask.palletsprojects.com/

---

## Gunicorn

https://docs.gunicorn.org/

---

## Instaloader

https://instaloader.github.io/

---

# 🛠 سرویس‌های جایگزین

در صورت نیاز می‌توانید از سرویس‌های زیر نیز استفاده کنید:

- Railway
- PythonAnywhere
- Fly.io
- DigitalOcean
- AWS
- Microsoft Azure
- Google Cloud Platform

---

# ⚠️ نکات مهم

- **GitHub Pages قابلیت اجرای Python یا Flask را ندارد.**
- GitHub Pages فقط برای فایل‌های استاتیک مانند موارد زیر مناسب است:
  - HTML
  - CSS
  - JavaScript
  - تصاویر

برای اجرای پروژه‌های Flask باید از سرویس‌هایی مانند Render، Railway یا یک سرور اختصاصی (VPS) استفاده کنید.

---

# 🔄 فرآیند دیپلوی

```text
پروژه روی کامپیوتر
        │
        ▼
بارگذاری در GitHub
        │
        ▼
اتصال به Render
        │
        ▼
نصب وابستگی‌ها
        │
        ▼
اجرای Gunicorn
        │
        ▼
دریافت آدرس عمومی
```

---

# ✅ نمونه

**مخزن GitHub**

```text
https://github.com/raminxz/ig_photo_extractor
```

**آدرس آنلاین برنامه**

```text
https://ig-photo-extractor.onrender.com
```

> پس از هر `git push`، Render به‌صورت خودکار نسخه جدید پروژه را منتشر خواهد کرد.
