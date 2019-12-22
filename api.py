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
user_del = ''


def get_user_id(workspace_id, user_name):
    get_users_path = f'/workspaces/{workspace_id}/users'
    URL = url_base + get_users_path
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': api_key,
        },
    )
    if resp.status_code == 200:
        data = resp.json()
        try:
            # return filter(lambda x: x['name'] == user_name, data)['id']
            return [entry['id'] for entry in data
                    if entry['name'] == user_name][0]
        except IndexError:
            return f'Index Error: {user_name} not found'


def get_project_id(workspace_id, project_name):
    PATH = f'/workspaces/{workspace_id}/projects'
    URL = f'{url_base}{PATH}'
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': api_key,
        }
    )
    # print(f'Reading projects... [Status code: {resp.status_code}]')
    if resp.status_code == 200:
        data = resp.json()
        try:
            return [entry['id'] for entry in data
                    if entry['name'] == project_name][0]
        except IndexError:
            return f'Index Error: {project_name} not found'


def get_workspace_id(workspace):
    PATH = '/workspaces'
    URL = f'{url_base}{PATH}'
    resp = requests.get(
        url=URL,
        headers={
            'X-Api-key': api_key,
        }
    )
    if resp.status_code == 200:
        data = resp.json()
        try:
            return [entry['id']
                    for entry in data if entry['name'] == workspace][0]
        except IndexError:
            return f'Index Error: {workspace} not found'


def delete_entry(workspace_id, entry_id):
    # DELETE /workspaces/{workspaceId}/time-entries/{id}
    PATH = f'/workspaces/{workspace_id}/time-entries/{entry_id}'
    URL = f'{url_base}{PATH}'
    # print(f'Delete entry URL: {URL} \n')
    r = requests.delete(
        url=URL,
        headers={
            'X-Api-key': api_key,
            'Content-type': 'application/json'
        }
    )
    print(f'>>> Time entry {entry_id} on {workspace_id} deleted'
          if r.status_code == 204
          else f'DELETE {PATH} status code {r.status_code}')


def delete_entries(workspace_id, user_name, project_name):
    # GET /workspaces/{workspaceId}/user/{userId}/time-entries
    user_id_source = get_user_id(workspace_id, user_name)
    project_id = get_project_id(workspace_id, project_name)
    page_number = 1
    ended = False
    total_count = 0
    while not ended:
        # PATH = '/workspaces/{}/user/{}/time-entries/?page={}'.format(
        #     workspace_id, user_id_source, page_number)
        PATH = (f'/workspaces/{workspace_id}/user/{user_id_source}'
                f'/time-entries/?page={page_number}')
        URL = f'{url_base}{PATH}'
        resp = requests.get(
            url=URL,
            headers={
                'X-Api-key': api_key,
            },
        )
        print(f'Get time page {page_number} [Status code: {resp.status_code}]')
        counter = 0
        if resp.status_code == 200:
            data = resp.json()
            total_entries = len(data)
            print(f'>>> {total_entries} entries on page for all projects')
            for entry in data:
                if entry['projectId'] == project_id:
                    counter += 1
                    print(f'Entry {entry["description"]} '
                          f'id {entry["id"]} will be deleted')
                    delete_entry(workspace_id, entry['id'])
            print(f'{counter} out of {total_entries} deleted')
            total_count += counter
            if total_entries < 50:
                ended = True
            else:
                page_number += 1
    total_entries_parsed = total_entries + 50*(page_number-1)
    print(f'{page_number} pages parsed, or {total_entries_parsed} entries')
    print(f'{total_count} deleted')


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
            f'Workspace \'{workspace_name}\' already exists Id: {workspace_id}'
        )
        return workspace_id
    else:
        print(f'POST /workspaces/ error code {resp.status_code}')
        return 'Error'


def read_config():
    config_path = default_config_json
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    print(f'JSON configuration file: \'{config_path}\'')
    if not path.exists(config_path):
        print(
            f'JSON configuration file \'{config_path}\' not found')
        print('It should follow the \'config.json\' structure')
        return 'Error'
    with (open(config_path)) as file:
        clockify_data = json.load(file)
    # unpack the keys from the dictionary to individual variables
    print('Reading clockify data from configuration file...')
    for key, val in clockify_data.items():
        exec('global ' + key + '\n' + key + '=val')
        print(key, ' =  ', val)
    return clockify_data


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
    print(f'>>> Added time entry {post_data["description"]}'
          if resp_add.status_code == 201
          else f'POST {PATH_ADD_TE} error code {resp_add.status_code}'
          )


def copy_time_entries(workspace_id, user_name, project_name,
                      workspace_id_dest, user_name_dest, project_name_dest):
    # GET /workspaces/{workspaceId}/user/{userId}/time-entries
    user_id_source = get_user_id(workspace_id, user_name)
    project_id_source = get_project_id(
        workspace_id, project_name_source)
    user_id_dest = get_user_id(workspace_id_dest, user_name_dest)
    page_number = 1
    ended = False
    total_count = 0
    while not ended:
        PATH = (f'/workspaces/{workspace_id}/user/{user_id_source}'
                f'/time-entries/?page={page_number}')
        URL = f'{url_base}{PATH}'
        resp = requests.get(
            url=URL,
            headers={
                'X-Api-key': api_key,
            }
        )
        print(f'Get time page {page_number} [Status code: {resp.status_code}]')
        counter = 0
        if resp.status_code == 200:
            data = resp.json()
            total_entries = len(data)
            print(f'>>> {total_entries} Entries on page for all projects')
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
            print(f'{counter} out of {total_entries} copied')
            total_count += counter
            if total_entries < 50:
                ended = True
            else:
                page_number += 1
    total_entries_parsed = total_entries + 50*(page_number-1)
    print(f'{page_number} pages parsed, or {total_entries_parsed} entries')
    print(f'{total_count} copied')


def main():
    if read_config() == 'Error':
        exit()
    # read_config()
    workspace_id_dest = get_workspace_id(workspace_name_dest)
    # workspace_id_dest = add_workspace(workspace_name_dest)
    # if workspace_id_dest == 'Error':
    #     exit()
    user_id_source = get_user_id(workspace_id, user_name)
    project_id_dest = get_project_id(workspace_id_dest, project_name_dest)
    # myuser = 'Some name'
    # print(f'Checking for user id: {get_user_id(workspace_id, myuser)}')
    # copy_time_entries(workspace_id, user_name, project_name_source,
    #                   workspace_id_dest, user_name_dest, project_name_dest)
    # user_del = 'Some name'

    # print(f'Checking for user id: {get_user_id(workspace_id, user_del)}')
    # delete_entries(workspace_id_dest, user_del, project_name_dest)
    # copy_time_entries(workspace_id, user_name, project_name_source,
    #                   workspace_id_dest, user_name_dest, project_name_dest)
    # ws = 'Beta workspace'
    # print(f'Checking for workspace {ws} id: {get_workspace_id(ws)}')

    # copy_time_entries(workspace_id, user_name, project_name_source,
    #                   workspace_id_dest, user_name_dest, project_name_dest)

    # user_del read from config too
    delete_entries(workspace_id_dest, user_del, project_name_dest)


if __name__ == "__main__":
    # execute only if run as a script
    main()



