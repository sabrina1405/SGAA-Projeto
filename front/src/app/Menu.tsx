import { Feather, FontAwesome5, Ionicons, MaterialIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type ViewStyle,
} from 'react-native';
import type { ReactNode } from 'react';

import { useSessao } from '@/features/auth/SessaoContext';

type MenuItemProps = {
  icon: ReactNode;
  label: string;
  onPress: () => void;
};

function MenuItem({ icon, label, onPress }: MenuItemProps) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.menuItem, pressed && styles.menuItemHighlight]}
    >
      {icon}
      <Text style={styles.text}>{label}</Text>
    </Pressable>
  );
}

export default function Menu() {
  const router = useRouter();
  const { encerrarSessao } = useSessao();

  async function sair() {
    await encerrarSessao();
    router.replace('/loginProfessor');
  }

  return (
    <View style={styles.overlay}>
      <Pressable
        style={styles.backdrop as ViewStyle}
        onPress={() => router.back()}
        accessibilityRole="button"
        accessibilityLabel="Fechar menu"
      />
      <SafeAreaView style={styles.drawer}>
        <LinearGradient
          colors={['#7B0087', '#980070', '#C40E35']}
          style={styles.container}
        >
          <View style={styles.menuHeader}>
            <View style={styles.logo}>
              <Text style={styles.logoText}>SGAA</Text>
            </View>
            <Pressable
              onPress={() => router.back()}
              accessibilityRole="button"
              accessibilityLabel="Fechar menu"
              hitSlop={12}
            >
              <Feather name="x" size={26} color="#FFFFFF" />
            </Pressable>
          </View>

          <View style={styles.separator} />
          <ScrollView>
            <MenuItem
              icon={<Feather name="home" size={30} color="#FFFFFF" />}
              label="Início"
              onPress={() => router.replace('/aluno/home')}
            />
            <MenuItem
              icon={<FontAwesome5 name="calendar-check" size={30} color="#FFFFFF" />}
              label="Agenda"
              onPress={() => router.replace('/aluno/agenda')}
            />
            <MenuItem
              icon={<MaterialIcons name="checklist" size={30} color="#FFFFFF" />}
              label="Atividades"
              onPress={() => router.replace('/aluno/atividades')}
            />
            <MenuItem
              icon={<Ionicons name="cash-outline" size={30} color="#FFFFFF" />}
              label="Financeiro"
              onPress={() => router.replace('/aluno/financeiro')}
            />
            <MenuItem
              icon={<Feather name="user" size={30} color="#FFFFFF" />}
              label="Perfil"
              onPress={() => router.replace('/aluno/perfil')}
            />
            <MenuItem
              icon={<FontAwesome5 name="folder-open" size={30} color="#FFFFFF" />}
              label="Arquivos"
              onPress={() => router.replace('/aluno/arquivos')}
            />
            <MenuItem
              icon={<Feather name="send" size={30} color="#FFFFFF" />}
              label="Recados"
              onPress={() => router.replace('/aluno/recados')}
            />
            <View style={styles.separator} />
            <MenuItem
              icon={<Feather name="log-out" size={30} color="#FFFFFF" />}
              label="Sair do App"
              onPress={() => void sair()}
            />
          </ScrollView>
        </LinearGradient>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: { ...StyleSheet.absoluteFill, flexDirection: 'row' },
  backdrop: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(0,0,0,0.35)' },
  drawer: { marginLeft: 'auto', width: '82%', maxWidth: 320 },
  container: { flex: 1, paddingHorizontal: 20 },
  menuHeader: {
    height: 100,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logo: {
    width: 62,
    height: 62,
    borderRadius: 31,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: { color: '#84009A', fontSize: 16, fontWeight: '800' },
  separator: { height: 1, backgroundColor: 'rgba(255,255,255,0.45)', marginVertical: 10 },
  menuItem: {
    minHeight: 58,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    borderRadius: 10,
    paddingHorizontal: 12,
  },
  menuItemHighlight: { backgroundColor: 'rgba(255,255,255,0.12)' },
  text: { color: '#FFFFFF', fontSize: 16, fontWeight: '600' },
});
