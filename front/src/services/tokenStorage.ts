import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const CHAVE = 'access_token';

// O expo-secure-store não funciona na web, então lá usamos o localStorage.
export async function salvarToken(token: string): Promise<void> {
  if (Platform.OS === 'web') {
    localStorage.setItem(CHAVE, token);
    return;
  }
  await SecureStore.setItemAsync(CHAVE, token);
}

export async function obterToken(): Promise<string | null> {
  if (Platform.OS === 'web') return localStorage.getItem(CHAVE);
  return SecureStore.getItemAsync(CHAVE);
}

export async function removerToken(): Promise<void> {
  if (Platform.OS === 'web') {
    localStorage.removeItem(CHAVE);
    return;
  }
  await SecureStore.deleteItemAsync(CHAVE);
}