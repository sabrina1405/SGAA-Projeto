import type Ionicons from '@expo/vector-icons/Ionicons';
import type { ComponentProps } from 'react';

export type IconeNome = ComponentProps<typeof Ionicons>['name'];

export type ItemMenu = {
  rotulo: string;
  icone: IconeNome;
  // Sem rota = tela ainda não existe (só fecha o menu).
  rota?: string;
};

export const ITENS_MENU: ItemMenu[] = [
  { rotulo: 'Inicio', icone: 'home-outline', rota: '/professor' },
  { rotulo: 'Alunos', icone: 'people-outline', rota: '/professor/alunos' },
  { rotulo: 'Agenda', icone: 'calendar-outline', rota: '/professor/agenda' },
  { rotulo: 'Atividades', icone: 'checkmark-done-outline' }, // TODO: criar rota
  { rotulo: 'Financeiro', icone: 'cash-outline', rota: '/professor/financeiro' },
  { rotulo: 'Arquivos', icone: 'folder-open-outline' }, // TODO: criar rota
  { rotulo: 'Relatórios', icone: 'layers-outline' }, // TODO: criar rota
  { rotulo: 'Configurações', icone: 'settings-outline' }, // TODO: criar rota
  { rotulo: 'Recados', icone: 'mail-outline' }, // TODO: criar rota
];