import { mutate, request } from './client';

export type TrainingProfile = {
  id: number;
  height_cm: number;
  date_of_birth: string;
  age: number;
};

export type StrengthSet = {
  id: number;
  set_number: number;
  weight_kg: string;
  repetitions: number;
  rest_seconds: number | null;
};

export type StrengthExercise = {
  id: number;
  name: string;
  order: number;
  notes: string;
  sets: StrengthSet[];
};

export type StrengthWorkout = {
  id: number;
  workout_date: string;
  started_at: string | null;
  duration_minutes: number | null;
  notes: string;
  exercises: StrengthExercise[];
  total_volume_kg: string;
};

export type StrengthWorkoutInput = {
  workout_date: string;
  started_at?: string | null;
  duration_minutes?: number | null;
  notes?: string;
  exercises: Array<{
    name: string;
    order: number;
    notes?: string;
    sets: Array<{
      set_number: number;
      weight_kg: string;
      repetitions: number;
      rest_seconds?: number | null;
    }>;
  }>;
};

export type DailySteps = {
  id: number;
  date: string;
  steps: number;
  goal: number | null;
  notes: string;
};

export type HealthMeasurement = {
  id: number;
  date: string;
  weight_kg: string;
  bmi: string | null;
  body_fat_percentage: string | null;
  subcutaneous_fat_percentage: string | null;
  visceral_fat_level: string | null;
  body_water_percentage: string | null;
  muscle_mass_kg: string | null;
  bone_mass_kg: string | null;
  basal_metabolic_rate_kcal: number | null;
  metabolic_age: number | null;
  notes: string;
};

export type TrainingSummary = {
  today: {
    steps: number | null;
    steps_goal: number | null;
    workout_count: number;
    weight_kg: string | null;
  };
  week: {
    total_steps: number;
    average_steps: number;
    workout_count: number;
  };
  health: {
    latest: HealthMeasurement | null;
    weight_change_from_first_kg: string | null;
    weight_change_from_previous_kg: string | null;
  };
  steps_history: Array<{ date: string; steps: number; goal: number | null }>;
  health_history: HealthMeasurement[];
};

const root = (spaceId: number) => `/api/v1/spaces/${spaceId}/training`;

export async function fetchTrainingProfile(spaceId: number) {
  return (await request(`${root(spaceId)}/profile/`)) as TrainingProfile;
}

export async function saveTrainingProfile(spaceId: number, input: Pick<TrainingProfile, 'height_cm' | 'date_of_birth'>) {
  return (await mutate(`${root(spaceId)}/profile/`, 'PUT', input)) as TrainingProfile;
}

export async function fetchTrainingSummary(spaceId: number) {
  return (await request(`${root(spaceId)}/summary/`)) as TrainingSummary;
}

export async function fetchWorkouts(spaceId: number) {
  return (await request(`${root(spaceId)}/workouts/`)) as StrengthWorkout[];
}

export async function createWorkout(spaceId: number, input: StrengthWorkoutInput) {
  return (await mutate(`${root(spaceId)}/workouts/`, 'POST', input)) as StrengthWorkout;
}

export async function deleteWorkout(spaceId: number, workoutId: number) {
  await mutate(`${root(spaceId)}/workouts/${workoutId}/`, 'DELETE');
}

export async function fetchDailySteps(spaceId: number) {
  return (await request(`${root(spaceId)}/steps/`)) as DailySteps[];
}

export async function createDailySteps(spaceId: number, input: Omit<DailySteps, 'id' | 'notes'> & { notes?: string }) {
  return (await mutate(`${root(spaceId)}/steps/`, 'POST', input)) as DailySteps;
}

export async function updateDailySteps(spaceId: number, entryId: number, input: Partial<DailySteps>) {
  return (await mutate(`${root(spaceId)}/steps/${entryId}/`, 'PATCH', input)) as DailySteps;
}

export async function fetchHealthMeasurements(spaceId: number) {
  return (await request(`${root(spaceId)}/health/`)) as HealthMeasurement[];
}

export async function createHealthMeasurement(spaceId: number, input: Omit<HealthMeasurement, 'id' | 'notes'> & { notes?: string }) {
  return (await mutate(`${root(spaceId)}/health/`, 'POST', input)) as HealthMeasurement;
}

export async function updateHealthMeasurement(spaceId: number, entryId: number, input: Partial<HealthMeasurement>) {
  return (await mutate(`${root(spaceId)}/health/${entryId}/`, 'PATCH', input)) as HealthMeasurement;
}
