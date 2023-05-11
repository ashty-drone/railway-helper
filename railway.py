import os
import re
from asyncio import sleep
from subprocess import run

from validators.url import url

from userbot import BOTLOG_CHATID, catub

from ..core.managers import edit_delete, edit_or_reply
from ..helpers import config_helper as dBcof
from ..helpers.utils import _catutils

plugin_category = "tools"

# =========@ Constants @=========
RAILWAY_GIT_AUTHOR = author = os.getenv('RAILWAY_GIT_AUTHOR')
GITHUB_ACCESS_TOKEN = token = os.getenv('GITHUB_ACCESS_TOKEN', None)
RAILWAY_GIT_REPO_OWNER = owner = os.getenv('RAILWAY_GIT_REPO_OWNER')
RAILWAY_GIT_REPO_NAME = repo_name = os.getenv('RAILWAY_GIT_REPO_NAME')

config = "./config.py"
var_checker = [
    "APP_ID",
    "PM_LOGGER_GROUP_ID",
    "PRIVATE_CHANNEL_BOT_API_ID",
    "PRIVATE_GROUP_BOT_API_ID",
    "PLUGIN_CHANNEL",
]

default = [
    "./README.md",
    "./config.py",
    "./requirements.txt",
    "./CatTgbot.session",
    "./sample_config.py",
    "./stringsetup.py",
    "./exampleconfig.py",
]

cmds = [
    "rm -rf downloads",
    "mkdir downloads",
]
# ===============================

if token:
    with open('token.txt', 'w+') as t: t.write(token)
    os.unsetenv('GITHUB_ACCESS_TOKEN') # For security purpose.

def runcmd(cmd):
    output = run(cmd, shell=True, capture_output=True)

    stdout = (output.stdout).decode()
    stderr = (output.stderr).decode()
    return stdout, stderr

def _repoEdit(check=False):
    """This will ensure that the config repo is private."""
    GITHUB_ACCESS_TOKEN = token = os.getenv('GITHUB_ACCESS_TOKEN', None)
    
    if check:
        exist = os.path.exists('token.txt')
        if not exist: err = "Token doesn't exist." if not token else False
        else: err = False
    
    if token:
        with open('token.txt', 'w+') as t: t.write(token)
        os.unsetenv('GITHUB_ACCESS_TOKEN') # For security purpose.

    cmd = (
        'gh auth login --with-token < token.txt && '
       f'gh repo edit {owner}/{repo_name} --visibility private'
    )
    stdout, stderr = runcmd(cmd)

    if stderr:
        if 'Visibility is already private' in stderr: error = False
        else: error = True
    else: error = False

    # In a nutshell, if err is False, it's good. Same goes for error.
    if check: 
        if error: return err, stderr
        return err, error
    return error

async def repoPushConfig(event, push=True):
    """This will push the config.env file to your private repo."""
    
    GITHUB_ACCESS_TOKEN = token = os.getenv('GITHUB_ACCESS_TOKEN', None)

    # Well, first we need to check if we can push or not.
    err, error = _repoEdit(check=True)
    message = None

    if err == "Token doesn't exist.":
        message = (
            "Set the required variables in railway to make this function normally.\n"
            "`GITHUB_ACCESS_TOKEN`\n"
            "Please do not report this problem to catuserbot support as this is not official. "
            "Feel free to report it to Lee Kaze")
    if error:
        message = (
            "Some unknown error occured. Here's a brief traceback:\n"
           f"`{error}`\n"
            "Please do not report this in the cat support group as this is not official. "
            "Feel free to report it to Lee Kaze.")
    
    if message:
        cat = await event.reply(
            "Variable change unsuccessful. "
            "Please check your Catuserbot BotLog group.")
        await event.client.send_message(BOTLOG_CHATID, message)
        await sleep(5) ; await cat.delete()
        return False
    
    if not push: return True
  
    if token:
        with open('token.txt', 'w+') as t: t.write(token)
        os.unsetenv('GITHUB_ACCESS_TOKEN') # For security purpose.

    if not token: token = str((open('token.txt')).read()).strip()
    
    cmd = (f"rm -rf {repo_name} && "
           f"git clone https://{token}@github.com/{owner}/{repo_name} && "
           f"cp -f config.py {repo_name} && cd {repo_name} && "
           f"git config user.name {author} && git config user.email {author}@railway.com"
            "git add config.py && git commit -m 'Update config.py' && git push")
    
    run(cmd, shell=True, check=True)
    stderr = ''
    
    if 'error:' in stderr:
        with open('railwayConfigError.txt', 'w+') as r:
            r.write(stderr)
        cat = await event.edit('Some unknown error occured. But Variable changed.. temporarily. '
                               'Please check Catuserbot BotLog Group')
        await event.client.send_message(
            BOTLOG_CHATID,
            'Please do not report this error to catuserbot support as it is unofficial. '
            'Feel free to report it to Lee Kaze',
            file = 'railwayConfigError.txt')
        sleep(5)
        cat.delete()
        return False
    return True

async def reload_codebase():
    with open(config, "r") as f:
        configs = f.read()
    if os.path.exists("catub.log"):
        os.remove("catub.log")
    if os.path.exists("badcatext"):
        await _catutils.runcmd("rm -rf badcatext")
    if os.path.exists("xtraplugins"):
        await _catutils.runcmd("rm -rf xtraplugins")
    if os.path.exists("catvc"):
        await _catutils.runcmd("rm -rf catvc")
    

@catub.cat_cmd(
    pattern="(set|get|del|info) var(?:\s|$)([\s\S]*)",
    command=("var", plugin_category),
    info={
        "header": "To manage config vars.",
        "flags": {
            "set": "To set new var in vps or modify the old var",
            "get": "To show the already existing var value.",
            "del": "To delete the existing value",
            "info": "To get info about current available vars",
        },
        "usage": [
            "{tr}set var <var name> <var value>",
            "{tr}get var <var name>",
            "{tr}del var <var name>",
            "{tr}info var",
        ],
        "examples": [
            "{tr}get var ALIVE_NAME",
        ],
    },
)
async def variable(event):
    "Manage most of ConfigVars setting, set new var, get current var, or delete var..."
    if not os.path.exists(config):
        return await edit_delete(
            event, "`There no Config file , You can't use this plugin.`"
        )
    cmd = event.pattern_match.group(1)
    if cmd == "info":
        return await edit_delete(event, dBcof.vars_info(), 60)
    value = None
    variable = event.pattern_match.group(2)
    if " " in variable:
        variable, value = variable.split(" ", 1)
    if not variable:
        return await edit_or_reply(event, "`What to do without Config Var??`")
    if variable in dBcof.var_list:
        cat = await edit_or_reply(event, "`Processing...`")
        data = await dBcof.setup_vars(event, cmd, variable, value)
        return await edit_delete(cat, data)
    string = ""
    match = None
    with open(config, "r") as f:
        configs = f.readlines()

    if cmd == "get":
        cat = await edit_or_reply(event, "`Getting information...`")
        for i in configs:
            if variable in i:
                _, val = i.split("= ")
                return await edit_or_reply(
                    cat, "**ConfigVars**:" f"\n\n`{variable}` = `{val}`"
                )
        await edit_or_reply(
            cat, "**ConfigVars**:" f"\n\n__Error:\n-> __`{variable}`__ doesn't exists__"
        )

    elif cmd == "set":
        cat = await edit_or_reply(event, "`Setting information...`")
        if not value:
            return await edit_or_reply(cat, "`.set var <ConfigVars-name> <value>`")
        if variable not in var_checker:
            if variable == "EXTERNAL_REPO":
                if bool(value and (value.lower() != "false")) and not url(value):
                    value = "https://github.com/TgCatUB/CatPlugins"
                else:
                    return await edit_or_reply(
                        cat,
                        f"**There no point in setting `{variable}` with `{value}`\nUse `.del var` to delete instead.**",
                    )
            value = f'"{value}"'
        for i in configs:
            if variable in i:
                string += f"    {variable} = {value}\n"
                match = True
            else:
                string += i
        if match:
            await edit_or_reply(
                cat, f"`{variable}` **successfully changed to  ->  **`{value}`"
            )
            logtext = f"#UPDATED\n\n`{variable}` = `{value}`"
        else:
            string += f"    {variable} = {value}\n"
            await edit_or_reply(
                cat, f"`{variable}`**  successfully added with value  ->  **`{value}`"
            )
            logtext = f"#ADDED\n\n`{variable}` = `{value}`"

    elif cmd == "del":
        cat = await edit_or_reply(event, "`Deleting information...`")
        for i in configs:
            if variable in i:
                match = True
            else:
                string += i
        if not match:
            return await edit_or_reply(
                cat,
                "**ConfigVars**:" f"\n\n__Error:\n-> __`{variable}`__ doesn't exists__",
            )
        await edit_or_reply(cat, f"`{variable}` **successfully deleted.**")
        logtext = f"#DELETED\n\n`{variable}`"

    if cmd != "get":
        with open(config, "w") as f1:
            f1.write(string)
            f1.close()
        await event.client.send_message(
            BOTLOG_CHATID, f"#VAR #CONFIG_VAR {logtext}", silent=True
        )
        await repoPushConfig(event)
        await reload_codebase()
        await event.client.reload(cat)


