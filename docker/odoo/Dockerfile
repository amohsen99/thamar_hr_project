# 1. تحديد الصورة الأساسية من دوكر هب بناءً على نسخة أودو المطلوبة
FROM odoo:19.0

# 2. التحويل للمستخدم root لامتلاك صلاحيات التثبيت
USER root

# 3. تحديث مستودعات النظام وتثبيت حزم الـ Node.js والـ npm الأساسية لتنسيق الـ CSS في أودو
RUN apt-get update && apt-get install -y nodejs npm \
    && npm install -g less less-plugin-clean-css \
    && apt-get clean

# 4. تثبيت مكتبة pyzk ومكتبة hijri-converter الأساسية للمشروع
RUN pip3 install pyzk --break-system-packages

# 4.1. تثبيت مكتبات Python الإضافية من requirements.txt (qrcode لتوليد رموز QR)
COPY etc/requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages -r /tmp/requirements.txt

# 5. العودة للمستخدم odoo العادي لأمان وحماية الحاوية
USER odoo