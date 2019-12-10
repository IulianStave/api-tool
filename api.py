# https://api.clockify.me/api/v1
 
import requests
import json
import sys
from os import name, system, path

default_config_json = 'local.config.json'

def clear():
    # in case the system is linux / mac => name = 'posix'
    if name == 'posix':
        __ = system('clear')
    # in case the system is windows => name = 'nt'
    else:
        __ = system('cls')

# Get userId in workspace based on user name
## GET /workspaces/{workspaceId}/users
def get_user_id(workspace_id, user_name):
    get_users_path = '/workspaces/{}/users'.format(workspace_id)
    URL = URL_BASE + get_users_path
    resp = requests.get(
        url = URL,
        headers = {
            'X-Api-key': API_KEY,
        },
    ) 
    print('\nReading user entries in workspace {}... [Status code: {}] \n'.format(
        workspace_id, resp.status_code))
    if resp.status_code == 200:
        data = resp.json()
        # print('Project entries in workspace {} for project {}'.format(workspace_id, project_name))
        #result = [entry for entry in data if entry['name']==project_name][0]['id']
        #id = [entry for entry in data if entry['name']==project_name][0]['id']
        for entry in data:
            if entry['name'] == user_name:
                return entry['id']
        return 'Error, user {} not found in workspace {}'.format(user_name, workspace_id)
        # return '\nReading project entries in workspace... [Status code: {}] \n'.format(resp.status_code
        # retrun entry['id'] for entry in data if entry['name']==project_name

# Get projectId in destination workspace based on name
## GET /workspaces/{workspaceId}/projects
def get_project_id(workspace_id, project_name):
    #print('\nReading project entries in workspace... [Status code: {}] \n'.format(resp.status_code))
    get_projects_path = '/workspaces/{}/projects'.format(workspace_id)
    URL = URL_BASE + get_projects_path
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': API_KEY,
        },
    )
    print('\nReading project entries in workspace {}... [Status code: {}] \n'.format(
        workspace_id, resp.status_code))
    if resp.status_code == 200:
        data = resp.json()
        # print('Project entries in workspace {} for project {}'.format(workspace_id, project_name))
        #result = [entry for entry in data if entry['name']==project_name][0]['id']
        #id = [entry for entry in data if entry['name']==project_name][0]['id']
        for entry in data:
            if entry['name'] == project_name:
                print('>> Project {} found, id: {}'.format(
                    project_name, entry['id']))
                return entry['id']
        return 'Error, project {} not found in workspace {}'.format(project_name, workspace_id)
        # return '\nReading project entries in workspace... [Status code: {}] \n'.format(resp.status_code
        # retrun entry['id'] for entry in data if entry['name']==project_name


# Add new time entry to workspace
## POST /workspaces/{workspaceId}/time-entries
def put_new_time_entry(workspace_id, post_data):
    PATH_ADD_TE = '/workspaces/{}/time-entries'.format(workspace_id)
    # URL = URL_BASE + PATH_ADD_TE  # use f'
    URL = f'{URL_BASE}{PATH_ADD_TE}'
    resp_add = requests.post(
        url = URL,
        headers = {
            'X-Api-key': API_KEY,
            'Content-type': 'application/json',
        },
        json = post_data
    )
    print(f'>>>>> Succes! New time entry on {workspace_id} has been created, id: {resp_add.json()["id"]}'
          if resp_add.status_code == 201 else f'POST {PATH_ADD_TE} error code {resp_add.status_code}'
          )


# Add new workspace named workspace_name_dest
# PATH /workspaces
def add_workspace(workspace_name):
    PATH_ADD_WS = '/workspaces'
    URL = f'{URL_BASE}{PATH_ADD_WS}'
    resp = requests.post(
        url = URL,
        headers = {
            'X-Api-key': API_KEY,
            'Content-type': 'application/json',
        },
        json = {'name': workspace_name}
    )

    if resp.status_code == 201:
        workspace_id_dest = resp.json()["id"]
        print(
            f'New workspace {workspace_name} created, id: {workspace_id_dest}')
        return workspace_id_dest
    if resp.status_code == 400:
        # already exists, find workspaces for currently logged in user
        PATH_GET_WSID = '/workspaces'
        URL = URL_BASE+PATH_GET_WSID
        resp = requests.get(
            url=URL,
            headers={
                'X-Api-key': API_KEY,
            },
        )
        data = resp.json()
        # and get the id of the already existing workspace identified by name
        workspace_id_dest = [workspace['id']
                            for workspace in data if workspace['name'] == workspace_name][0]
        print(
            f'Workspace \'{workspace_name}\' already exists, id: {workspace_id_dest}')
        return workspace_id_dest
    else:
        print('POST /workspaces/ error code {}'.format(resp.status_code))
        return 'Error'


clear()
config_path = default_config_json
if len(sys.argv) > 1:
    config_path = sys.argv[1]
print(f'JSON configuration file is \'{config_path}\'')
    
if not path.exists(config_path):
    print(f'Error reading configuration JSON file \'{config_path}\'. File not found')
    print('Its location should be the current folder and it should follow the \'config.json\' structure')
    exit()

with (open(config_path)) as file:
    clockify_data = json.load(file)
for key, val in clockify_data.items():  # unpack the keys from the dictionary to individual variables
    exec (key + '=val')
    print(key,' =  ', val)

workspace_id_dest = add_workspace(workspace_name_dest) 
if workspace_id_dest == 'Error':
    exit()
user_id_source = get_user_id(WORKSPACE_ID, user_name)
project_id_dest = get_project_id(workspace_id_dest, project_name_dest)

# get time entries for the project, user
GET_TIME_PATH = '/workspaces/{}/user/{}/time-entries'.format(
    WORKSPACE_ID, user_id_source)
URL = URL_BASE + GET_TIME_PATH
resp = requests.get(
    url = URL,
    headers = {
        'X-Api-key': API_KEY,
    },
)
print('\nReading Time entries in workspace... [Status code: {}] \n'.format(
    resp.status_code))
if resp.status_code == 200:
    data = resp.json()
    project_id_source = get_project_id(WORKSPACE_ID, project_name_source)
    user_id_dest = get_user_id(
                workspace_id_dest, user_name_dest)
    for entry in data:
        if entry['projectId'] == project_id_source:
            # get all the time entries logged on the project `project_id_source`
            # print('ProjectId: {} Start: {} -- End {} '.format(
            #     entry['projectId'], entry['timeInterval']['start'], entry['timeInterval']['end']))

            # build new time entry new_entry and add it to destination workspace
            new_entry = {}
            # start is mandatory
            new_entry['start'] = entry['timeInterval']['start']
            new_entry['end'] = entry['timeInterval']['end']
            new_entry['billable'] = entry['billable']
            new_entry['description'] = entry['description']
            new_entry['timeInterval'] = entry['timeInterval']
            new_entry['projectId'] = project_id_dest
            new_entry['userId'] = user_id_dest
            put_new_time_entry(workspace_id_dest, new_entry)
