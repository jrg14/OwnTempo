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

export type ExpenseReportResult = {
  title: string;
  summary: string;
  overall_status: 'on_track' | 'needs_attention' | 'insufficient_data';
  scores: {
    spending_control: number;
    trend: number;
    savings_outlook: number;
  };
  avoidable_findings: string[];
  trend_findings: string[];
  forecast_findings: string[];
  recommended_actions: string[];
  cautions: string[];
};

export type ExpenseReportMetrics = {
  scope: 'personal' | 'common';
  period: { month: string; is_partial: boolean };
  budget: { monthly: number | null; actual: number; difference: number | null };
  current_month: {
    total: number;
    income: number;
    movement_count: number;
    categories: Array<{
      id: number;
      name: string;
      total: number;
      historical_average: number | null;
      difference: number | null;
      difference_percentage: number | null;
      excess: number | null;
      avoidable: boolean;
    }>;
  };
  evolution: {
    monthly: Array<{ month: string; total: number; income: number; movement_count: number }>;
    previous_month_change: number | null;
    previous_year_same_month_change: number | null;
    monthly_trend_amount: number;
    trend: 'increasing' | 'decreasing' | 'stable';
    extraordinary_months: Array<{ month: string; total: number }>;
  };
  avoidable_spending: {
    current_total: number;
    current_share_percentage: number;
    historical_excess: number;
    reduction_10: number;
    reduction_20: number;
  };
  annual_forecast: {
    projected_expenses: number;
    projected_income: number | null;
    projected_savings: number | null;
    scenarios: {
      baseline: ExpenseForecastScenario;
      reduce_avoidable_10: ExpenseForecastScenario;
      reduce_avoidable_20: ExpenseForecastScenario;
    };
  };
  data_quality: { historical_months: number; warnings: string[] };
};

export type ExpenseForecastScenario = {
  projected_expenses: number;
  future_avoidable_reduction: number;
  projected_savings: number | null;
};

export type MonthlyExpenseReport = {
  id: number;
  month: string;
  scope: 'personal' | 'common';
  goal: string;
  monthly_budget: string | null;
  avoidable_category_ids: number[];
  status: 'pending' | 'processing' | 'completed' | 'failed';
  input_payload: ExpenseReportMetrics | Record<string, never>;
  result_payload: ExpenseReportResult | Record<string, never>;
  model_name: string;
  prompt_version: string;
  error_message: string;
  completed_at: string | null;
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

export async function fetchMonthlyExpenseReports(spaceId: number) {
  return (await request(`${base(spaceId)}/monthly-reports/`)) as MonthlyExpenseReport[];
}

export async function queueMonthlyExpenseReport(spaceId: number, input: {
  month: string;
  goal: string;
  monthly_budget: string | null;
  avoidable_category_ids: number[];
}) {
  return (await mutate(`${base(spaceId)}/monthly-reports/`, 'POST', input)) as MonthlyExpenseReport;
}

export async function deleteMonthlyExpenseReport(spaceId: number, reportId: number) {
  await mutate(`${base(spaceId)}/monthly-reports/${reportId}/`, 'DELETE');
}
