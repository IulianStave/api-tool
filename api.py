import requests
import json
import sys
from os import path

default_config_json = 'local.config.json'


def get_user_id(workspace_id, user_name):
    get_users_path = '/workspaces/{}/users'.format(workspace_id)
    URL = url_base + get_users_path
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': api_key,
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
    URL = url_base + get_projects_path
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': api_key,
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
        return 'Error, {project_name} not found in workspace {workspace_id}'
        # retrun entry['id'] for entry in data if entry['name']==project_name


def put_new_time_entry(workspace_id, post_data):
    PATH_ADD_TE = f'/workspaces/{workspace_id}/time-entries'
    URL = f'{url_base}{PATH_ADD_TE}'
    resp_add = requests.post(
        url=URL,
        headers={
            'X-Api-key': api_key,
            'Content-type': 'application/json',
        },
        json=post_data
    )
    print(f'>>>>> Success! New time entry on {workspace_id} has been created'
          if resp_add.status_code == 201 else f'POST {PATH_ADD_TE} error code {resp_add.status_code}'
          )


def add_workspace(workspace_name):
    PATH_ADD_WS = '/workspaces'
    URL = f'{url_base}{PATH_ADD_WS}'
    resp = requests.post(
        url=URL,
        headers={
            'X-Api-key': api_key,
            'Content-type': 'application/json',
        },
        json={'name': workspace_name}
    )

    if resp.status_code == 201:
        workspace_id_dest = resp.json()["id"]
        print(
            f'New workspace {workspace_name} created, id: {workspace_id_dest}')
        return workspace_id_dest
    if resp.status_code == 400:
        # already exists, find workspaces for currently logged in user
        PATH_GET_WSID = '/workspaces'
        URL = url_base+PATH_GET_WSID
        resp = requests.get(
            url=URL,
            headers={
                'X-Api-key': api_key,
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


config_path = default_config_json
if len(sys.argv) > 1:
    config_path = sys.argv[1]
print(f'JSON configuration file is \'{config_path}\'')

if not path.exists(config_path):
    print(
        f'Configuration JSON file \'{config_path}\' not found')
    print('It should follow the \'config.json\' structure')
    exit()

with (open(config_path)) as file:
    clockify_data = json.load(file)
# unpack the keys from the dictionary to individual variables
for key, val in clockify_data.items():
    exec(key + '=val')
    print(key, ' =  ', val)

workspace_id_dest = add_workspace(workspace_name_dest)
if workspace_id_dest == 'Error':
    exit()
user_id_source = get_user_id(workspace_id, user_name)
project_id_dest = get_project_id(workspace_id_dest, project_name_dest)


# get time entries for the project, user
page_number = 1
ended = False
while not ended:

    GET_TIME_PATH = '/workspaces/{}/user/{}/time-entries/?page={}'.format(
        workspace_id, user_id_source, page_number)
    print(GET_TIME_PATH)
    URL = url_base + GET_TIME_PATH
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': api_key,
        }
    )

    print('\nReading Time entries in workspace... [Status code: {}] \n'.format(
        resp.status_code))
    counter = 0
    if resp.status_code == 200:
        data = resp.json()
        project_id_source = get_project_id(workspace_id, project_name_source)
        user_id_dest = get_user_id(
            workspace_id_dest, user_name_dest)

        print(len(data))
        for entry in data:
            if entry['projectId'] == project_id_source:
                counter += 1
                new_entry = {}
                # value for start key is mandatory
                new_entry['start'] = entry['timeInterval']['start']
                new_entry['end'] = entry['timeInterval']['end']
                new_entry['billable'] = entry['billable']
                new_entry['description'] = entry['description']
                new_entry['timeInterval'] = entry['timeInterval']
                new_entry['projectId'] = project_id_dest
                new_entry['userId'] = user_id_dest
                put_new_time_entry(workspace_id_dest, new_entry)

        print('Counter: ', counter)
        print(type(resp))
        print(len(data))
        if len(data) < 50:
            ended = True
        else:
            page_number += 1
