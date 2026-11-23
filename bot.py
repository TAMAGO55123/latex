"""Markdownを画像化して送信する簡易Discord Bot。"""

import asyncio
import io
import os
import re

from dotenv import load_dotenv

load_dotenv()

import discord
from discord import app_commands
from discord.ext import commands

from md_to_image import render_markdown, RenderError

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("環境変数 DISCORD_BOT_TOKEN を設定してください")

# $$...$$ または同一行内の $...$ を抽出する。
# $ の間に改行がある数式は、メッセージ全体のMarkdown描画対象から除外する。
MATH_EXPRESSION_PATTERN = r"\$\$[\s\S]+?\$\$|(?<!\$)\$[^\$\r\n]+?\$(?!\$)"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.tree.command(name="render", description="Markdownを画像として表示します")
@app_commands.describe(text="Markdownテキスト")
async def render(interaction: discord.Interaction, text: str):
    await interaction.response.defer(thinking=True)
    try:
        buf: io.BytesIO = await asyncio.to_thread(render_markdown, text)
    except RenderError as exc:
        await interaction.followup.send(f"レンダリングエラー: {exc}", ephemeral=True)
        return
    except Exception as exc:
        await interaction.followup.send(f"予期しないエラー: {exc}", ephemeral=True)
        return

    buf.seek(0)
    file = discord.File(buf, filename="render.png")
    await interaction.followup.send(file=file)


@bot.tree.command(name="formula", description="$$で囲んだ表示数式を画像化します")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.describe(formula="$$で囲んだLaTeX式")
async def formula(interaction: discord.Interaction, formula: str):
    """表示数式をユーザー本人にだけ見えるPNGとして返す。"""
    expression = formula.strip()
    if not (expression.startswith("$$") and expression.endswith("$$")):
        await interaction.response.send_message(
            "LaTeX式は $$...$$ の形式で入力してください。",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        buf: io.BytesIO = await asyncio.to_thread(render_markdown, expression)
    except RenderError as exc:
        await interaction.followup.send(
            f"数式レンダリングエラー: {exc}", ephemeral=True
        )
        return
    except Exception as exc:
        await interaction.followup.send(
            f"予期しないエラー: {type(exc).__name__}: {exc}", ephemeral=True
        )
        return

    buf.seek(0)
    await interaction.followup.send(
        file=discord.File(buf, filename="formula.png"),
        ephemeral=True,
    )


@app_commands.context_menu(name="数式を画像化")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.allowed_installs(guilds=False, users=True)
async def formula_from_message(
    interaction: discord.Interaction, message: discord.Message
):
    """メッセージ内の$$...$$または同一行の$...$を抽出して画像化する。"""
    expressions = re.findall(MATH_EXPRESSION_PATTERN, message.content)
    if not expressions:
        await interaction.response.send_message(
            "対象メッセージに $$...$$ または同一行の $...$ 形式のLaTeX式がありません。",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        # 数式の存在だけ確認し、実際にはメッセージ全文をMarkdownとして描画する。
        buf: io.BytesIO = await asyncio.to_thread(render_markdown, message.content)
    except RenderError as exc:
        await interaction.followup.send(
            f"数式レンダリングエラー: {exc}", ephemeral=True
        )
        return
    except Exception as exc:
        await interaction.followup.send(
            f"予期しないエラー: {type(exc).__name__}: {exc}", ephemeral=True
        )
        return

    buf.seek(0)
    await interaction.followup.send(
        file=discord.File(buf, filename="formula.png"),
        ephemeral=True,
    )


bot.tree.add_command(formula_from_message)


if __name__ == "__main__":
    bot.run(TOKEN)
