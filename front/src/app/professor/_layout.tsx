import Ionicons from '@expo/vector-icons/Ionicons';
import { Tabs } from 'expo-router';

import { palette } from '@/constants/palette';
import { MenuProvider } from '@/features/menu/menu-context';


export default function ProfessorLayout() {
  return (
    <MenuProvider>
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: palette.primary,
          tabBarInactiveTintColor: '#555555',
          tabBarLabelStyle: { fontSize: 11 },
        }}
      >
        <Tabs.Screen
          name="inicio"
          options={{
            title: 'Início',
            tabBarIcon: ({ color, size }) => <Ionicons name="home-outline" size={size} color={color} />,
          }}
        />
        <Tabs.Screen
          name="financeiro"
          options={{
            title: 'Financeiro',
            tabBarIcon: ({ color, size }) => <Ionicons name="cash-outline" size={size} color={color} />,
          }}
        />
        <Tabs.Screen
          name="agenda"
          options={{
            title: 'Agenda',
            tabBarIcon: ({ color, size }) => <Ionicons name="calendar-outline" size={size} color={color} />,
          }}
        />
        <Tabs.Screen
          name="alunos"
          options={{
            title: 'Alunos',
            tabBarIcon: ({ color, size }) => <Ionicons name="people-outline" size={size} color={color} />,
          }}
        />
        <Tabs.Screen
          name="perfil"
          options={{
            title: 'Perfil',
            tabBarIcon: ({ color, size }) => <Ionicons name="person-outline" size={size} color={color} />,
          }}
        />

        {/* Rota que existe, mas não deve aparecer como aba */}
        <Tabs.Screen name="comprovante" options={{ href: null }} />
        <Tabs.Screen name="atividades" options={{ href: null }} />
        <Tabs.Screen name="recados" options={{ href: null }} />
        <Tabs.Screen name="arquivos" options={{ href: null }} />
      </Tabs>
    </MenuProvider>
  );
}