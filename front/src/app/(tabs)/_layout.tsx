import { Tabs } from "expo-router";

import { Ionicons } from "@expo/vector-icons";

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
            name="Login"
            options={{
            title: "Login",
            tabBarIcon: ({ color, size }) => (
                <Ionicons
                name="people-outline"
                color={color}
                size={size}
                />
            ),
            }}
        />
    </Tabs>
  );
}