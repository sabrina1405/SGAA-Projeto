import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { Stack, useRouter, useSegments } from 'expo-router';

import { palette } from '@/constants/palette';
import { SessaoProvider, useSessao } from '@/features/auth/SessaoContext';

function Guarda() {
  const { estado } = useSessao();
  const segmentos = useSegments();
  const router = useRouter();

  const emAuth = (segmentos[0] as string) === '(auth)';
  const deveIrParaLogin = estado === 'anonimo' && !emAuth;
  const deveIrParaInicio = estado === 'autenticado' && emAuth;

  useEffect(() => {
    if (deveIrParaLogin) router.replace('/loginProfessor');
    else if (deveIrParaInicio) router.replace('/professor/inicio');
  }, [deveIrParaLogin, deveIrParaInicio, router]);

  // Cobre a tela enquanto confere o token ou redireciona, para não piscar conteúdo protegido.
  const bloqueado = estado === 'carregando' || deveIrParaLogin || deveIrParaInicio;

  return (
    <>
      <Stack screenOptions={{ headerShown: false }} />
      {bloqueado && (
        <View style={styles.cobertura}>
          <ActivityIndicator color={palette.header} />
        </View>
      )}
    </>
  );
}

export default function RootLayout() {
  return (
    <SessaoProvider>
      <Guarda />
    </SessaoProvider>
  );
}

const styles = StyleSheet.create({
  cobertura: {
    ...StyleSheet.absoluteFill,
    backgroundColor: palette.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
});