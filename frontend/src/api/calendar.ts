import { mutate, request } from './client';

export type CalendarColor = 'teal' | 'amber' | 'rose' | 'blue' | 'violet' | 'slate';

export type CalendarUser = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
};

export type CalendarEvent = {
  id: number;
  space_id: number;
  title: string;
  description: string;
  start_at: string | null;
  end_at: string | null;
  all_day: boolean;
  date: string | null;
  location: string;
  color: CalendarColor;
  created_by: CalendarUser;
  created_at: string;
  updated_at: string;
};

export type CalendarEventInput = {
  title: string;
  description?: string;
  start_at?: string | null;
  end_at?: string | null;
  all_day: boolean;
  date?: string | null;
  location?: string;
  color?: CalendarColor;
};

export async function fetchCalendarEvents(spaceId: number, from: string, to: string) {
  const params = new URLSearchParams({ from, to });
  return (await request(
    `/api/v1/spaces/${spaceId}/calendar/events/?${params.toString()}`,
  )) as CalendarEvent[];
}

export async function createCalendarEvent(spaceId: number, input: CalendarEventInput) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/calendar/events/`,
    'POST',
    input,
  )) as CalendarEvent;
}

export async function updateCalendarEvent(
  spaceId: number,
  eventId: number,
  input: Partial<CalendarEventInput>,
) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/calendar/events/${eventId}/`,
    'PATCH',
    input,
  )) as CalendarEvent;
}

export async function deleteCalendarEvent(spaceId: number, eventId: number) {
  await mutate(`/api/v1/spaces/${spaceId}/calendar/events/${eventId}/`, 'DELETE');
}
