import { Stack } from "expo-router";

export default function RootLayout() {
  return (
/*     <AuthProvider>
 */      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Login" />
        <Stack.Screen name="Home" />
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