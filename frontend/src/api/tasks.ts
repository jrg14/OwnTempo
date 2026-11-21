import { mutate, request } from './client';

export type TaskStatus = 'pending' | 'completed';
export type TaskPriority = 'low' | 'normal' | 'high';

export type TaskUser = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
};

export type Task = {
  id: number;
  space_id: number;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  created_by: TaskUser;
  assignees: TaskUser[];
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskInput = {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string | null;
  assignee_ids?: number[];
};

export async function fetchTasks(spaceId: number) {
  return (await request(`/api/v1/spaces/${spaceId}/tasks/`)) as Task[];
}

export async function createTask(spaceId: number, input: TaskInput) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/tasks/`,
    'POST',
    input,
  )) as Task;
}

export async function updateTask(
  spaceId: number,
  taskId: number,
  input: Partial<TaskInput>,
) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/tasks/${taskId}/`,
    'PATCH',
    input,
  )) as Task;
}

export async function deleteTask(spaceId: number, taskId: number) {
  await mutate(`/api/v1/spaces/${spaceId}/tasks/${taskId}/`, 'DELETE');
}
