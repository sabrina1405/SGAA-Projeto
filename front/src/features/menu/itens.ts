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
  { rotulo: 'Atividades', icone: 'checkmark-done-outline', rota:'/professor/atividades' }, 
  { rotulo: 'Financeiro', icone: 'cash-outline', rota: '/professor/financeiro' },
  { rotulo: 'Arquivos', icone: 'folder-open-outline', rota:"/professor/arquivos" },
  { rotulo: 'Relatórios', icone: 'layers-outline', rota:"/professor/financeiro/relatorioFinanceiro"}, 
  { rotulo: 'Recados', icone: 'mail-outline', rota: '/professor/recados' }, 
  { rotulo: 'Configurações', icone: 'settings-outline', rota: "/professor/perfil" }, 
  
];