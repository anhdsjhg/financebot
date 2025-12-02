from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import async_to_sync
import json
import random

TOKEN = "8050416803:AAH-H_CWnRgJ2n5MoQYzshVIqU-jhrjeJus"
bot = Bot(token=TOKEN)

# Максимальное количество покупок за игру
MAX_PURCHASES = 6

# Состояние пользователей
user_states = {}  # {chat_id: {...}}

quiz_questions = [
    {"question": "Не жақсы: бірден сатып алу немесе ақша жинау?",
     "options": ["Бірден сатып алу", "Ақша жинау", "Маңызды емес"],
     "correct": 1,
     "explanation": "Ақша жинаған дұрыс, импульсивті сатып алудан аулақ болу үшін."},

    {"question": "Пайдаға жарамды бағаны қалай анықтауға болады?",
     "options": ["Бағаларды салыстыру", "Көргенін алу", "Достардан сұрау"],
     "correct": 0,
     "explanation": "Әрқашан әр жердегі бағаларды салыстырыңыз."},

    {"question": "Артық шығынды болдырмау үшін не істеу керек?",
     "options": ["Тізім жасау", "Көңіл-күймен алу", "Достармен бірге бару"],
     "correct": 0,
     "explanation": "Тізім шығынды бақылауға көмектеседі."},

    {"question": "Қайсысы дұрысырақ?",
     "options": ["Жеңілдікті күту", "Толық бағамен алу", "Жеңілдікке сенбеу"],
     "correct": 0,
     "explanation": "Жеңілдіктер үнемдеуге көмектеседі."},

    {"question": "Бюджет жүргізу не үшін қажет?",
     "options": ["Шығынды бақылау үшін", "Уақыт жоғалту", "Қызық үшін"],
     "correct": 0,
     "explanation": "Бюджет ақшаңызды басқаруды жеңілдетеді."},

    {"question": "Сатып аларда не маңызды?",
     "options": ["Сапа", "Түс", "Танымалдығы"],
     "correct": 0,
     "explanation": "Сапалы зат ұзақ уақыт шыдайды, сондықтан тиімді."}
]


tips_list = [
    "Сатып алмас бұрын әрдайым бағаларды салыстырыңыз.",
    "Чекті сұраңыз — шығынды бақылау оңай болады.",
    "Сатып алатын заттар тізімін алдын ала жасаңыз.",
    "Импульсивті сатып алудан аулақ болыңыз — 24 сағат ережесін қолданыңыз.",
    "Қажет емес жазылымдарды тексеріп, өшіріңіз.",
    "Үнемдеу үшін үйде тамақ дайындап көріңіз.",
    "Қымбат заттар алғанша, сапалы және ұзақмерзімді заттарды таңдаңыз.",
    "Ай сайын кіріс-шығыс жоспарын жасаңыз.",
    "Жеңілдіктер мен акцияларды бақылап отырыңыз.",
    "«Қажет пе, әлде қалайды ма?» деген сұрақ қойыңыз."
]


# Мини-игра: корзина
shop_items_master = [
    {"name": "Рюкзак", "price": 4000, "points": 10},
    {"name": "Кітап", "price": 1500, "points": 5},
    {"name": "Снэк", "price": 500, "points": 2},
    {"name": "Ойыншық", "price": 2500, "points": 7},
    {"name": "Шыны кружка", "price": 1000, "points": 3},
    {"name": "Футболка", "price": 1200, "points": 4},
    {"name": "Блокнот", "price": 800, "points": 3},
    {"name": "Су бөтелкесі", "price": 700, "points": 2},
    {"name": "Сағат", "price": 3500, "points": 8},
    {"name": "Ланчбокс", "price": 900, "points": 3},
]

myths_facts = [
    {"statement": "Көп табыс тапсаң, ақша жинау оңайырақ болады.",
     "is_true": False,
     "explanation": "Үнемдеу әдеті табыс мөлшерінен маңызды."},

    {"statement": "Бағаларды салыстыру ақша үнемдеуге көмектеседі.",
     "is_true": True,
     "explanation": "Иә, әрдайым бағаларды салыстырыңыз."},

    {"statement": "Бәріне несие алу арқылы тез сатып алған дұрыс.",
     "is_true": False,
     "explanation": "Несие шығынды көбейтеді және бюджетті қиындатады."},

    {"statement": "Жеңілдікпен алған әрқашан тиімді.",
     "is_true": False,
     "explanation": "Жеңілдік тек қажет затқа болса ғана пайдалы."},

    {"statement": "Ақшаны тек үлкен сатып алуларға жинау керек.",
     "is_true": False,
     "explanation": "Күнделікті үнемдеу де өте маңызды."},

    {"statement": "Қымбат зат әрқашан сапалы.",
     "is_true": False,
     "explanation": "Сапа бағаға емес, өндірушіге байланысты."},

    {"statement": "Бюджет жасау — қиын нәрсе.",
     "is_true": False,
     "explanation": "Қарапайым тізімнің өзі бюджет болып саналады."},

    {"statement": "Қолма-қол ақшамен төлеу шығынды азайтады.",
     "is_true": True,
     "explanation": "Картаға қарағанда нақты ақшаны бақылау жеңіл."},

    {"statement": "Арнайы орынға жинақтау — табысы төмен адамдарға пайдалы емес.",
     "is_true": False,
     "explanation": "Жинақтау кез келген адамға пайдалы."},

    {"statement": "Сатып алу тізімі артық шығынды азайтады.",
     "is_true": True,
     "explanation": "Тізімсіз барған адам көбірек жұмсайды."}
]


# Главное меню
async def send_main_menu(chat_id):
    keyboard = [
        [InlineKeyboardButton("📊 Викторина", callback_data='quiz')],
        [InlineKeyboardButton("🎮 Мини-ойын «Себет»", callback_data='game')],
        [InlineKeyboardButton("💡 Кеңестер", callback_data='tips')],
        [InlineKeyboardButton("🧐 Мифтер мен фактілер", callback_data='myths')],
        [InlineKeyboardButton("🎯 Қаржылық мақсаттар", callback_data='goals')],
        [InlineKeyboardButton("📒 Жеке бюджет", callback_data='budget')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id=chat_id, text="Бөлімді таңдаңыз:", reply_markup=reply_markup)

# Квиз
async def send_quiz(chat_id):
    state = user_states.setdefault(chat_id, {"quiz_index": 0, "quiz_score": 0})
    index = state.get("quiz_index", 0)

    if index >= len(quiz_questions):
        score = state.get("quiz_score", 0)
        await bot.send_message(chat_id=chat_id, text=f"Викторина аяқталды! Нәтиже: {score}/{len(quiz_questions)}")
        state["quiz_index"] = 0
        state["quiz_score"] = 0

        await send_main_menu(chat_id)
        return

    q = quiz_questions[index]
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"quiz_answer_{i}")] for i, opt in enumerate(q["options"])]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id=chat_id, text=q["question"], reply_markup=reply_markup)

# Советы
async def send_tip(chat_id):
    tip = random.choice(tips_list)
    await bot.send_message(chat_id=chat_id, text=f"💡 Кеңес:\n{tip}")

# ================== Финансовые цели ==================
async def send_goals_menu(chat_id):
    state = user_states.setdefault(chat_id, {})
    goals = state.setdefault("goals", [])
    keyboard = [
        [InlineKeyboardButton("➕ Жаңа мақсат жасау", callback_data="create_goal")],
        [InlineKeyboardButton("💰 Мақсатқа ақша қосу", callback_data="add_to_goal")],
        [InlineKeyboardButton("📊 Прогресті қарау", callback_data="view_goals")],
        [InlineKeyboardButton("🔙 Негізгі менюға оралу", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id, text="Әрекетті таңдаңыз:", reply_markup=reply_markup)


# Создание цели
async def create_goal(chat_id, title=None, amount=None):
    state = user_states.setdefault(chat_id, {})
    goals = state.setdefault("goals", [])

    if title and amount:
        goals.append({"title": title, "amount": amount, "saved": 0})
        await bot.send_message(chat_id, f"✅ Мақсат '{title}' қосылды! Мақсат сомасы: {amount} тг")
        await send_goals_menu(chat_id)
    else:
        await bot.send_message(chat_id, "Мақсатты енгізіңіз: Атауы - Сома")
        # здесь нужно добавить обработку следующего сообщения пользователя

# Добавление денег к цели
async def add_to_goal(chat_id, goal_index=None, amount=None):
    state = user_states.setdefault(chat_id, {})
    goals = state.get("goals", [])
    if goal_index is not None and amount is not None:
        goals[goal_index]["saved"] += amount
        await bot.send_message(chat_id, f"💰 {amount} тг '{goals[goal_index]['name']}' мақсатына қосылды!")
        await send_goals_menu(chat_id)
    else:
        await bot.send_message(chat_id, "Қосқыңыз келген мақсат пен соманы таңдаңыз (қазір қарапайым мәтін арқылы жасауға болады).")

# Просмотр прогресса
async def view_goals(chat_id):
    state = user_states.setdefault(chat_id, {})
    goals = state.get("goals", [])
    if not goals:
        await bot.send_message(chat_id, "🎯 Сізде мақсатыңыз жоқ.")
    else:
        text = "📊 Мақсаттарыңыз:\n"
        for i, goal in enumerate(goals):
            text += f"{i+1}. {goal['name']}: {goal['saved']}/{goal['amount']} тг\n"
        await bot.send_message(chat_id, text)
    await send_goals_menu(chat_id)

async def send_budget_menu(chat_id):
    keyboard = [
        [InlineKeyboardButton("➕ Табыс қосу", callback_data="add_income")],
        [InlineKeyboardButton("➖ Шығын қосу", callback_data="add_expense")],
        [InlineKeyboardButton("📊 Бюджетті қарау", callback_data="view_budget")],
        [InlineKeyboardButton("🔙 Менюға қайту", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id, text="Әрекетті таңдаңыз:", reply_markup=reply_markup)

# Добавление дохода
async def add_income(chat_id, amount=None, category=None):
    state = user_states.setdefault(chat_id, {})
    incomes = state.setdefault("incomes", [])
    if amount and category:
        incomes.append({"amount": amount, "category": category})
        await bot.send_message(chat_id, f"✅ Табыс қосылды: {amount} тг ({category})")
        await send_budget_menu(chat_id)

# Добавление расхода
async def add_expense(chat_id, amount=None, category=None):
    state = user_states.setdefault(chat_id, {})
    expenses = state.setdefault("expenses", [])
    if amount and category:
        expenses.append({"amount": amount, "category": category})
        await bot.send_message(chat_id, f"✅ Шығын қосылды: {amount} тг ({category})")
        await send_budget_menu(chat_id)

# Просмотр бюджета
async def view_budget(chat_id):
    state = user_states.setdefault(chat_id, {})
    incomes = sum([i["amount"] for i in state.get("incomes", [])])
    expenses = sum([e["amount"] for e in state.get("expenses", [])])
    balance = incomes - expenses
    await bot.send_message(chat_id, f"💵 Табыс: {incomes} тг\n💸 Шығын: {expenses} тг\n💰 Баланс: {balance} тг")
    await send_budget_menu(chat_id)


# Начало мини-игры «Корзина»
async def start_shop_game(chat_id):
    state = user_states.setdefault(chat_id, {"budget": 10000})
    state["budget"] = 10000
    state["points"] = 0
    state["selected_items"] = []
    state["shop_items"] = random.sample(shop_items_master, k=len(shop_items_master))  # случайный набор
    await send_shop_items(chat_id)

async def send_shop_items(chat_id):
    state = user_states.get(chat_id)
    if not state:
        await start_shop_game(chat_id)
        return

    budget = state.get("budget", 0)
    selected = state.get("selected_items", [])
    shop_items = state.get("shop_items", [])

    keyboard = []
    for i, item in enumerate(shop_items):
        label = f"{item['name']} - {item['price']} теңге"
        if item["name"] in selected:
            label += " ✅ Сатып алынды"

        # Если достигнут лимит покупок, блокируем кнопки покупки
        if len(selected) < MAX_PURCHASES:
            keyboard.append([InlineKeyboardButton(label, callback_data=f"buy_{i}")])
        else:
            keyboard.append([InlineKeyboardButton(label + " ❌ Лимит таусылды", callback_data="none")])

    keyboard.append([InlineKeyboardButton("Сатып алуды аяқтау", callback_data="finish_shopping")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id=chat_id, text=f"💰 Ваш бюджет: {budget} теңге\nТауарды таңдаңыз:", reply_markup=reply_markup)

# Обработка покупок с лимитом и бонусами
async def handle_shop_game(chat_id, data):
    state = user_states.get(chat_id)
    if not state:
        await start_shop_game(chat_id)
        return

    shop_items = state.get("shop_items", [])
    selected = state.get("selected_items", [])
    budget = state.get("budget", 0)

    if data.startswith("buy_"):
        if len(selected) >= MAX_PURCHASES:
            await bot.send_message(chat_id=chat_id, text=f"❌ Сатып алу лимитіңіз таусылды ({MAX_PURCHASES})!")
            await send_shop_items(chat_id)
            return

        index = int(data.split("_")[-1])
        item = shop_items[index]

        if item["price"] > budget:
            await bot.send_message(chat_id=chat_id, text=f"❌ {item['name']} алуға қаржы жеткіліксіз!")
            return

        if item["name"] not in selected:
            points_earned = item["points"]
            if item["price"] <= 1000:  # бонус за дешёвый товар
                points_earned += 2
            points_earned += random.randint(0, 3)  # случайный бонус

            state["budget"] -= item["price"]
            state["points"] += points_earned
            selected.append(item["name"])

            await bot.send_message(chat_id=chat_id,
                                   text=f"✅ Сіз сатып алдыңыз {item['name']}! Сатып алудан ұпай: {points_earned} "
                                        f"Қалған қаржы: {state['budget']} теңге")
        else:
            await bot.send_message(chat_id=chat_id, text=f"ℹ️ {item['name']} Сатып алынып қойған. Ұпай жоқ.")

        await send_shop_items(chat_id)

    elif data == "finish_shopping":
        await finish_shop_game(chat_id)

# Завершение игры
async def finish_shop_game(chat_id):
    state = user_states.get(chat_id)
    if not state:
        return

    selected_items = state.get("selected_items", [])
    total_points = state.get("points", 0)
    remaining = state.get("budget", 0)

    # Ранжирование
    if total_points <= 10:
        rank = "Жаңадан бастаған"
    elif total_points <= 20:
        rank = "Бюджет бойынша сарапшы"
    else:
        rank = "Сатып алу шебері"

    items_text = ", ".join(selected_items) if selected_items else "ничего"
    await bot.send_message(chat_id=chat_id,
                           text=f"🎉 Ойын аяқталды!\nСатып алынған заттар: {items_text}\nҰпайлар: {total_points}\nДәреже: {rank}\nБюджет қалдығы: {remaining} теңге")
    await send_main_menu(chat_id)
    

async def send_myth(chat_id):
    state = user_states.setdefault(chat_id, {})
    if "myth_index" not in state:
        state["myth_index"] = 0

    index = state["myth_index"]

    if index >= len(myths_facts):
        await bot.send_message(chat_id, text="🎉 Сіз барлық мәлімдемелерді аяқтадыңыз!")
        state["myth_index"] = 0  # сбрасываем для будущих игр
        await send_main_menu(chat_id)  # ← ВОЗВРАТ В МЕНЮ
        return

    statement = myths_facts[index]["statement"]

    keyboard = [
        [InlineKeyboardButton("Шын", callback_data="myth_true")],
        [InlineKeyboardButton("Миф", callback_data="myth_false")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await bot.send_message(chat_id=chat_id, text=statement, reply_markup=reply_markup)


async def handle_myth(chat_id, data):
    state = user_states.setdefault(chat_id, {})
    if "myth_index" not in state:
        state["myth_index"] = 0

    index = state["myth_index"]

    myth = myths_facts[index]

    user_choice = data == "myth_true"
    if user_choice == myth["is_true"]:
        await bot.send_message(chat_id=chat_id, text="✅ Дұрыс!")
    else:
        await bot.send_message(chat_id=chat_id, text="❌ Қате!")

    await bot.send_message(chat_id=chat_id, text="💡 " + myth["explanation"])

    state["myth_index"] += 1

    await send_myth(chat_id)


# Основная обработка коллбэков
processing = {}

async def handle_callback(callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    state = user_states.setdefault(chat_id, {})

    if processing.get(chat_id):
        await bot.answer_callback_query(callback_query.id)
        return

    processing[chat_id] = True

    await bot.answer_callback_query(callback_query.id)

    try:
        # ===== Квиз =====
        if data == "quiz":
            await send_quiz(chat_id)

        elif data.startswith("quiz_answer_"):
            index = state.get("quiz_index", 0)

            if index >= len(quiz_questions):
                await send_quiz(chat_id)
                return

            q = quiz_questions[index]
            selected = int(data.split("_")[-1])

            if selected == q["correct"]:
                state["quiz_score"] = state.get("quiz_score", 0) + 1
                await bot.send_message(chat_id, f"✅ Дұрыс!\n{q['explanation']}")
            else:
                await bot.send_message(chat_id, f"❌ Қате!\n{q['explanation']}")

            state["quiz_index"] = index + 1
            await send_quiz(chat_id)

        # ===== Советы =====
        elif data == "tips":
            await send_tip(chat_id)

        # ===== Мини-игра «Корзина» =====
        elif data == "game":
            await start_shop_game(chat_id)
        elif data.startswith("buy_") or data == "finish_shopping":
            await handle_shop_game(chat_id, data)

        # ===== Мифы и факты =====
        elif data == "myths":
            await send_myth(chat_id)
        elif data in ["myth_true", "myth_false"]:
            await handle_myth(chat_id, data)

        # ===== Финансовые цели =====
        elif data == "goals":
            await send_goals_menu(chat_id)

        elif data == "create_goal":
            state["awaiting_goal_input"] = True
            await bot.send_message(
                chat_id,
                "Мақсатты осы форматта енгізіңіз: Аты - Сома (мысалы: Жаңа телефон - 50000)"
            )

        elif data == "add_to_goal":
            state["awaiting_goal_contribution"] = True
            await bot.send_message(
                chat_id,
                "Мақсаттың номеры мен сомасын енгізіңіз: 1 5000"
            )

        elif data == "view_goals":
            await view_goals(chat_id)

        elif data.startswith("goal_progress:"):
            try:
                index = int(data.split(":")[1])
                goals = state.get("goals", [])

                if 0 <= index < len(goals):
                    goal = goals[index]
                    await bot.send_message(
                        chat_id,
                        f"Мақсат: {goal['name']}\nПрогресс: {goal['saved']}/{goal['amount']} теңге"
                    )
                else:
                    await bot.send_message(chat_id, "❌ Мақсат табылмады.")

            except Exception:
                await bot.send_message(chat_id, "❌ Мақсатты табуда қате.")

        # ===== Бюджет =====
        elif data == "budget":
            await send_budget_menu(chat_id)

        elif data == "add_income":
            state["awaiting_budget_income"] = True
            await bot.send_message(
                chat_id,
                "Табыс форматы: Сома Категория (мысалы: 5000 ЗП)"
            )

        elif data == "add_expense":
            state["awaiting_budget_expense"] = True
            await bot.send_message(
                chat_id,
                "Шығын форматы: Сома Категория (мысалы: 1200 азық-түлік)"
            )

        elif data == "view_budget":
            await view_budget(chat_id)

        # ===== Главное меню =====
        elif data == "main_menu" or data == "back_to_main":
            await send_main_menu(chat_id)

    finally:
        processing[chat_id] = False


@csrf_exempt
def telegram_webhook(request):
    try:
        if request.method == "POST":
            data = json.loads(request.body)

            # -------- Сообщения --------
            if "message" in data and "chat" in data["message"]:
                chat_id = data["message"]["chat"]["id"]
                text = data["message"].get("text", "")
                state = user_states.setdefault(chat_id, {})

                # Создание финансовой цели
                if state.get("awaiting_goal_input"):
                    try:
                        name, amount = map(str.strip, text.split("-", 1))
                        amount = int(amount)
                        goals = state.setdefault("goals", [])
                        goals.append({"name": name, "amount": amount, "saved": 0, "completed": False})
                        state["awaiting_goal_input"] = False
                        async_to_sync(bot.send_message)(chat_id, f"✅ Мақсат '{name}' {amount} теңгеге қосылды!")
                        async_to_sync(send_goals_menu)(chat_id)
                    except Exception:
                        async_to_sync(bot.send_message)(chat_id, "❌ Қате формат. Осы форматта енгізіңіз: Аты - Қаржы сомасы")
                    return JsonResponse({"ok": True})

                # Добавление денег к цели
                elif state.get("awaiting_goal_contribution"):
                    try:
                        index_str, amount_str = text.split()
                        index = int(index_str) - 1
                        amount = int(amount_str)
                        goals = state.get("goals", [])
                        if 0 <= index < len(goals):
                            if goals[index].get("completed", False):
                                async_to_sync(bot.send_message)(
                                    chat_id, f"❌ Мақсат '{goals[index]['name']}' Орындалып қойған! Ақша қоса алмайсыз."
                                )
                            else:
                                goals[index]["saved"] += amount
                                saved = goals[index]["saved"]
                                total = goals[index]["amount"]
                                message = f"💰 С3з мақсатыңызға {amount} теңге қостыңыз '{goals[index]['name']}'\nПрогресс: {saved}/{total} тг"

                                if saved >= total:
                                    goals[index]["completed"] = True
                                    message += f"\n🎉 Құттықтаймын! Мақсатыңызға '{goals[index]['name']}' жеттіңіз!"

                                async_to_sync(bot.send_message)(chat_id, message)
                        else:
                            async_to_sync(bot.send_message)(chat_id, "❌ Мақсаттың номері қате.")
                        state["awaiting_goal_contribution"] = False
                        async_to_sync(send_goals_menu)(chat_id)
                    except Exception:
                        async_to_sync(bot.send_message)(chat_id, "❌ Осы форматта енгізіңіз: номер қаржы сомасы (мысалы: 1 5000)")
                    return JsonResponse({"ok": True})

                # Добавление дохода
                elif state.get("awaiting_budget_income"):
                    try:
                        amount_str, category = text.split(maxsplit=1)
                        amount = int(amount_str)
                        incomes = state.setdefault("incomes", [])
                        incomes.append({"amount": amount, "category": category})
                        async_to_sync(bot.send_message)(chat_id, f"✅ Табыс {amount} ({category}) қосылды!")
                        state["awaiting_budget_income"] = False
                        async_to_sync(send_budget_menu)(chat_id)
                    except Exception:
                        async_to_sync(bot.send_message)(chat_id, "❌ Осы форматта енгізіңіз: Қаржы сомасы Категория (мысалы: 5000 ЗП)")
                    return JsonResponse({"ok": True})

                # Добавление расхода
                elif state.get("awaiting_budget_expense"):
                    try:
                        amount_str, category = text.split(maxsplit=1)
                        amount = int(amount_str)
                        expenses = state.setdefault("expenses", [])
                        expenses.append({"amount": amount, "category": category})
                        async_to_sync(bot.send_message)(chat_id, f"✅ Шығын {amount} ({category}) қосылды!")
                        state["awaiting_budget_expense"] = False
                        async_to_sync(send_budget_menu)(chat_id)
                    except Exception:
                        async_to_sync(bot.send_message)(chat_id, "❌ Осы форматта енгізіңіз: Қаржы сомасы Категория (мысалы: 1500 шоколад)")
                    return JsonResponse({"ok": True})

                # Команда /start
                elif text == "/start":
                    async_to_sync(send_main_menu)(chat_id)
                    return JsonResponse({"ok": True})
                else:
                    async_to_sync(bot.send_message)(chat_id, "Бастау үшін /start бас.")
                    return JsonResponse({"ok": True})

            # -------- Коллбэки --------
            elif "callback_query" in data:
                callback_id = data["callback_query"]["id"]
                chat_id = data["callback_query"]["message"]["chat"]["id"]
                callback_data = data["callback_query"]["data"]
                async_to_sync(handle_callback)(chat_id, callback_data)
                return JsonResponse({"ok": True})

    except Exception as e:
        print("Ошибка обработки запроса:", e)

    return JsonResponse({"ok": True})