import os
from dotenv import load_dotenv
from asyncio import sleep
from subprocess import run

from userbot import BOTLOG_CHATID, catub

from ..core.managers import edit_delete, edit_or_reply
from ..helpers import config_helper as dBcof
from ..helpers.utils import _catutils

plugin_category = "tools"

# =========@ Constants @=========
GITHUB_ACCESS_TOKEN = token = os.getenv('GITHUB_ACCESS_TOKEN', None)
RAILWAY_GIT_REPO_OWNER = owner = os.getenv('RAILWAY_GIT_REPO_OWNER')
RAILWAY_GIT_REPO_NAME = repo_name = os.getenv('RAILWAY_GIT_REPO_NAME')
# ===============================

if token:
    with open('token.txt', 'w+') as t: t.write(token)
    os.unsetenv('GITHUB_ACCESS_TOKEN') # For security purpose.

def load_environtment_variables():
    try: load_dotenv('config.env')
    except: pass

def runcmd(cmd):
    output = run(cmd, shell=True, capture_output=True)

    stdout = (output.stdout).decode()
    stderr = (output.stderr).decode()
    return stdout, stderr

def _repoEdit(check=False):
    """This will ensure that the config repo is private."""
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

    if not token: token = str((open('token.txt')).read()).strip()
    
    cmd = (f"rm -rf {repo_name} && "
           f"git clone https://{token}@github.com/{owner}/{repo_name} && "
           f"cp -f config.env {repo_name} && cd {repo_name} && "
            "git add config.env && git commit -m 'Update config.env' && git push")
    
    stdout, stderr = runcmd(cmd)
    
    stdout, stderr = repoPushConfig(event)
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
            "set": "To set new var in railway or modify the old var",
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
    cmd = event.pattern_match.group(1)
    if cmd == 'info':
        return await edit_delete(event, dBcof.vars_info(), 60)
    
    variable = event.pattern_match.group(2)
    if " " in variable:
        variable, value = variable.split(" ", 1)
    if not variable:
        return await edit_delete(event, "`What to do without Config Var??`")
    if variable in dBcof.var_list:
        cat = await edit_or_reply(event, "`Processing...`")
        data = await dBcof.setup_vars(event, cmd, variable, value)
        return await edit_delete(cat, data)

    if cmd == 'get':
        cat = await edit_or_reply(event, "`Getting information...`")
        val = os.getenv(variable)
        if val is None: 
            return await edit_or_reply(
                cat,
                "**ConfigVars**:" f"\n\n__Error:\n-> __`{variable}`__ does't exist.__",
            )
        return await edit_or_reply(
                    cat, "**ConfigVars**:" f"\n\n`{variable}` = `{val}`"
            )
    
    elif cmd == 'set':
        cat = await edit_or_reply(event, "`Setting information...`")
        if not value:
            return await edit_or_reply(cat, "`.set var <ConfigVars-name> <value>`")
        
        if not repoPushConfig(push=False): return

        try: open('config.env', 'x') 
        except: pass

        done = False
        config = (open('config.env')).readlines()
        for l in config:
            if variable in l:
                newLine = f'{variable} = {value}'
                f = str((open('config.env')).read())
                newConfig = f.replace(l, newLine)
                with open('config.env', 'w+') as f: f.write(newConfig)
                done = True
                # I didn't break it in case someone wrote the variable multiple times.
    
        if not done:
            newLine = f'\n{variable} = {value}'
            with open('config.env', 'a') as config: config.write(newLine)
        
        if not repoPushConfig(): return

        await edit_or_reply(
            cat, f"`{variable}` **successfully changed to  ->  **`{value}`"
        )
        await event.client.send_message(
            BOTLOG_CHATID,
            f"#CONFIG_VAR  #UPDATED\n\n`{variable}` = `{value}`",
            silent=True,
        )
        reload_codebase()
        await event.client.reload(cat)
        load_environtment_variables()
        

    elif cmd == 'del':
        cat = await edit_or_reply(
            event, "`Getting information for deleting a variable...`"
        )

        if not repoPushConfig(push=False): return

        try: open('config.env', 'x') 
        except: pass

        done = False
        config = (open('config.env').readlines())

        for l in config:
            if variable in l:
                f = str((open('config.env')).read())
                newConfig = f.replace(l, '')
                with open('config.env', 'w+') as f: f.write(newConfig)
                done = True
                # I didn't break it in case someone wrote the variable multiple times.
    
        if not done: return await edit_or_reply(cat, f"`{variable}`**  does not exist**")

        if not repoPushConfig(): return

        await edit_or_reply(cat, f"`{variable}`  **successfully deleted**")
        await event.client.send_message(
            BOTLOG_CHATID, f"#CONFIG_VAR  #DELETED\n\n`{variable}`", silent=True
        )
        reload_codebase()
        await event.client.reload(cat)
        load_environtment_variables()


