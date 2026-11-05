import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router, usePathname, type Href } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Animated, Modal, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ITENS_MENU, type ItemMenu } from '../itens';
import { useMenu } from '../menu-context';

// Degradê do menu (roxo -> azul), igual ao Figma.
const GRADIENTE = ['#6B1B7F', '#3B3BB0', '#1677F0'] as const;
const DURACAO = 220;

export function MenuLateral() {
  const { aberto, fechar } = useMenu();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const largura = Math.min(width * 0.8, 320);

  const anim = useRef(new Animated.Value(0)).current; // 0 fechado, 1 aberto
  const [montado, setMontado] = useState(false);

  useEffect(() => {
    if (aberto) {
      setMontado(true);
      Animated.timing(anim, { toValue: 1, duration: DURACAO, useNativeDriver: true }).start();
    } else {
      Animated.timing(anim, { toValue: 0, duration: DURACAO, useNativeDriver: true }).start(
        ({ finished }) => finished && setMontado(false),
      );
    }
  }, [aberto, anim]);

  function estaAtivo(rota?: string) {
    if (!rota) return false;
    if (rota === '/professor') return pathname === '/professor' || pathname === '/professor/index';
    return pathname === rota || pathname.startsWith(`${rota}/`);
  }

  function ir(item: ItemMenu) {
    fechar();
    if (item.rota) router.navigate(item.rota as Href);
  }

  function sair() {
    fechar();
    // TODO: limpar sessão/token e redirecionar para o login
  }

  const translateX = anim.interpolate({ inputRange: [0, 1], outputRange: [-largura, 0] });
  const opacidadeFundo = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 0.45] });

  return (
    <Modal visible={montado} transparent animationType="none" onRequestClose={fechar} statusBarTranslucent>
      <View style={styles.raiz}>
        <Animated.View style={[styles.fundo, { opacity: opacidadeFundo }]}>
          <Pressable
            style={StyleSheet.absoluteFill}
            onPress={fechar}
            accessibilityRole="button"
            accessibilityLabel="Fechar menu"
          />
        </Animated.View>

        <Animated.View style={[styles.painel, { width: largura, transform: [{ translateX }] }]}>
          <LinearGradient colors={GRADIENTE} style={[styles.gradiente, { paddingTop: insets.top, paddingBottom: insets.bottom + 16 }]}>
            <View style={styles.logo}>
              <Text style={styles.logoTexto}>Logo</Text>
            </View>

            <View style={styles.divisor} />

            <View style={styles.lista}>
              {ITENS_MENU.map((item) => {
                const ativo = estaAtivo(item.rota);
                return (
                  <Pressable
                    key={item.rotulo}
                    accessibilityRole="button"
                    accessibilityState={{ selected: ativo }}
                    onPress={() => ir(item)}
                    style={({ pressed }) => [styles.item, ativo && styles.itemAtivo, pressed && styles.pressionado]}
                  >
                    <Ionicons name={item.icone} size={22} color="#fff" />
                    <Text style={styles.itemTexto}>{item.rotulo}</Text>
                  </Pressable>
                );
              })}
            </View>

            <View style={styles.rodape}>
              <View style={styles.divisor} />
              <Pressable
                accessibilityRole="button"
                onPress={sair}
                style={({ pressed }) => [styles.sair, pressed && styles.pressionado]}
              >
                <Ionicons name="log-out-outline" size={22} color="#fff" />
                <Text style={styles.itemTexto}>Sair do App</Text>
              </Pressable>
            </View>
          </LinearGradient>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  raiz: { flex: 1 },
 fundo: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: '#000' },
  painel: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 0,
    elevation: 16,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 12,
    shadowOffset: { width: 4, height: 0 },
  },
  gradiente: { flex: 1, paddingHorizontal: 16 },
  logo: { height: 96, alignItems: 'center', justifyContent: 'center' },
  logoTexto: { color: '#fff', fontSize: 14 },
  divisor: { height: StyleSheet.hairlineWidth, backgroundColor: 'rgba(255,255,255,0.6)', marginVertical: 8 },
  lista: { flex: 1, gap: 4, marginTop: 8 },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 46,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  itemAtivo: { backgroundColor: 'rgba(255,255,255,0.3)' },
 itemTexto: { flex: 1, textAlign: 'left', marginLeft: 16, color: '#fff', fontSize: 16, fontWeight: '500' },
  rodape: { gap: 12 },
  sair: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 46,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.3)',
  },
  pressionado: { opacity: 0.8 },
});