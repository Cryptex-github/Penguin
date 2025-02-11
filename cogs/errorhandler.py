import re
import sys
import traceback

import discord
import humanize
from discord.ext import commands

from utils.fuzzy import finder


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        command = ctx.invoked_with

        # This prevents any commands with local handlers being handled here in on_command_error.
        global match
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        # ignored = (commands.CommandNotFound,)  # if you want to not send error messages
        ignored = ()

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandNotFound):
            failed_command = re.match(rf"^({ctx.prefix})\s*(.*)", ctx.message.content, flags=re.IGNORECASE).group(2)
            matches = finder(failed_command, self.bot.command_list, lazy=False)
            if not matches:
                return
            match = None
            for command in matches:
                cmd = self.bot.get_command(command)
                if not await cmd.can_run(ctx):
                    return
                match = command
                break
            return await ctx.send(embed=ctx.embed(
                description=f"No command called `{command}` found. Did you mean `{match}`?"
            ))

        if isinstance(error, commands.CheckFailure):
            return await ctx.send(embed=ctx.embed(
                description=f'You do not have the correct permissions for `{command}`'
            ))

        if isinstance(error, discord.Forbidden):
            return await ctx.send(embed=ctx.embed(
                description=f'I do not have the correct permissions for `{command}`'
            ))

        if isinstance(error, commands.CommandOnCooldown):
            retry = humanize.precisedelta(error.retry_after, minimum_unit='seconds')
            return await ctx.send(embed=ctx.embed(
                description=f"{command} is on cooldown.\nTry again in {retry}"
            ))

        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(embed=ctx.embed(description=f"{ctx.invoked_with} cannot be used in DM's"))
            except discord.HTTPException:
                pass

        if isinstance(error, commands.MissingRequiredArgument):
            errors = str(error).split(" ", maxsplit=1)
            return await ctx.send(embed=ctx.embed(
                description=f'`{errors[0]}` {errors[1]}\n'
                            f'You can view the help for this command with `{ctx.prefix}help` `{command}`'
            ))

        if isinstance(error, commands.DisabledCommand):
            return await ctx.send(embed=ctx.embed(description=f'`{command}` has been disabled.'))


        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error),
                                  error,
                                  error.__traceback__,
                                  file=sys.stderr)
        formatted = traceback.format_exception(type(error), error, error.__traceback__)
        await ctx.send(f"Something has gone wrong while executing `{command}`:\n"
                       f"```py\n{''.join(formatted)}\n```")


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
