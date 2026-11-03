import { Stack } from "expo-router";

export default function RootLayout() {
  return (
/*     <AuthProvider>
 */      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Home" />
        <Stack.Screen name="Financeiro" />
        <Stack.Screen name="Agenda" />
        <Stack.Screen name="Perfil" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen
          name="Menu"
          options={{
            presentation: "transparentModal",
            animation: "fade",
            contentStyle: { backgroundColor: "transparent" },
          }}
        />
      </Stack>
/*     </AuthProvider>
 */  );
}