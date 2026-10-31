# مشروع تفريغ ملحمة جلجامش

مشروع قابل للاستكمال لتقسيم التسجيل، وتفريغه بـ faster-whisper، وحفظ النتائج مع التوقيتات، ودمج المقاطع، ومحاذاة المصدرين النصيين، وإجراء اختبارات الجودة، ثم إنشاء مخرجات Word بعد المراجعة.

## التشغيل

استخدم Python من البيئة الافتراضية:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py environment
.\.venv\Scripts\python.exe run_pipeline.py chunk
.\.venv\Scripts\python.exe run_pipeline.py transcribe
.\.venv\Scripts\python.exe run_pipeline.py merge
.\.venv\Scripts\python.exe run_pipeline.py compare
```

مرحلة التفريغ تحفظ كل مقطع في ملف JSON مستقل وتتجاوز الملفات المكتملة عند إعادة التشغيل.
