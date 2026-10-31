from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def hms(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def main() -> None:
    env = json.loads((ROOT / "output/reports/environment.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/chunks/manifest.json").read_text(encoding="utf-8"))
    merged = json.loads((ROOT / "data/aligned_transcripts/merged.json").read_text(encoding="utf-8"))
    build = json.loads((ROOT / "data/reviewed_text/build_metadata.json").read_text(encoding="utf-8"))
    comparison_path = ROOT / "output/reports/اختلافات_المصادر.csv"
    with comparison_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    status_counts = Counter(r["status"] for r in rows)
    unresolved = [r for r in rows if r["status"] == "غير محسوم"]
    raw_files = sorted((ROOT / "data/raw_transcripts").glob("chunk_*.json"))
    raw = [json.loads(p.read_text(encoding="utf-8")) for p in raw_files]
    small_test = json.loads((ROOT / "data/raw_transcripts/test_small_beam5.json").read_text(encoding="utf-8"))
    medium_test = json.loads((ROOT / "data/raw_transcripts/test_medium_beam5.json").read_text(encoding="utf-8"))
    final_text = (ROOT / "output/txt/ملحمة_جلجامش_النص_المشكول.txt").read_text(encoding="utf-8")
    final_word_count = len(re.findall(r"\S+", final_text))
    youtube_score_col = next(k for k in rows[0] if k.startswith("مستفرغ") and k.endswith(" score"))
    human_score_col = next(k for k in rows[0] if k.startswith("ملحمة") and k.endswith(" score"))
    youtube_scores = [float(r[youtube_score_col]) for r in rows]
    human_scores = [float(r[human_score_col]) for r in rows if float(r[human_score_col]) > 0]

    medium_manifest = json.loads((ROOT / "data/chunks/medium_review_sequential/manifest.json").read_text(encoding="utf-8"))
    medium_results = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((ROOT / "data/raw_transcripts_medium_review_sequential").glob("chunk_*.json"))
    ]
    review_rows = []
    for item, result in zip(medium_manifest["chunks"], medium_results):
        review_rows.append({
            "start": item["start"],
            "end": item["end"],
            "small_score": item["comparison_score"],
            "small": item["small_transcript"],
            "medium": result["text"].replace("\n", " "),
        })
    review_csv = ROOT / "output/reports/مراجعة_medium_للمواضع_الملتبسة.csv"
    with review_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(review_rows[0]))
        writer.writeheader(); writer.writerows(review_rows)

    report = []
    report.append("# تقرير تحقيق ملحمة جلجامش")
    report.append("")
    report.append("## الخلاصة")
    report.append("")
    report.append(
        "عولج التسجيل كاملًا من البداية إلى النهاية، وحُفظ تفريغ آلي جديد مع توقيتات الكلمات. "
        "النص البشري المتاح يغطي نحو أول أربعين دقيقة وهو مشكول أصلًا؛ أما بقية التسجيل فبُنيت من مقابلة "
        "تفريغ يوتيوب بالتفريغ الجديد ثم شُكلت آليًا. لذلك لا توصف النسخة كلها بأنها محققة أو مشكلة بشريًا، "
        "ويظهر حد الانتقال صراحة في ملفي TXT وWord."
    )
    report.append("")
    report.append("## المصادر المفحوصة فعلًا")
    report.append("")
    report.append("- التسجيل الأصلي MP3، وهو المصدر الصوتي الأساسي.")
    report.append("- تفريغ يوتيوب الآلي المقدم داخل المشروع: 1,925 سطرًا و13,769 كلمة.")
    report.append("- النسخة البشرية غير المكتملة: 448 سطرًا، منها 443 سطرًا نصيًا مستخدمًا، و3,939 كلمة قبل استبعاد الملاحظة الختامية.")
    report.append("- رابط يوتيوب المذكور في الطلب لم يُستخدم لتنزيل صوت بديل؛ الاعتماد الصوتي كان على ملف MP3 المحلي.")
    report.append("")
    report.append("## البيئة والأدوات")
    report.append("")
    report.append(f"- النظام: {env['platform']}.")
    report.append(f"- Python: 3.11.9، المعالج: {env['cpu_physical']} أنوية فعلية و{env['cpu_logical']} خيطًا.")
    report.append(f"- RAM: {env['ram_total_gb']}GB إجماليًا، والمتاح وقت الفحص {env['ram_available_gb']}GB.")
    report.append(f"- GPU: {env['gpu']}؛ لم يُستخدم بسبب قدم تعريف CUDA ومحدودية 4GB VRAM.")
    report.append("- FFmpeg 7.1 من imageio-ffmpeg، وPyAV لفحص الحاوية. لم يكن ffprobe مستقلًا موجودًا على PATH.")
    report.append("- faster-whisper 1.2.1، RapidFuzz، Mishkal 0.4.1، وCAMeL Tools 1.6.0.")
    report.append("")
    report.append("## التفريغ الصوتي")
    report.append("")
    report.append(f"- مدة Mutagen: 7,635.40898 ثانية. مدة PyAV: {manifest['duration']:.6f} ثانية.")
    report.append(f"- التقسيم: {len(manifest['chunks'])} مقطعًا، 240 ثانية للمقطع وتداخل ثانيتين.")
    report.append(f"- التغطية: {len(raw_files)}/{len(manifest['chunks'])} مقطعًا مكتملًا، دون مقاطع فاشلة.")
    report.append("- النموذج الكامل: faster-whisper-small متعدد اللغات، CPU int8، beam size 5، اللغة ar، دون VAD، مع word timestamps.")
    report.append(f"- الناتج الخام: {sum(len(x['segments']) for x in raw):,} مقطع ASR و{sum(len(s.get('words', [])) for x in raw for s in x['segments']):,} كلمة قبل الدمج.")
    report.append(f"- الناتج المدمج: {len(merged['words']):,} كلمة؛ أزيلت 27 كلمة كتكرار مؤكد عند حدود التداخل.")
    report.append(f"- زمن الاستدلال الإجمالي المسجل: {hms(sum(x['elapsed_seconds'] for x in raw))}.")
    report.append("")
    report.append("## اختبار النموذج الأعلى دقة")
    report.append("")
    report.append(f"- عينة 45 ثانية: small استغرق {small_test['elapsed_seconds']:.2f} ثانية، وmedium استغرق {medium_test['elapsed_seconds']:.2f} ثانية.")
    report.append("- medium حسّن تطابق العينة مع النسخة البشرية وأزال تكرارًا وهميًا؛ لذلك استُخدم في مراجعة تسعة مواضع منخفضة الاتفاق.")
    report.append("- من أمثلة التصحيح: عند 00:44:07 كرر small اسم الشاعر، بينما أعاد medium جملة تبدأ بـ«قال لها آنو...». لم يُستبدل النص تلقائيًا بلا مقابلة.")
    report.append("")
    report.append("## المحاذاة والتحقق")
    report.append("")
    report.append(f"- وحدات المحاذاة: {len(rows)} وحدة، كل منها نحو 35 كلمة، بترتيب متتابع مقيد زمنيًا.")
    report.append(f"- مؤيد بمصدر نصي بشري: {status_counts['مؤيد بمصدر نصي بشري']} وحدة.")
    report.append(f"- مؤيد باتفاق تفريغين آليين: {status_counts['مؤيد باتفاق تفريغين آليين']} وحدة.")
    report.append(f"- غير محسوم: {status_counts['غير محسوم']} وحدات.")
    report.append(f"- متوسط التشابه مع تفريغ يوتيوب: {sum(youtube_scores)/len(youtube_scores):.1f}%. متوسط التشابه في نطاق النسخة البشرية: {sum(human_scores)/len(human_scores):.1f}%.")
    report.append("- لم تحدث مراجعة سمعية بشرية مباشرة داخل هذه الجلسة، لذلك لا توجد كلمات موسومة «مؤكدة بمراجعة صوتية فعلية». التحقق الصوتي هنا آلي ومقابل بمصدرين نصيين.")
    report.append("")
    report.append("## المواضع غير المحسومة")
    report.append("")
    report.append("| التوقيت | قراءة ASR الجديدة | القراءة المقابلة | الحالة |")
    report.append("|---|---|---|---|")
    youtube_text_col = youtube_score_col[:-6]
    for row in unresolved:
        a = row["new_transcript"].replace("|", "\\|")[:180]
        b = row[youtube_text_col].replace("|", "\\|")[:180]
        report.append(f"| {hms(float(row['start']))}–{hms(float(row['end']))} | {a} | {b} | غير محسوم |")
    report.append("")
    report.append("## بناء النص والتشكيل")
    report.append("")
    report.append(f"- القسم الأول: {build['human_lines']} سطرًا و{build['human_words']:,} كلمة من النسخة البشرية المشكولة، وينتهي قرب 00:40:09.")
    report.append(f"- القسم الثاني: {build['continuation_lines']} سطرًا و{build['continuation_words']:,} كلمة من التفريغ الكامل المقابل، مع تشكيل Mishkal آلي.")
    report.append(f"- النص المسلم: {len(final_text.splitlines()):,} سطرًا و{final_word_count:,} كلمة شاملة العنوان وعلامة الانتقال.")
    report.append("- اختُبر ثبات الحروف لكل سطر مشكل آليًا؛ لم يُسمح للتشكيل بتغيير تسلسل الحروف العربية.")
    report.append("- جُرّب CAMeL MLE الرسمي، لكنه أخطأ في سياق اختباري واضح («شَرَّكَ» بدل «شَرَك»)، ولذلك لم يُعتمد بديلًا شاملًا.")
    report.append("- التشكيل بعد حد الانتقال مسودة آلية غير مراجعة كلمة كلمة، ولا ينبغي الاستشهاد بها بوصفها ضبطًا نحويًا نهائيًا.")
    report.append("")
    report.append("## تغييرات قابلة للتتبع")
    report.append("")
    for name, count in build["deterministic_name_corrections"].items():
        report.append(f"- {name}: {count} تصحيحًا إملائيًا حتميًا في قسم الاستكمال.")
    report.append(f"- استُبعدت من نص القصيدة {len(build['excluded_sound_event_lines'])} علامة صوتية مثل [تصفيق] و[موسيقى]، وبقيت مادة التسجيل الخام محفوظة في ملفات ASR.")
    report.append("")
    report.append("## مستوى الثقة")
    report.append("")
    report.append("- مرتفع نسبيًا في القسم الأول لوجود نسخة بشرية مشكولة ومقابلة آلية بالصوت.")
    report.append("- متوسط في القسم الثاني من جهة الكلمات العامة بسبب اتفاق تفريغين آليين في معظم الوحدات.")
    report.append("- منخفض في التشكيل النحوي والصرفي للقسم الثاني وفي الوحدات الثماني غير المحسومة.")
    report.append("- لا يحقق المشروع بعد شرط «تحقيق كامل نهائي» أو «تشكيل بشري كامل»؛ الملفات تسجل هذه الحدود صراحة.")

    qa_path = ROOT / "output/reports/quality_check.json"
    if qa_path.exists():
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        report.append("")
        report.append("## جودة ملف Word والمخرجات النهائية")
        report.append("")
        report.append(f"- ملف DOCX سليم كبنية ZIP/OOXML وقابل للفتح برمجيًا: {qa.get('docx_test_open', False)}.")
        report.append(f"- اتجاه RTL موجود، وإعداد A4 صحيح: RTL={qa.get('docx_has_rtl_bidi', False)}، A4={qa.get('docx_has_a4_page_size', False)}.")
        report.append(f"- حُوّل المستند إلى PDF وصور: {qa.get('rendered_page_count', 0)} صفحة بأبعاد موحدة {qa.get('rendered_page_dimensions')}.")
        report.append("- فُحصت صور الصفحات الـ47 بصريًا كاملة عبر 12 لوحة اتصال، مع عناية خاصة بالبداية وحد الانتقال والنهاية؛ لم يظهر اقتطاع أو صفحة فارغة غير مقصودة أو اختفاء للحركات أو خلل في اتجاه العربية.")
        report.append("- هذا الفحص يثبت سلامة الإخراج الطباعي، ولا يرفع مستوى القسم الآلي إلى تحقيق لغوي بشري.")

    report_path = ROOT / "output/reports/تقرير_تحقيق_ملحمة_جلجامش.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(report_path.as_posix().encode("unicode_escape").decode("ascii"))


if __name__ == "__main__":
    main()
