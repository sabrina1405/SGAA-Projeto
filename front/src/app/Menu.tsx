import {
  SafeAreaView,
  ScrollView,
  Text,
  View,
  Pressable,
} from 'react-native';
import { useState, type ReactNode } from 'react';

import { Feather, MaterialCommunityIcons, FontAwesome5, MaterialIcons, Ionicons } from '@expo/vector-icons';
import { styles } from '@/screens/Home/menu.styles';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';

type MenuItemProps = {
  icon: ReactNode;
  label: string;
};

function MenuItem({ icon, label }: MenuItemProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <Pressable
      accessibilityRole="button"
      onHoverIn={() => setHovered(true)}
      onHoverOut={() => setHovered(false)}
      style={({ pressed }) => [
        styles.menuItem,
        (pressed || hovered) && styles.menuItemHighlight,
      ]}
    >
      {icon}
      <Text style={styles.text}>{label}</Text>
    </Pressable>
  );
}

export default function Menu() {
  return (
    <View style={styles.overlay}>
      <Pressable
        style={styles.backdrop}
        onPress={() => router.back()}
        accessibilityRole="button"
        accessibilityLabel="Fechar menu"
      />

      <SafeAreaView style={styles.drawer}>
        <LinearGradient
          colors={['#7B0087', '#980070', '#C40E35']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
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
              <Feather name="x" size={26} color="#fff" />
            </Pressable>
          </View>

          <View style={styles.separator} />

          <ScrollView>
            <MenuItem icon={<Feather name="home" size={30} color="#fff" />} label="Início" />
            <MenuItem icon={<FontAwesome5 name="calendar-check" size={30} color="#fff" />} label="Agenda" />
            <MenuItem icon={<MaterialIcons name="checklist" size={30} color="#fff" />} label="Atividades" />
            <MenuItem icon={<Ionicons name="cash-outline" size={30} color="#fff" />} label="Financeiro" />
            <MenuItem icon={<FontAwesome5 name="folder-open" size={30} color="#fff" />} label="Arquivos" />
            <MenuItem icon={<MaterialCommunityIcons name="nut" size={30} color="#fff" />} label="Configuração" />
            <MenuItem icon={<Feather name="send" size={30} color="#fff" />} label="Recados" />
            <MenuItem icon={<MaterialCommunityIcons name="account-school" size={30} color="#fff" />} label="Professor" />

            <View style={styles.separator} />

            <MenuItem icon={<Feather name="log-out" size={30} color="#fff" />} label="Sair do App" />
          </ScrollView>
        </LinearGradient>
      </SafeAreaView>
    </View>
  );
}