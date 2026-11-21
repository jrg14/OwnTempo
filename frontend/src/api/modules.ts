import { mutate, request } from './client';

export type ModuleCatalogEntry = {
  key: 'tasks' | 'shopping' | 'wishlist' | 'calendar' | 'expenses' | 'training';
  name: string;
  description: string;
  icon: 'check' | 'cart' | 'heart' | 'calendar' | 'wallet' | 'activity';
  app_label: string | null;
  available: boolean;
};

export type SpaceModuleConfiguration = Omit<ModuleCatalogEntry, 'app_label'> & {
  enabled: boolean;
  route: string;
};

export async function fetchModuleCatalog() {
  return (await request('/api/v1/modules/catalog/')) as ModuleCatalogEntry[];
}

export async function fetchSpaceModules(spaceId: number) {
  return (await request(
    `/api/v1/spaces/${spaceId}/modules/`,
  )) as SpaceModuleConfiguration[];
}

export async function updateSpaceModule(
  spaceId: number,
  moduleKey: string,
  enabled: boolean,
) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/modules/${moduleKey}/`,
    'PATCH',
    { enabled },
  )) as SpaceModuleConfiguration;
}
