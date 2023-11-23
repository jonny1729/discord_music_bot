import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

token = os.getenv('DISCORD_BOT_TOKEN')


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

is_loop = False
last_played_url = ""
current_track_title = None
current_track_url = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name="help", help="利用可能なコマンドとその説明を表示します。")
async def custom_help(ctx, *commands : str):
    """Shows this message"""

    # ヘルプメッセージを構築
    help_embed = discord.Embed(title="ヘルプ", description="利用可能なコマンドの一覧です", color=0x42f57e)

    for command in bot.commands:
        help_embed.add_field(name=command.name, value=command.help, inline=False)

    await ctx.send(embed=help_embed)

@bot.command(name = "join", help = "コマンドを実行したユーザーのVCに参加します。")
async def join(ctx):
    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    else:
        await ctx.voice_client.move_to(channel)

@bot.command(name = "loop", help ="曲のループのオン/オフを変更します。")
async def loop(ctx):
    global is_loop
    is_loop = not is_loop
    await ctx.send("Loop機能が" + ("オンに変更されました。" if is_loop else "オフに変更されました。"))

@bot.command(name ="play", help ="指定されたURLの音楽を再生します。")
async def play(ctx, url, volume: float = 0.05):
    global last_played_url, current_track_title, current_track_url
    last_played_url = url

    # yt_dlpのフォーマットオプションを定義
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }

    with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
        info = ydl.extract_info(url, download=False)
        current_track_title = info.get('title')
        current_track_url = url
        url2 = info['url']

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    else:
        await ctx.voice_client.move_to(channel)

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }
    vc = ctx.voice_client
    vc.stop()
    audio_source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS)
    vc.play(discord.PCMVolumeTransformer(audio_source, volume=volume), after=lambda e: asyncio.run_coroutine_threadsafe(after_playing(e, ctx), bot.loop).result())

async def after_playing(error, ctx):
    if is_loop:
        await play(ctx, last_played_url)

@bot.command(name ="status", help="現在再生中の曲の名前/URLとループ機能の有無を表示します。")
async def status(ctx):
    if current_track_title is not None and current_track_url is not None:
        await ctx.send(f"現在再生中の曲: {current_track_title}\nURL: {current_track_url}\nループ状態: {'オン' if is_loop else 'オフ'}")
    else:
        await ctx.send("現在再生中の曲はありません。")

@bot.command(name="leave", help="ボイスチャンネルから退出します。")
async def leave(ctx):
    await ctx.voice_client.disconnect()

bot.run(token)


