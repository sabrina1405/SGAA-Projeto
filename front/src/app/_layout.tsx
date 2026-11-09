import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Stack } from 'expo-router';
import {
  AuthSessionProvider,
  useAuthSession,
} from '@/contexts/auth-context';

export default function RootLayout() {
  return (
    <AuthSessionProvider>
      <RootNavigator />
    </AuthSessionProvider>
  );
}

function RootNavigator() {
  const { status, user, retry } = useAuthSession();
  const [retrying, setRetrying] = useState(false);

  if (status === 'checking') {
    return (
      <View style={styles.statusContainer}>
        <ActivityIndicator size="large" color="#84009A" />
      </View>
    );
  }

  if (status === 'error') {
    const handleRetry = async () => {
      setRetrying(true);
      try {
        await retry();
      } finally {
        setRetrying(false);
      }
    };

    return (
      <View style={styles.statusContainer}>
        <Text style={styles.errorText}>
          Não foi possível validar sua sessão. Verifique a conexão e tente novamente.
        </Text>
        <Pressable
          accessibilityRole="button"
          disabled={retrying}
          onPress={() => void handleRetry()}
          style={styles.retryButton}
        >
          <Text style={styles.retryText}>
            {retrying ? 'Verificando...' : 'Tentar novamente'}
          </Text>
        </Pressable>
      </View>
    );
  }

  const authenticated = status === 'authenticated' && user !== null;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={authenticated}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen
          name="Menu"
          options={{
            presentation: 'transparentModal',
            animation: 'fade',
            contentStyle: { backgroundColor: 'transparent' },
          }}
        />
        <Stack.Screen name="Pagamento" />
        <Stack.Screen name="Recados" />
        <Stack.Screen name="Arquivos" />
      </Stack.Protected>
      <Stack.Protected guard={!authenticated}>
        <Stack.Screen name="Login" />
        <Stack.Screen name="FirstAccess" />
        <Stack.Screen name="PasswordRec" />
      </Stack.Protected>
    </Stack>
  );
}

const styles = StyleSheet.create({
  statusContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  errorText: {
    color: '#222',
    marginBottom: 16,
    textAlign: 'center',
  },
  retryButton: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#84009A',
  },
  retryText: {
    color: '#fff',
    fontWeight: '600',
  },
});