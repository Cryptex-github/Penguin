import traceback

import discord

def traceback_maker(err, advance: bool = True):
    """A way to debug your code anywhere"""
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = '```py\n{1}{0}: {2}\n```'.format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"

async def qembed(ctx, text):
    bot = ctx.bot
    embed = discord.Embed(description=text[:2048], color=bot.embed_color, timestamp=ctx.message.created_at).set_footer(
        text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

def plural(text, size):
    logic = size == 1
    target = (("(s)", ("s", "")), ("(is/are)", ("are", "is")))
    for x, y in target:
        text = text.replace(x, y[logic])
    return text
