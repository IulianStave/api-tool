import requests
import json
import sys
from os import path

default_config_json = 'local.config.json'
api_key = ''
url_base = ''
workspace_id = ''
workspace_name_dest = ''
user_name = ''
user_name_dest = ''
project_name_source = ''
project_name_dest = ''


def get_user_id(workspace_id, user_name):
    get_users_path = f'/workspaces/{workspace_id}/users'
    URL = url_base + get_users_path
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': api_key,
        },
    )
    # print(f'Getting users in workspace {workspace_id}... \
    #     [Status code: {resp.status_code}]')
    if resp.status_code == 200:
        data = resp.json()
        # print('Project entries in workspace {} for project {}'.format(workspace_id, project_name))
        # result = [entry for entry in data if entry['name']==project_name][0]['id']
        try:
            return [entry['id'] for entry in data if entry['name'] == user_name][0]
        except IndexError:
            return 'Index Error'
        # id = filter(lambda x: x['name'] == user_name, data)['id']


def get_project_id(workspace_id, project_name):
    get_projects_path = f'/workspaces/{workspace_id}/projects'
    URL = url_base + get_projects_path
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': api_key,
        },
    )
    print(f'Reading projects... [Status code: {resp.status_code}]')
    if resp.status_code == 200:
        data = resp.json()
        # print('Project entries in workspace {} for project {}'.format(workspace_id, project_name))
        # result = [entry for entry in data if entry['name']==project_name][0]['id']
        # id = [entry for entry in data if entry['name']==project_name][0]['id']
        for entry in data:
            if entry['name'] == project_name:
                print('>> Project {} found, id: {}'.format(
                    project_name, entry['id']))
                return entry['id']
        return f'Error, {project_name} not found in workspace {workspace_id}'
        # retrun entry['id'] for entry in data if entry['name']==project_name


def add_time_entry(workspace_id, post_data):
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
          if resp_add.status_code == 201 else f'POST {PATH_ADD_TE} \
              error code {resp_add.status_code}'
          )


def delete_entry(workspace_id, entry_id):
    # DELETE /workspaces/{workspaceId}/time-entries/{id}
    PATH = f'/workspaces/{workspace_id}/time-entries/{entry_id}'
    URL = f'{url_base}{PATH}'
    print(f'Delete entry URL: {URL} \n')
    r = requests.delete(
        url=URL,
        headers={
            'X-Api-key': api_key,
        }
    )
    print(f'>>> Time entry {entry_id} on {workspace_id} deleted'
          if r.status_code == 204
          else f'DELETE {PATH} status code {r.status_code}')


def delete_entries(workspace_id, user_name, project_name):
    # GET /workspaces/{workspaceId}/user/{userId}/time-entries
     # get time entries for the project, user
    user_id_source = get_user_id(workspace_id, user_name)
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
        print(
            f'Get Time entries in workspace...[Status code: {resp.status_code}]')
        counter = 0
        if resp.status_code == 200:
            data = resp.json()
            project_id = get_project_id(
                workspace_id, project_name)
            

            print(f'>>> {len(data)} Entries found. All projects')
            for entry in data:
                if entry['projectId'] == project_id:
                    counter += 1
                    print(f'Entry found id {entry["id"]}')
                    # value for start key is mandatory
                    # new_entry['start'] = entry['timeInterval']['start']
                    # new_entry['end'] = entry['timeInterval']['end']
                    # new_entry['billable'] = entry['billable']
                    # new_entry['description'] = entry['description']
                    # new_entry['timeInterval'] = entry['timeInterval']
                    # new_entry['projectId'] = project_id_dest
                    # new_entry['userId'] = user_id_dest
                    delete_entry(workspace_id, entry['id'])

            print(f'Counter: {counter}')
            print(len(data))
            if len(data) < 50:
                ended = True
            else:
                page_number += 1
    print(page_number)


def get_workspace_id(workspace_name):
    # find workspaces for currently logged in user
    PATH = '/workspaces'
    URL = f'{url_base}{PATH}'
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
    return workspace_id_dest


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
        workspace_id = resp.json()["id"]
        print(
            f'New workspace {workspace_name} created, id: {workspace_id}')
        return workspace_id
    if resp.status_code == 400:
        workspace_id = get_workspace_id(workspace_name)
        print(
            f'Workspace \'{workspace_name}\' already exists, id: {workspace_id}'
        )
        return workspace_id
    else:
        print(f'POST /workspaces/ error code {resp.status_code}')
        return 'Error'


def read_config():
    config_path = default_config_json
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    print(f'JSON configuration file is \'{config_path}\'')
    if not path.exists(config_path):
        print(
            f'Configuration JSON file \'{config_path}\' not found')
        print('It should follow the \'config.json\' structure')
        return 'Error'
    with (open(config_path)) as file:
        clockify_data = json.load(file)
    # unpack the keys from the dictionary to individual variables
    print('Reading clockify data from file...')
    for key, val in clockify_data.items():
        exec('global '+key+'\n'+ key + '=val')
        print(key, ' =  ', val)
    return clockify_data


def copy_time_entries(
                        workspace_id, user_name, project_name, 
                        workspace_id_dest, user_name_dest, project_name_dest
                        ):
    # get time entries for the project, user
    user_id_source = get_user_id(workspace_id, user_name)
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
        print(
            f'Get Time entries in workspace...[Status code: {resp.status_code}]')
        counter = 0
        if resp.status_code == 200:
            data = resp.json()
            project_id_source = get_project_id(
                workspace_id, project_name_source)
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
                    add_time_entry(workspace_id_dest, new_entry)

            print(f'Counter: {counter}')
            print(type(resp))
            print(len(data))
            if len(data) < 50:
                ended = True
            else:
                page_number += 1
    print(page_number)


def main():
    if read_config() == 'Error':
        exit()


if __name__ == "__main__":
    # execute only if run as a script
    main()


read_config()
workspace_id_dest = add_workspace(workspace_name_dest)
if workspace_id_dest == 'Error':
    exit()
user_id_source = get_user_id(workspace_id, user_name)
project_id_dest = get_project_id(workspace_id_dest, project_name_dest)
print(f'User passed in json is {user_name} id: {user_id_source}')
myuser = 'User name'
# copy_time_entries(workspace_id, user_name, project_name_source,
#                   workspace_id_dest, user_name_dest, project_name_dest) 
print(f'>>>> Destination workspace {workspace_id_dest} \
::: id: {get_user_id(workspace_id_dest, myuser)} name: {myuser}')
# print('deleting entries')
# delete_entries(workspace_id_dest, myuser, project_name_dest)
# copy_time_entries(workspace_id, user_name, project_name_source,
#                   workspace_id_dest, user_name_dest, project_name_dest)
print(get_workspace_id('workspace name'))
