from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json, os, uuid, logging

# -------- قراءة التوكن من متغير البيئة (أمن) مع fallback مؤقت ----------
# أنصح بوضع التوكن في Secrets/Environment variables باسم TOKEN في Replit
import os
TOKEN = os.environ["TOKEN"]
# --------------------------------------------------------------------

DATA_FILE = "data.json"

# أسماء الأجزاء بالعربي
part_names = [
    "الجزء الأول","الجزء الثاني","الجزء الثالث","الجزء الرابع","الجزء الخامس",
    "الجزء السادس","الجزء السابع","الجزء الثامن","الجزء التاسع","الجزء العاشر",
    "الجزء الحادي عشر","الجزء الثاني عشر","الجزء الثالث عشر","الجزء الرابع عشر","الجزء الخامس عشر",
    "الجزء السادس عشر","الجزء السابع عشر","الجزء الثامن عشر","الجزء التاسع عشر","الجزء العشرون",
    "الجزء الحادي والعشرون","الجزء الثاني والعشرون","الجزء الثالث والعشرون","الجزء الرابع والعشرون","الجزء الخامس والعشرون",
    "الجزء السادس والعشرون","الجزء السابع والعشرون","الجزء الثامن والعشرون","الجزء التاسع والعشرون","الجزء الثلاثون"
]

# تفعيل اللوق للـ console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- دوال إدارة ملف البيانات ----
def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        base = {
            "khatmahs": {
                "shared": {
                    "name": "الختمة المشتركة",
                    "owner": None,
                    "parts": {str(i): None for i in range(1, 31)}
                }
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)

def load_data():
    ensure_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # ضمان البنية
    if "khatmahs" not in data:
        data["khatmahs"] = {
            "shared": {
                "name": "الختمة المشتركة",
                "owner": None,
                "parts": {str(i): None for i in range(1, 31)}
            }
        }
    if "shared" not in data["khatmahs"]:
        data["khatmahs"]["shared"] = {
            "name": "الختمة المشتركة",
            "owner": None,
            "parts": {str(i): None for i in range(1, 31)}
        }
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---- بناء لوحة الأزرار ----
def build_markup(khatmah_code, khatmah):
    keyboard = []
    row = []
    for i in range(1, 31):
        state = khatmah["parts"].get(str(i))
        if state is None:
            symbol = "◻️"
        elif isinstance(state, dict) and state.get("status") == "inprogress":
            symbol = "🔒"
        elif isinstance(state, dict) and state.get("status") == "done":
            symbol = "✅"
        else:
            symbol = "◻️"
        btn_text = f"{i} {symbol}"
        callback = f"res|{khatmah_code}|{i}"
        row.append(InlineKeyboardButton(btn_text, callback_data=callback))
        if i % 5 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# ---- أوامر البوت ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    data = load_data()
    bot_username = context.bot.username or "bot"
    if args:
        code = args[0]
        kh = data["khatmahs"].get(code)
        if kh:
            text = f"🌹 هذه ختمة باسم: {kh.get('name','')}\nاضغط على أي جزء للحجز أو الإكمال:"
            markup = build_markup(code, kh)
            await update.message.reply_text(text, reply_markup=markup)
            return
    # رسالة افتراضية
    await update.message.reply_text(
        "السلام عليكم 🌹\n"
        "مرحبًا في بوت الختمة.\n\n"
        "🔸 إنشاء ختمة خاصة: /create\n"
        "🔹 عرض ختمتك الخاصة: /parts\n"
        "🔸 عرض الختمة المشتركة: /shared\n"
        "🔹 إعادة بدء ختمتك (بعد الاكتمال): /reset\n\n"
        "بعد /create ستحصل على رابط مشاركة يمكنك إرساله للآخرين."
    )

async def create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    data = load_data()
    # تأكد إن صاحب الحساب ما عنده ختمة مسبقًا
    for code, info in data["khatmahs"].items():
        if info.get("owner") == user.id:
            link = f"https://t.me/{context.bot.username}?start={code}"
            await update.message.reply_text(f"لديك ختمة سابقة، رابطها:\n{link}")
            return
    # إنشاء كود سري جديد (UUID)
    code = str(uuid.uuid4())
    data["khatmahs"][code] = {
        "name": user.full_name or user.first_name or "ختمة خاصة",
        "owner": user.id,
        "parts": {str(i): None for i in range(1, 31)}
    }
    save_data(data)
    link = f"https://t.me/{context.bot.username}?start={code}"
    await update.message.reply_text(
        f"🎉 تم إنشاء ختمتك الخاصة!\n\nرابط المشاركة:\n{link}\n\nاستخدم /parts لعرض أجزاء ختمتك."
    )

async def parts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    data = load_data()
    for code, info in data["khatmahs"].items():
        if info.get("owner") == user.id:
            text = f"ختمتك: {info.get('name','')}\nاضغط على جزء للحجز أو الإكمال:"
            markup = build_markup(code, info)
            await update.message.reply_text(text, reply_markup=markup)
            return
    await update.message.reply_text("❌ لم تقم بإنشاء ختمة خاصة بعد. اكتب /create")

async def shared_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    shared = data["khatmahs"].get("shared")
    if not shared:
        data["khatmahs"]["shared"] = {
            "name": "الختمة المشتركة",
            "owner": None,
            "parts": {str(i): None for i in range(1, 31)}
        }
        save_data(data)
        shared = data["khatmahs"]["shared"]
    text = "الختمة المشتركة - اضغط جزء للحجز أو الإكمال:"
    markup = build_markup("shared", shared)
    await update.message.reply_text(text, reply_markup=markup)

# ---- معالِج ضغط الأزرار (الحجز/الإكمال) ----
async def reserve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user = query.from_user

    parts = query.data.split("|", 2)
    if len(parts) < 3:
        await query.answer("خطأ في البيانات.", show_alert=True)
        return
    _, kh_code, part_number = parts
    kh = data["khatmahs"].get(kh_code)
    if not kh:
        await query.answer("الختمة غير موجودة.", show_alert=True)
        return

    p = kh["parts"].get(part_number)

    # متاح -> نحجز (inprogress)
    if p is None:
        kh["parts"][part_number] = {"status": "inprogress", "by": user.id, "by_name": user.full_name or user.first_name}
        save_data(data)
        # حدث النص في الرسالة التي عرضت الأزرار (إن أمكن)
        try:
            await query.edit_message_text(text=f"ختمة: {kh.get('name')}\n✅ تم حجز الجزء {part_number}.", reply_markup=build_markup(kh_code, kh))
        except Exception:
            pass

        # إرسال المعاينة (الصورة) والـ PDF للمستخدم في رسالة خاصة
        file_index = int(part_number) - 1
        photo_name = f"photo-output {part_number}.JPEG"  # اسم الصورة كما عندك
        pdf_name = f"part{part_number}.pdf"
        arabic_pdf_name = f"{part_names[file_index]}.pdf"

        # حاول الإرسال في الخاص، وإلا أعلم في المحادثة
        try:
            if os.path.exists(photo_name):
                with open(photo_name, "rb") as ph:
                    await context.bot.send_photo(chat_id=user.id, photo=ph, caption=f"📖 {part_names[file_index]}\nجزاك الله خيرًا — تم حجز هذا الجزء لك.")
            if os.path.exists(pdf_name):
                # نرسل الملف مع اسم عربي
                with open(pdf_name, "rb") as pdf:
                    await context.bot.send_document(chat_id=user.id, document=pdf, filename=arabic_pdf_name)
            else:
                # إن لم يوجد PDF، نرسل رسالة نصية بدلًا من الملف
                await context.bot.send_message(chat_id=user.id, text=f"ملف {arabic_pdf_name} غير موجود على الخادم.")
        except Exception as e:
            logger.info(f"Could not send private message: {e}")
            # نخبر المستخدم في نفس المحادثة العامة
            try:
                await query.message.reply_text("✅ تم الحجز، لكن لم أستطع إرسال الملف في الخاص (ربما لم تبدأ محادثة خاصة مع البوت).")
            except Exception:
                pass
        return

    # الحالة inprogress -> محاولة إكمال (إذا نفس الشخص)
    if isinstance(p, dict) and p.get("status") == "inprogress":
        if p.get("by") == user.id:
            kh["parts"][part_number] = {"status": "done", "by": user.id, "by_name": user.full_name or user.first_name}
            save_data(data)
            try:
                await query.edit_message_text(text=f"ختمة: {kh.get('name')}\n🎉 تم إكمال الجزء {part_number}.", reply_markup=build_markup(kh_code, kh))
            except Exception:
                pass
            # لو كل الأجزاء مكتملة -> نخبر صاحب الختمة (أو المحادثة)
            if all(isinstance(v, dict) and v.get("status") == "done" for v in kh["parts"].values()):
                try:
                    await query.message.reply_text("🌟 ألف مبروك! اكتملت الختمة بالكامل. يمكن لصاحب الختمة إعادة البدء باستخدام /reset")
                except Exception:
                    pass
                owner = kh.get("owner")
                if owner:
                    try:
                        await context.bot.send_message(chat_id=owner, text=f"🌟 ختمتك ({kh.get('name')}) اكتملت بالكامل!")
                    except Exception:
                        pass
            return
        else:
            await query.answer("❌ هذا الجزء محجوز لشخص آخر.", show_alert=True)
            return

    # حالة مكتمل مسبقاً
    if isinstance(p, dict) and p.get("status") == "done":
        await query.answer("✅ هذا الجزء مكتمل بالفعل.", show_alert=True)
        return

# ---- إعادة الختمة (بعد الاكتمال) ----
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    data = load_data()
    for code, info in data["khatmahs"].items():
        if info.get("owner") == user.id:
            parts = info["parts"]
            if not all(isinstance(v, dict) and v.get("status") == "done" for v in parts.values()):
                await update.message.reply_text("❌ لا يمكنك إعادة الختمة قبل إكمال جميع الأجزاء.")
                return
            data["khatmahs"][code]["parts"] = {str(i): None for i in range(1, 31)}
            save_data(data)
            await update.message.reply_text("♻️ تم إعادة بدأ ختمتك الخاصة. استخدم /parts لعرض الأجزاء.")
            return
    await update.message.reply_text("❌ لم نعثر على ختمة خاصة بك. استخدم /create لإنشاء واحدة.")

# ---- تسجيل وتشغيل البوت ----
def main():
    # حاول تشغيل keep-alive لو الملف موجود (تجنّب الخطأ إن لم يوجد)
    try:
        import keep_alive
        keep_alive.keep_alive()
        logger.info("keep_alive started")
    except Exception as e:
        logger.info(f"keep_alive not started: {e}")

    ensure = ensure_data_file
    ensure()
    # تحقق من التوكن
    if not TOKEN:
        logger.error("TOKEN not set. ضع TOKEN كـ environment variable أو اضف التوكن في الكود.")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create", create))
    app.add_handler(CommandHandler("parts", parts_command))
    app.add_handler(CommandHandler("shared", shared_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CallbackQueryHandler(reserve_handler, pattern=r"^res\|"))
    logger.info("🤖 البوت يعمل الآن")
    app.run_polling()

if __name__ == "__main__":
    main()