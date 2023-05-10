from subprocess import run
from os import getenv, path
from dotenv import load_dotenv

token = (getenv('GITHUB_ACCESS_TOKEN')).strip()
owner = 'curtsy-follicle'
repo_name = 'Duplicate-Railway-Pack'

cmd = f'git clone https://{token}@github.com/{owner}/{repo_name}'

run(cmd, shell=True)

cmd = f'cp {repo_name}/config.env catuserbot/'
path = f'{repo_name}/config.env}'
if path.exists(path):
  load_dotenv(path)
  run(cmd, shell=True')
