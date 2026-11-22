import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';
import {
  RecadoGeral,
  RecadoListaItem,
  limparRecadoGeral,
  listarRecados,
  mensagemDeErro,
  obterRecadoGeral,
} from '@/services/recado-service';

// AAAA-MM-DD -> DD/MM/AAAA
function formatarData(iso: string) {
  return iso.split('-').reverse().join('/');
}

export default function RecadosScreen() {
  const router = useRouter();
  const [geral, setGeral] = useState<RecadoGeral | null>(null);
  const [recados, setRecados] = useState<RecadoListaItem[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [limpando, setLimpando] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const [recadoGeral, lista] = await Promise.all([obterRecadoGeral(), listarRecados()]);
      setGeral(recadoGeral);
      setRecados(lista.itens);
    } catch (erro) {
      Alert.alert('Erro', mensagemDeErro(erro, 'Falha ao carregar os recados.'));
    } finally {
      setCarregando(false);
    }
  }, []);

  // Recarrega sempre que a tela volta ao foco (ex.: depois de salvar um recado).
  useFocusEffect(
    useCallback(() => {
      carregar();
    }, [carregar]),
  );

  function confirmarLimpeza() {
    Alert.alert('Limpar painel', 'Deseja limpar o recado geral?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Limpar',
        style: 'destructive',
        onPress: async () => {
          setLimpando(true);
          try {
            await limparRecadoGeral();
            setGeral(null);
          } catch (erro) {
            Alert.alert('Erro', mensagemDeErro(erro, 'Falha ao limpar o painel.'));
          } finally {
            setLimpando(false);
          }
        },
      },
    ]);
  }

  return (
    <View style={styles.container}>
      <View style={styles.headerTop}>
        <Text style={styles.headerTitle}>Central de Recados</Text>
        <Pressable
          style={({ pressed }) => [styles.btnNovo, pressed && styles.pressionado]}
          onPress={() => router.push('/professor/recados/novo')}
        >
          <Ionicons name="megaphone-outline" size={16} color="#FFFFFF" />
          <Text style={styles.btnNovoTexto}>Novo Recado</Text>
        </Pressable>
      </View>

      {carregando ? (
        <ActivityIndicator style={{ marginTop: 40 }} color={palette.title} />
      ) : (
        <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
          {/* Recado Ativo Principal */}
          <Text style={styles.sectionTitle}>Recado Geral Ativo</Text>
          <View style={styles.cardDestaque}>
            <View style={styles.cardHeaderRow}>
              <Ionicons name="pin" size={18} color="#D81B60" />
              <Text style={styles.cardDestaqueTitle}>Aviso da Semana</Text>
            </View>
            <Text style={styles.cardTexto}>{geral ? geral.conteudo : 'Nenhum recado geral ativo.'}</Text>
            <View style={styles.acoesRow}>
              <Pressable
                style={[styles.btnSecundario, (!geral || limpando) && styles.pressionado]}
                onPress={confirmarLimpeza}
                disabled={!geral || limpando}
              >
                <Text style={styles.btnSecundarioTexto}>Limpar Painel</Text>
              </Pressable>
              <Pressable
                style={styles.btnPrimario}
                onPress={() => router.push('/professor/recados/novo?geral=1')}
              >
                <Text style={styles.btnPrimarioTexto}>Editar Recado</Text>
              </Pressable>
            </View>
          </View>

          {/* Histórico */}
          <Text style={styles.sectionTitle}>Histórico de Recados</Text>
          {recados.length === 0 ? (
            <View style={styles.cardHistorico}>
              <Text style={styles.cardTextoHistorico}>Nenhum recado enviado.</Text>
            </View>
          ) : (
            recados.map((recado) => (
              <View key={recado.id} style={styles.cardHistorico}>
                <View style={styles.cardHeaderRow}>
                  <Ionicons name="calendar-outline" size={14} color={palette.textMuted} />
                  <Text style={styles.historicoData}>{formatarData(recado.data_inicio)}</Text>
                </View>
                <Text style={styles.cardTextoHistorico}>{recado.conteudo}</Text>
              </View>
            ))
          )}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: palette.line,
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: palette.title },
  btnNovo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: palette.button || '#2E7D32',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  btnNovoTexto: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },
  conteudo: { padding: 16, gap: 14, paddingBottom: 40 },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: palette.title, marginTop: 4 },
  cardDestaque: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  cardHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  cardDestaqueTitle: { fontSize: 14, fontWeight: '700', color: palette.title },
  cardTexto: { fontSize: 13, color: '#374151', lineHeight: 18 },
  linkBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#EFF6FF',
    padding: 10,
    borderRadius: 10,
  },
  linkTexto: { fontSize: 12, color: '#2563EB', fontWeight: '600' },
  acoesRow: { flexDirection: 'row', gap: 10, marginTop: 4 },
  btnSecundario: {
    flex: 1,
    height: 38,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnSecundarioTexto: { color: '#4B5563', fontSize: 12, fontWeight: '600' },
  btnPrimario: {
    flex: 1,
    height: 38,
    borderRadius: 10,
    backgroundColor: palette.title,
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnPrimarioTexto: { color: '#FFFFFF', fontSize: 12, fontWeight: '600' },
  cardHistorico: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 6,
  },
  historicoData: { fontSize: 11, fontWeight: '600', color: palette.textMuted },
  cardTextoHistorico: { fontSize: 12, color: palette.title },
  pressionado: { opacity: 0.8 },
});