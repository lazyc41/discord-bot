import os
import discord
from discord.ext import commands

# ===== 請確認這三項設定 =====
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1538207896238817313
SUPPORT_ROLE_ID = 1557220597249998948

# 暫時不使用分類就維持 None
CATEGORY_ID = None

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

SERVICES = ["娛樂陪", "技術陪", "代打", "客服"]
GUILD = discord.Object(id=GUILD_ID)
panel_synced = False


class OrderSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=name,
                description=f"建立{name}私人服務頻道"
            )
            for name in SERVICES
        ]
        super().__init__(
            placeholder="請選擇你需要的服務",
            options=options,
            custom_id="service_order_select"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.defer(ephemeral=True)
        if guild is None:
            await interaction.followup.send(
                "請在伺服器內使用這個選單。", ephemeral=True
            )
            return

        # 避免同一人重複建立未完成的服務頻道
        for channel in guild.text_channels:
            if channel.topic == f"order:{interaction.user.id}":
                await interaction.followup.send(
                    f"你已有服務頻道：{channel.mention}",
                    ephemeral=True
                )
                return

        support_role = guild.get_role(SUPPORT_ROLE_ID)
        bot_member = guild.get_member(bot.user.id)

        if support_role is None or bot_member is None:
            await interaction.response.send_message(
                "找不到客服身分組或機器人身分，請檢查設定。",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            support_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            bot_member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True
            )
        }

        category = (
            guild.get_channel(CATEGORY_ID)
            if CATEGORY_ID else None
        )

        try:
            channel = await guild.create_text_channel(
                name=f"{self.values[0]}-{interaction.user.name}",
                topic=f"order:{interaction.user.id}",
                overwrites=overwrites,
                category=(
                    category
                    if isinstance(category, discord.CategoryChannel)
                    else None
                )
            )

            await channel.send(
                f"{interaction.user.mention} 您好！\n"
                f"您選擇的服務是：**{self.values[0]}**\n"
                "請在這裡說明您的需求，客服會盡快協助您。"
            )

            await interaction.response.send_message(
                f"已建立私人服務頻道：{channel.mention}",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "機器人權限不足，請確認它有管理頻道的權限，"
                "且角色排序設定正確。",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "建立頻道失敗，請稍後再試或檢查伺服器設定。",
                ephemeral=True
            )


class OrderView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OrderSelect())


@bot.tree.command(
    name="下單面板",
    description="建立服務下單選單",
    guild=GUILD
)
async def order_panel(interaction: discord.Interaction):
    await interaction.response.send_message(
        "請選擇你需要的服務：",
        view=OrderView()
    )


@bot.event
async def on_ready():
    global panel_synced

    if not panel_synced:
        bot.add_view(OrderView())
        try:
            await bot.tree.sync(guild=GUILD)
            panel_synced = True
            print("斜線指令同步成功")
        except discord.HTTPException as error:
            print(f"指令同步失敗：{error}")

    print(f"機器人已登入：{bot.user}")


bot.run(TOKEN)

