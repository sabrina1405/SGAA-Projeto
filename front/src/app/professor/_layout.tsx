import Ionicons from '@expo/vector-icons/Ionicons';
import { Tabs } from 'expo-router';

import { palette } from '@/constants/palette';


export default function ProfessorLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false, // cada aba usa o header do próprio Stack
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
    </Tabs>
  );
}