import disnake
from disnake.ext import commands
import json

# Конфигурация
config = {
    "token": "MTE3NDcyNTk4NDkxODk3MDM4OA.GlRs0A.gFkfQClM91F3maO-ipESpd1KFTnanQgmJgFXHs",
    "admin_roles": [1089600280817062011],
    "results_channel_id": 1159569295282536509,
    "whitelist_channel_id": 1089600282733854785,
    "accepted_role_id": 1089600280800280689,
    "native_role_id": 1158806346326614076,  # ID "родной роли"
    "accept_message": "@юзер\nВаша анкета на https://discord.com/channels/1089600280779305151/1089600281836269598 была принята!",
    "questions": [
        "Ваше имя и реальный возраст?",
        "Ваш ник в игре?",
        "Как к Вам обращаться? Ваш @Телеграм",
        "Чем вы хотите заниматься на нашем сервере?",
        "Откуда узнали о нашем сервере?"
    ],
    "placeholders": [
        "Дмитрий, 15 лет",
        "DimaUtkin",
        "Дима, @DimaUtkin1487",
        "Строить, общаться, организовать город и клан",
        "Ютуб/Стрим/Тикток/Друзья рассказали"
    ]
}

intents = disnake.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Словарь для хранения состояний анкет пользователей
user_forms = {}

# Команда для создания анкеты
@bot.command()
async def create_form(ctx):
    if ctx.author.guild_permissions.administrator:
        embed = disnake.Embed(
            title="Заполнить анкету",
            description="Нажми кнопку ниже, что бы заполнить анкету и попасть на наш сервер!",
            color=disnake.Color.green()
        )
        components = [disnake.ui.ActionRow(
            disnake.ui.Button(label="Заполнить анкету", custom_id="fill_form", style=disnake.ButtonStyle.success)
        )]
        await ctx.send(embed=embed, components=components)
    else:
        await ctx.send("У вас нет прав для использования этой команды.")

# Обработка нажатия кнопки заполнения анкеты
@bot.listen("on_button_click")
async def handle_button_click(interaction: disnake.MessageInteraction):
    if interaction.data.custom_id == "fill_form":
        if interaction.user.id in user_forms:
            await interaction.response.send_message("Вы уже заполнили анкету.", ephemeral=True)
            return
        
        questions = config["questions"]
        placeholders = config["placeholders"]
        user_forms[interaction.user.id] = {"answers": {}, "message": None}
        
        components = [
            disnake.ui.TextInput(
                label=(question[:42] + '...') if len(question) > 45 else question,
                custom_id=f"q{i}",
                style=disnake.TextInputStyle.short,
                placeholder=placeholders[i]
            ) for i, question in enumerate(questions)
        ]
        
        await interaction.response.send_modal(
            title="Заполнение анкеты",
            custom_id="user_form",
            components=components
        )

# Обработка отправки анкеты
@bot.listen("on_modal_submit")
async def handle_modal_submit(interaction: disnake.ModalInteraction):
    if interaction.data.custom_id == "user_form":
        user_data = user_forms[interaction.user.id]
        questions = config["questions"]
        
        for i, question in enumerate(questions):
            user_data["answers"][question] = interaction.text_values[f"q{i}"]
        
        user_forms[interaction.user.id] = user_data
        
        result_channel = bot.get_channel(config["results_channel_id"])
        if result_channel is None:
            print(f'Error: Канал с ID {config["results_channel_id"]} не найден.')
            await interaction.response.send_message("Произошла ошибка, не удалось найти канал для отправки анкеты.", ephemeral=True)
            return
        
        admin_roles = ", ".join([f"<@&{role_id}>" for role_id in config["admin_roles"]])
        answers_text = "\n\n".join([f"**{q}**:\n{a}" for q, a in user_data["answers"].items()])
        
        embed = disnake.Embed(
            title="Результаты анкеты",
            description=answers_text,
            color=disnake.Color.green()
        )
        
        result_message = await result_channel.send(
            f"{admin_roles}\nПользователь {interaction.user.mention} заполнил анкету:",
            embed=embed,
            components=[
                disnake.ui.ActionRow(
                    disnake.ui.Button(label="Принять", custom_id="accept", style=disnake.ButtonStyle.success),
                    disnake.ui.Button(label="Вайтлист", custom_id="whitelist", style=disnake.ButtonStyle.primary),
                    disnake.ui.Button(label="Аннулировать анкету", custom_id="reset_form", style=disnake.ButtonStyle.secondary),
                    disnake.ui.Button(label="Бан", custom_id="ban", style=disnake.ButtonStyle.danger)
                )
            ]
        )
        
        user_forms[interaction.user.id]["message"] = result_message.id
        await interaction.response.send_message("Ваша анкета отправлена!", ephemeral=True)

# Обработка действий с результатами анкеты
@bot.listen("on_button_click")
async def handle_result_buttons(interaction: disnake.MessageInteraction):
    user_id = next((uid for uid, data in user_forms.items() if data["message"] == interaction.message.id), None)
    if not user_id:
        return
    
    member = interaction.guild.get_member(user_id)
    if member is None:
        print(f'Error: Участник с ID {user_id} не найден.')
        await interaction.response.send_message("Произошла ошибка, не удалось найти участника.", ephemeral=True)
        return
    
    if interaction.data.custom_id == "accept":
        role = interaction.guild.get_role(config['accepted_role_id'])
        native_role = interaction.guild.get_role(config['native_role_id'])
        if role is None:
            print(f'Error: Роль с ID {config["accepted_role_id"]} не найдена.')
            await interaction.response.send_message("Произошла ошибка, не удалось найти роль.", ephemeral=True)
            return
        if native_role is None:
            print(f'Error: Родная роль с ID {config["native_role_id"]} не найдена.')
            await interaction.response.send_message("Произошла ошибка, не удалось найти родную роль.", ephemeral=True)
            return
        try:
            await member.remove_roles(native_role)  # Удаляем родную роль
            await member.add_roles(role)  # Добавляем новую роль
            await member.send(config["accept_message"].replace("@юзер", member.mention))
            await interaction.response.send_message("Пользователь принят.", ephemeral=True)
        except disnake.Forbidden:
            print(f"Error: Не хватает прав для добавления или удаления роли у пользователя {member.display_name}.")
            await interaction.response.send_message("Произошла ошибка, не удалось изменить роли пользователя.", ephemeral=True)
    elif interaction.data.custom_id == "whitelist":
        whitelist_channel = bot.get_channel(config["whitelist_channel_id"])
        if whitelist_channel is None:
            print(f'Error: Канал с ID {config["whitelist_channel_id"]} не найден.')
            await interaction.response.send_message("Произошла ошибка, не удалось найти канал для вайтлиста.", ephemeral=True)
            return
        nickname = user_forms[user_id]["answers"]["Ваш ник в игре?"]
        await whitelist_channel.send(f"easywhitelist add {nickname}")
        await interaction.response.send_message("Пользователь добавлен в вайтлист.", ephemeral=True)
    elif interaction.data.custom_id == "reset_form":
        del user_forms[user_id]
        await member.send("Ваша анкета была аннулирована, вы можете заполнить её заново.")  # Отправляем сообщение пользователю
        await interaction.response.send_message("Анкета аннулирована. Пользователь может заполнить анкету снова.", ephemeral=True)
    elif interaction.data.custom_id == "ban":
        try:
            await member.ban(reason="Заполнение анкеты")
            await member.send("Вы были заблокированы.")  # Отправляем сообщение пользователю
            await interaction.response.send_message("Пользователь забанен.", ephemeral=True)
        except disnake.Forbidden:
            print(f"Error: Не хватает прав для бана пользователя {member.display_name}.")
            await interaction.response.send_message("Произошла ошибка, не удалось забанить пользователя.", ephemeral=True)

try:
    bot.run(config["token"])
except Exception as e:
    print(f"Error: {e}")
