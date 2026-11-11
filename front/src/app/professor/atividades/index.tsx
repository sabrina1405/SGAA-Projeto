import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';

type FiltroAtividade = 'todas' | 'vencidas' | 'proximas' | 'entregues';

export default function AtividadesScreen() {
  const router = useRouter();
  const [filtro, setFiltro] = useState<FiltroAtividade>('todas');

  return (
    <View style={styles.container}>
      {/* Header com Filtros em Abas */}
      <View style={styles.headerArea}>
        <View style={styles.headerTop}>
          <Text style={styles.headerTitle}>Mural de Atividades</Text>
          <Pressable
            style={({ pressed }) => [styles.btnCriar, pressed && styles.pressionado]}
            onPress={() => router.push('/professor/atividades/novo')}
          >
            <Ionicons name="add" size={18} color="#FFFFFF" />
            <Text style={styles.btnCriarTexto}>Nova Atividade</Text>
          </Pressable>
        </View>

        {/* Segmented Control / Tabs */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabsContainer}>
          {[
            { id: 'todas', label: 'Todas' },
            { id: 'vencidas', label: 'Vencidas (1)' },
            { id: 'proximas', label: 'Próximas (1)' },
            { id: 'entregues', label: 'Entregues (2)' },
          ].map((tab) => (
            <Pressable
              key={tab.id}
              style={[styles.tabChip, filtro === tab.id && styles.tabChipAtivo]}
              onPress={() => setFiltro(tab.id as FiltroAtividade)}
            >
              <Text style={[styles.tabChipTexto, filtro === tab.id && styles.tabChipTextoAtivo]}>
                {tab.label}
              </Text>
            </Pressable>
          ))}
        </ScrollView>
      </View>

      <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
        {/* Atividade Vencida */}
        {(filtro === 'todas' || filtro === 'vencidas') && (
          <View style={[styles.card, { borderLeftColor: '#EF4444' }]}>
            <View style={styles.cardTopRow}>
              <View style={[styles.iconBox, { backgroundColor: '#FEE2E2' }]}>
                <Ionicons name="alert-circle" size={20} color="#EF4444" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>Aula Espanhol 03</Text>
                <Text style={styles.cardSub}>Aluno: Maria Silva</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: '#FEE2E2' }]}>
                <Text style={[styles.badgeText, { color: '#DC2626' }]}>Vencida</Text>
              </View>
            </View>
            <View style={styles.cardFooter}>
              <Ionicons name="calendar-outline" size={14} color={palette.textMuted} />
              <Text style={styles.cardFooterText}>Prazo encerrado em 05/10/2026</Text>
            </View>
          </View>
        )}

        {/* Próxima Atividade */}
        {(filtro === 'todas' || filtro === 'proximas') && (
          <View style={[styles.card, { borderLeftColor: '#F59E0B' }]}>
            <View style={styles.cardTopRow}>
              <View style={[styles.iconBox, { backgroundColor: '#FEF3C7' }]}>
                <Ionicons name="time" size={20} color="#F59E0B" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>Atividade Espanhol 03</Text>
                <Text style={styles.cardSub}>Aluno: João Pedro</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: '#FEF3C7' }]}>
                <Text style={[styles.badgeText, { color: '#D97706' }]}>Em Aberto</Text>
              </View>
            </View>
            <View style={styles.cardFooter}>
              <Ionicons name="calendar-outline" size={14} color={palette.textMuted} />
              <Text style={styles.cardFooterText}>Vence em 22/10/2026 às 15:00</Text>
            </View>
          </View>
        )}

        {/* Atividade Entregue */}
        {(filtro === 'todas' || filtro === 'entregues') && (
          <View style={[styles.card, { borderLeftColor: '#10B981' }]}>
            <View style={styles.cardTopRow}>
              <View style={[styles.iconBox, { backgroundColor: '#D1FAE5' }]}>
                <Ionicons name="checkmark-done-circle" size={20} color="#10B981" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>Exercício de Gramática 01</Text>
                <Text style={styles.cardSub}>Aluno: Sofia Amorim</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: '#D1FAE5' }]}>
                <Text style={[styles.badgeText, { color: '#059669' }]}>Entregue</Text>
              </View>
            </View>
            <View style={styles.cardFooter}>
              <Ionicons name="checkmark-circle-outline" size={14} color="#10B981" />
              <Text style={styles.cardFooterText}>Enviado em 08/10/2026</Text>
            </View>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  headerArea: {
    backgroundColor: '#FFFFFF',
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: palette.line,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: palette.title },
  btnCriar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: palette.button || '#2E7D32',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  btnCriarTexto: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },
  tabsContainer: { paddingHorizontal: 16, gap: 8 },
  tabChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  tabChipAtivo: { backgroundColor: palette.title },
  tabChipTexto: { fontSize: 12, fontWeight: '600', color: '#6B7280' },
  tabChipTextoAtivo: { color: '#FFFFFF' },
  conteudo: { padding: 16, gap: 12, paddingBottom: 40 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
    gap: 12,
  },
  cardTopRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconBox: { width: 38, height: 38, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  cardTitle: { fontSize: 14, fontWeight: '700', color: palette.title },
  cardSub: { fontSize: 12, color: palette.textMuted, marginTop: 2 },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  badgeText: { fontSize: 11, fontWeight: '700' },
  cardFooter: { flexDirection: 'row', alignItems: 'center', gap: 6, borderTopWidth: 1, borderTopColor: '#F3F4F6', paddingTop: 8 },
  cardFooterText: { fontSize: 11, color: palette.textMuted, fontWeight: '500' },
  pressionado: { opacity: 0.8 },
});