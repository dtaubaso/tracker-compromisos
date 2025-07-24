import os
import requests
from datetime import datetime
#from dotenv import load_dotenv

#load_dotenv()

ASANA_PAT = os.getenv('ASANA_PAT')

def create_asana_task(name, assignee_email, project_id, due_on=None, description=None, subtasks=None):
    print("Args received:")
    print(f"name={name}, assignee_email={assignee_email}, project_id={project_id}, due_on={due_on}, description={description}, subtasks={subtasks}")
    headers = {
        'Authorization': f'Bearer {ASANA_PAT}',
        'Content-Type': 'application/json'
    }
    
    task_data = {
        'data': {
            'name': name,
            'projects': [project_id]
        }
    }
    
    # Agregar descripción si existe
    if description:
        task_data['data']['notes'] = description
    
    assignee_gid = None
    if assignee_email:
        print(f"Buscando usuario en Asana con email: {assignee_email}")
        assignee_gid = get_user_by_email(assignee_email)
        if assignee_gid:
            print(f"Usuario encontrado en Asana: {assignee_gid}")
            task_data['data']['assignee'] = assignee_gid
        else:
            print(f"Usuario NO encontrado en Asana con email: {assignee_email}")
    
    if due_on:
        try:
            parsed_date = parse_date(due_on)
            if parsed_date:
                task_data['data']['due_on'] = parsed_date
        except:
            pass
    
    response = requests.post(
        'https://app.asana.com/api/1.0/tasks',
        headers=headers,
        json=task_data
    )
    
    if response.status_code == 201:
        task = response.json()['data']
        task_gid = task['gid']
        
        # Crear subtareas si existen
        if subtasks:
            subtask_list = [s.strip() for s in subtasks.split('\n') if s.strip()]
            for subtask_name in subtask_list:
                create_subtask(task_gid, subtask_name, assignee_gid)
        
        return {
            'url': f"https://app.asana.com/0/{project_id}/{task_gid}",
            'assignee_found': assignee_gid is not None
        }
    else:
        raise Exception(f"Error creating Asana task: {response.status_code} - {response.text}")

def create_subtask(parent_task_gid, name, assignee_gid=None):
    headers = {
        'Authorization': f'Bearer {ASANA_PAT}',
        'Content-Type': 'application/json'
    }
    
    subtask_data = {
        'data': {
            'name': name,
            'parent': parent_task_gid
        }
    }
    
    if assignee_gid:
        subtask_data['data']['assignee'] = assignee_gid
    
    response = requests.post(
        'https://app.asana.com/api/1.0/tasks',
        headers=headers,
        json=subtask_data
    )
    
    if response.status_code != 201:
        print(f"Error creating subtask: {response.status_code} - {response.text}")

def get_user_by_email(email):
    if not email:
        print("No se proporcionó email")
        return None
        
    headers = {
        'Authorization': f'Bearer {ASANA_PAT}'
    }
    
    try:
        workspace_gid = get_workspace_gid()
    except Exception as e:
        print(f"Error obteniendo workspace: {e}")
        return None
    
    # Intentar buscar por email exacto
    response = requests.get(
        f'https://app.asana.com/api/1.0/workspaces/{workspace_gid}/users',
        headers=headers
    )
    
    if response.status_code == 200:
        all_users = response.json()['data']
        print(f"Total usuarios en workspace: {len(all_users)}")
        
        # Buscar coincidencia exacta por email
        for user in all_users:
            user_detail = requests.get(
                f'https://app.asana.com/api/1.0/users/{user["gid"]}',
                headers=headers
            )
            if user_detail.status_code == 200:
                user_data = user_detail.json()['data']
                if user_data.get('email', '').lower() == email.lower():
                    print(f"Usuario encontrado: {user_data.get('name')} - {user_data.get('email')}")
                    return user['gid']
    print(response.text)
    print(f"No se encontró usuario con email: {email}")
    return None

def get_workspace_gid():
    headers = {
        'Authorization': f'Bearer {ASANA_PAT}'
    }
    
    response = requests.get(
        'https://app.asana.com/api/1.0/workspaces',
        headers=headers
    )
    
    if response.status_code == 200:
        workspaces = response.json()['data']
        if workspaces:
            return workspaces[0]['gid']
    
    raise Exception("No workspace found")

def parse_date(date_str):
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%m/%d/%Y',
        '%m-%d-%Y'
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None