import * as Device from 'expo-device';
import { Platform, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ThemedView } from '@/components/themed-view';
import { WebBadge } from '@/components/web-badge';
import { BottomTabInset, MaxContentWidth, Spacing } from '@/constants/theme';
import TelaInicial from './Tela_Inicial';
import LoginScreen from './(tabs)/Login';
import HomeTabScreen from './(tabs)/Home';

export default function HomeScreen() {
  return (
    <ThemedView style={styles.container}>
        <HomeTabScreen />
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    flexDirection: 'row',
  },
});
