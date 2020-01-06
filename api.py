"""Clockify API tool - copies or deletes time entries

This script can also be imported as a module
"""

import requests
import json
import argparse
from os import path

default_config_json = 'local.config.json'
api_key = ''
url_base = 'https://api.clockify.me/api/v1'
workspace_id = ''
workspace_name_source = ''
workspace_name_dest = ''
user_name = ''
user_name_dest = ''
project_name_source = ''
project_name_dest = ''
user_del = ''
config_path = ''


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


def get_workspace_name(workspace_id):
    """Checks for workspace existence

    Returns None if not found, on success returns workspace name
    """
    PATH = '/workspaces'
    URL = f'{url_base}{PATH}'
    try:
        resp = requests.get(
            url=URL,
            headers={
                'X-Api-key': api_key,
            }
        )
        resp.raise_for_status()
        if resp.status_code == 200:
            data = resp.json()
            try:
                return [entry['id']
                        for entry in data if entry['id'] == workspace_id][0]
            except IndexError:
                print(f'Index Error: Workspace {workspace_id} not found')
                return None
    except requests.ConnectionError as err:
        print(f'Connection error ::: {err}')
        return None
    except requests.Timeout as err:
        print(f'Timeout error ::: {err}')
        return None
    except requests.HTTPError as err:
        print(f'HTTP error ::: {err}')
        return None
    except requests.RequestException as err:
        print(f'Ambigous Request error ::: {err}')
        return None
    except KeyboardInterrupt:
        print(f'CTRL-C pressed')
        return None


def delete_entry(workspace_id, entry_id):
    # DELETE /workspaces/{workspaceId}/time-entries/{id}
    PATH = f'/workspaces/{workspace_id}/time-entries/{entry_id}'
    URL = f'{url_base}{PATH}'
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
    if user_id_source.startswith('Index Error'):
        print(f'User with id {user_name} not found')
        return
    project_id = get_project_id(workspace_id, project_name)
    page = 0
    ended = False
    count_deleted = 0
    all_entries = 0
    while not ended:
        PATH = (f'/workspaces/{workspace_id}/user/{user_id_source}'
                f'/time-entries')
        URL = f'{url_base}{PATH}'
        resp = requests.get(
            url=URL,
            headers={
                'X-Api-key': api_key,
            },
        )
        print(f'API requests - Status code: {resp.status_code}')
        counter = 0
        if resp.status_code == 200:
            data = resp.json()
            entries_on_page = len(data)
            if not entries_on_page:
                ended = True
                continue
            page += 1
            print(f'Processing page {page}')
            print(f'> {entries_on_page} entries on page for all projects')
            for entry in data:
                if entry['projectId'] == project_id:
                    counter += 1
                    # print(f'Entry {entry["description"]} '
                    #       f'id {entry["id"]} will be deleted')
                    delete_entry(workspace_id, entry['id'])
            print(f'>> {counter} deleted out of {entries_on_page} processed')
            count_deleted += counter
            if entries_on_page < 50:
                ended = True
                all_entries = entries_on_page + 50 * (page - 1)
    if all_entries:
        print(f'{page} page(s) processed')
        print(f'{all_entries} time entries processed')
        print(f'{count_deleted} time entries deleted')
        return
    print('There are no entries to delete')


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
            f'Workspace {workspace_name!r} already exists Id: {workspace_id}'
        )
        return workspace_id
    print(f'POST /workspaces/ error code {resp.status_code}')
    return 'Error'


def get_args():
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(
        '-j',
        '--json',
        action="store",
        dest='config_path',
        help='Store JSON configuration file'
    )
    parser.add_argument(
        '-d',
        '--delete',
        action='store_true',
        default=False,
        dest='delete',
        help='Set a delete operation switch to true')
    parser.add_argument(
        '-c',
        '--copy',
        action='store_true',
        default=False,
        dest='copy',
        help='Set a copy operation switch to true'
    )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s 1.0'
    )
    args = parser.parse_args()
    return args


def read_config(config_path=default_config_json):
    if not path.exists(config_path):
        print(f'JSON configuration file {config_path!r} not found')
        print(f'It should follow the config.json structure')
        return False
    with open(config_path) as file:
        clockify_data = json.load(file)
    # unpack the keys from the dictionary to individual variables
    print(f'\nReading clockify data from {config_path!r}...')
    for key, val in clockify_data.items():
        exec('global ' + key + '\n' + key + '=val')
        print(f'{key:<22} =  {val}')
    return clockify_data


def add_time_entry(workspace_id, post_data):
    PATH = f'/workspaces/{workspace_id}/time-entries'
    URL = f'{url_base}{PATH}'
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
          else f'POST {PATH} error code {resp_add.status_code}'
          )


def copy_time_entries(workspace_id, user_name, project_name,
                      workspace_id_dest, user_name_dest, project_name_dest):
    # GET /workspaces/{workspaceId}/user/{userId}/time-entries
    user_id_source = get_user_id(workspace_id, user_name)
    if user_id_source.startswith('Index Error'):
        print(f'User {user_name} not found')
        return
    project_id_source = get_project_id(
        workspace_id, project_name_source)
    user_id_dest = get_user_id(workspace_id_dest, user_name_dest)
    project_id_dest = get_project_id(workspace_id_dest, project_name_dest)
    page = 1
    ended = False
    count_copied = 0
    while not ended:
        PATH = (f'/workspaces/{workspace_id}/user/{user_id_source}'
                f'/time-entries/?page={page}')
        URL = f'{url_base}{PATH}'
        resp = requests.get(
            url=URL,
            headers={
                'X-Api-key': api_key,
            }
        )
        print(f'Processing page {page} [Status code: {resp.status_code}]')
        counter = 0
        if resp.status_code == 200:
            data = resp.json()
            entries_on_page = len(data)
            print(f'>>> {entries_on_page} entries on page for all projects')
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
            print(f'{counter} out of {entries_on_page} copied')
            count_copied += counter
            if entries_on_page < 50:
                ended = True
            else:
                page += 1
    all_entries = entries_on_page + 50*(page - 1)
    print(f'{page} page(s) processed')
    print(f'Copied {count_copied} entries out of {all_entries} processed')


def main():
    global workspace_id
    config_path = default_config_json
    args = get_args()
    if args.config_path:
        config_path = args.config_path
    print(f'JSON configuration file = {config_path!r}')
    if not read_config(config_path):
        exit()
    # In case the workspace id is not in JSON config
    if workspace_name_source and not workspace_id:
        workspace_id = get_workspace_id(workspace_name_source)
        msg = 'workspace id '
        print(f'{msg:<22} =  {workspace_id:<22}')
    if not workspace_name_source and not workspace_id:
        print(f'Neither workspace id nor workspace name is in {config_path!r}')
        exit()
    workspace_id_dest = get_workspace_id(workspace_name_dest)
    if args.copy:
        print(f'>>> Action chosen: copy time entries')
        copy_time_entries(workspace_id, user_name, project_name_source,
                          workspace_id_dest, user_name_dest, project_name_dest)
    if args.delete:
        print(f'>>> Action chosen: delete time entries')
        delete_entries(workspace_id_dest, user_del, project_name_dest)

    if not args.copy and not args.delete:
        print(f'\nMissing action arguments (copy/delete)\n'
              f'For help, run: python3 {__file__} -h\n')


if __name__ == "__main__":
    # execute only if run as a script
    main()
