import os
import json
import sys
import re
from github import Github

DATA_FILE = 'clicks_data.json'
README_FILE = 'README.md'

with open(DATA_FILE, 'r') as f:
    data = json.load(f)

token = os.environ['GITHUB_TOKEN']
repo_name = os.environ['GITHUB_REPOSITORY']
issue_author = os.environ['ISSUE_AUTHOR']

issue_title = sys.argv[1]
if 'Move Up' in issue_title:
    delta = 1
elif 'Move Down' in issue_title:
    delta = -1
else:
    print('Unknown issue title.')
    sys.exit(0)

data['score'] += delta
data['user_counts'][issue_author] = data['user_counts'].get(issue_author, 0) + 1

if issue_author not in data['recent_clickers']:
    data['recent_clickers'].insert(0, issue_author)
    if len(data['recent_clickers']) > 10:
        data['recent_clickers'].pop()

with open(DATA_FILE, 'w') as f:
    json.dump(data, f, indent=2)

leaderboard_list = sorted(data['user_counts'].items(), key=lambda x: x[1], reverse=True)[:5]
leaderboard_md = '\n'.join([f"{idx+1}. {user} ({score})" for idx, (user, score) in enumerate(leaderboard_list)])

with open(README_FILE, 'r') as f:
    readme_content = f.read()

def replace_between_markers(content, marker, new_value):
    pattern = re.compile(
        rf'(<!--{marker}_START-->)(.*?)(<!--{marker}_END-->)',
        re.DOTALL
    )
    return pattern.sub(rf'\1 {new_value} \3', content)

readme_content = replace_between_markers(readme_content, 'SCORE', str(data['score']))
readme_content = replace_between_markers(readme_content, 'RECENT', ', '.join(data['recent_clickers']))
readme_content = replace_between_markers(readme_content, 'LEADERBOARD', leaderboard_md)

g = Github(token)
repo = g.get_repo(repo_name)

contents = repo.get_contents('README.md')
latest_sha = contents.sha
remote_content = contents.decoded_content.decode()

if readme_content != remote_content:
    repo.update_file(
        path='README.md',
        message='Update click score and leaderboard',
        content=readme_content,
        sha=latest_sha
    )
    print("README.md updated successfully.")
else:
    print("No changes in README.md, skipping update.")

json_contents = repo.get_contents(DATA_FILE)
latest_sha_json = json_contents.sha
remote_json_content = json_contents.decoded_content.decode()

new_json_str = json.dumps(data, indent=2)
if new_json_str != remote_json_content:
    repo.update_file(
        path=DATA_FILE,
        message='Update clicks data',
        content=new_json_str,
        sha=latest_sha_json
    )
    print("clicks_data.json updated successfully.")
else:
    print("No changes in clicks_data.json, skipping update.")
