import { mutate, request } from './client';
import type { UserSummary } from './spaces';

export type ExpenseSplitMode = 'equal' | 'income' | 'custom';
export type ExpensePeriodStatus = 'open' | 'closed';

export type ExpenseParticipant = {
  id: number;
  user: UserSummary;
  income: string;
  personal_starting_savings: string;
  custom_percentage: string;
  position: number;
};

export type ExpensePeriod = {
  id: number;
  space_id: number;
  year: number;
  month: number;
  split_mode: ExpenseSplitMode;
  status: ExpensePeriodStatus;
  participants: ExpenseParticipant[];
  created_at: string;
  updated_at: string;
};

export type ParticipantInput = {
  user_id: number;
  income: string;
  personal_starting_savings?: string;
  custom_percentage: string;
};

export type ExpenseCategory = {
  id: number;
  name: string;
  color: string;
  is_active: boolean;
};

export type ExpenseEntry = {
  id: number;
  description: string;
  amount: string;
  spent_on: string;
  category: Pick<ExpenseCategory, 'id' | 'name' | 'color'>;
  paid_by?: ExpenseParticipant;
  owner?: ExpenseParticipant;
};

export type ExpenseSummary = {
  total_common: string;
  categories: Array<{ category_id: number; name: string; color: string; total: string }>;
  participants: Array<{
    participant_id: number;
    user: UserSummary;
    income: string;
    expected_contribution: string;
    paid: string;
    difference: string;
    available_savings: string;
    personal_starting_savings: string;
    personal_spent: string;
    final_savings: string;
  }>;
  transfers: Array<{ from: UserSummary; to: UserSummary; amount: string }>;
};

export type ExpenseEntryInput = {
  description: string;
  amount: string;
  spent_on: string;
  category_id: number;
  paid_by_id?: number;
};

const base = (spaceId: number) => `/api/v1/spaces/${spaceId}/expenses`;

export async function fetchExpensePeriods(spaceId: number) {
  return (await request(`${base(spaceId)}/periods/`)) as ExpensePeriod[];
}

export async function createExpensePeriod(spaceId: number, input: { year: number; month: number; split_mode: ExpenseSplitMode; participant_inputs: ParticipantInput[] }) {
  return (await mutate(`${base(spaceId)}/periods/`, 'POST', input)) as ExpensePeriod;
}

export async function updateExpensePeriod(spaceId: number, periodId: number, input: { split_mode?: ExpenseSplitMode; status?: ExpensePeriodStatus; participant_inputs?: ParticipantInput[] }) {
  return (await mutate(`${base(spaceId)}/periods/${periodId}/`, 'PATCH', input)) as ExpensePeriod;
}

export async function fetchExpenseSummary(spaceId: number, periodId: number) {
  return (await request(`${base(spaceId)}/periods/${periodId}/summary/`)) as ExpenseSummary;
}

export async function fetchExpenseCategories(spaceId: number) {
  return (await request(`${base(spaceId)}/categories/`)) as ExpenseCategory[];
}

export async function createExpenseCategory(spaceId: number, name: string) {
  return (await mutate(`${base(spaceId)}/categories/`, 'POST', { name })) as ExpenseCategory;
}

export async function updateExpenseCategory(spaceId: number, categoryId: number, input: { name?: string; is_active?: boolean }) {
  return (await mutate(`${base(spaceId)}/categories/${categoryId}/`, 'PATCH', input)) as ExpenseCategory;
}

export async function fetchCommonExpenses(spaceId: number, periodId: number) {
  return (await request(`${base(spaceId)}/periods/${periodId}/expenses/`)) as ExpenseEntry[];
}

export async function createCommonExpense(spaceId: number, periodId: number, input: ExpenseEntryInput) {
  return (await mutate(`${base(spaceId)}/periods/${periodId}/expenses/`, 'POST', input)) as ExpenseEntry;
}

export async function updateCommonExpense(spaceId: number, periodId: number, expenseId: number, input: ExpenseEntryInput) {
  return (await mutate(`${base(spaceId)}/periods/${periodId}/expenses/${expenseId}/`, 'PATCH', input)) as ExpenseEntry;
}

export async function deleteCommonExpense(spaceId: number, periodId: number, expenseId: number) {
  await mutate(`${base(spaceId)}/periods/${periodId}/expenses/${expenseId}/`, 'DELETE');
}

export async function fetchPersonalExpenses(spaceId: number, periodId: number) {
  return (await request(`${base(spaceId)}/periods/${periodId}/personal-expenses/`)) as ExpenseEntry[];
}

export async function createPersonalExpense(spaceId: number, periodId: number, input: ExpenseEntryInput) {
  return (await mutate(`${base(spaceId)}/periods/${periodId}/personal-expenses/`, 'POST', input)) as ExpenseEntry;
}

export async function updatePersonalExpense(spaceId: number, periodId: number, expenseId: number, input: ExpenseEntryInput) {
  return (await mutate(`${base(spaceId)}/periods/${periodId}/personal-expenses/${expenseId}/`, 'PATCH', input)) as ExpenseEntry;
}

export async function deletePersonalExpense(spaceId: number, periodId: number, expenseId: number) {
  await mutate(`${base(spaceId)}/periods/${periodId}/personal-expenses/${expenseId}/`, 'DELETE');
}
