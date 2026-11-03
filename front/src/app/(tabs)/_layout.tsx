import { Tabs } from "expo-router";

import { Ionicons, Feather } from "@expo/vector-icons";

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
      }}
    >
                
    <Tabs.Screen
        name="Home"
        options={{
            title: "Home",
            tabBarIcon: ({ color, size }) => (
            <Ionicons 
                name="home-outline" 
                color={color} 
                size={size} 
            />
            ),
        }}
        />
        
        <Tabs.Screen
            name="Financeiro"
            options={{
            title: "Financeiro",
            tabBarIcon: ({ color, size }) => (
                <Ionicons
                name="cash-outline"
                color={color}
                size={size}
                />
            ),
            }}
        />

        <Tabs.Screen
            name="Agenda"
            options={{
            title: "Agenda",
            tabBarIcon: ({ color, size }) => (
                <Feather
                name="calendar"
                color={color}
                size={size}
                />
            ),
            }}
        />

        <Tabs.Screen
            name="Atividades"
            options={{
            title: "Atividades",
            tabBarIcon: ({ color, size }) => (
                <Ionicons
                name="book-outline"
                color={color}
                size={size}
                />
            ),
            }}
        />

        <Tabs.Screen
            name="Perfil"
            options={{
            title: "Perfil",
            tabBarIcon: ({ color, size }) => (
                <Feather
                name="user"
                color={color}
                size={size}
                />
            ),
            }}
        />

    </Tabs>
  );
}