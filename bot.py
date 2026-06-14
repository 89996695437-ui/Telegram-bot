async def start(update, context):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("Согласна", callback_data="consent_yes")], [InlineKeyboardButton("Не согласна", callback_data="consent_no")]]
    await update.message.reply_text(CONSENT, reply_markup=InlineKeyboardMarkup(keyboard))

async def send_question(update, context):
    q_idx = context.user_data.get("question", 0)
    q = QUESTIONS[q_idx]
    keyboard = [[InlineKeyboardButton(t, callback_data="ans_"+str(q_idx)+"_"+str(i))] for i,(t,_) in enumerate(q["options"])]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=q["text"], reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_answer(update, context):
    data = update.callback_query.data
    if data == "consent_yes":
        context.user_data["scores"] = {k: 0 for k in RESULTS}
        context.user_data["question"] = 0
        keyboard = [[InlineKeyboardButton("Начать тест", callback_data="start_quiz")]]
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Отлично! 8 вопросов, выбирай честно. Готова?", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if data == "consent_no":
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Хорошо. Если передумаешь - напиши /start")
        return
    if data == "start_quiz":
        context.user_data["scores"] = {k: 0 for k in RESULTS}
        context.user_data["question"] = 0
        await send_question(update, context)
        return
    if data.startswith("ans_"):
        parts = data.split("_")
        qi = int(parts[1])
        oi = int(parts[2])
        if qi != context.user_data.get("question", 0):
            await update.callback_query.answer("Уже отвечено")
            return
        _, sd = QUESTIONS[qi]["options"][oi]
        for k,v in sd.items():
            context.user_data["scores"][k] = context.user_data["scores"].get(k,0)+v
        nq = qi+1
        context.user_data["question"] = nq
        if nq < len(QUESTIONS):
            await send_question(update, context)
        else:
            await show_result(update, context)

async def show_result(update, context):
    sc = context.user_data.get("scores",{})
    w = max(sc, key=sc.get)
    r = RESULTS[w]
    tips = "\n".join("- " + t for t in r["tips"])
    text = "Тест завершен!\n\nТебе нужен: " + r["title"] + "\n\n" + r["desc"] + "\n\nС чего начать:\n" + tips
    keyboard = [[InlineKeyboardButton("Пройти еще раз", callback_data="start_quiz")]]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_answer))
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
