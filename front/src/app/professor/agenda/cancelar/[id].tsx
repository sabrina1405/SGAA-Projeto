import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { palette } from '@/constants/palette';

export default function CancelarAulaScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();

  const handleConfirmarCancelamento = () => {
    // TODO: Lógica de cancelamento da aula no backend/estado
    router.back();
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
      
      <View style={styles.cardForm}>
        <View style={styles.cardHeaderRow}>
          <Text style={styles.cardHeaderTitle}>Informações de Aula</Text>
          <View style={styles.badgeAgendada}>
            <Text style={styles.badgeTexto}>Agendada</Text>
          </View>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.label}>Título</Text>
          <Text style={styles.valor}>Aula de Espanhol 03</Text>
        </View>

        <View style={styles.linhaDupla}>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>Data</Text>
            <Text style={styles.valor}>00/00/0000</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>Horário</Text>
            <Text style={styles.valor}>00:00 ás 00:30</Text>
          </View>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.label}>Aluno</Text>
          <Text style={styles.valor}>Nome do Aluno</Text>
        </View>

        <View style={styles.divisor} />

        {/* Pergunta de Confirmação de Cancelamento */}
        <View style={styles.confirmacaoContainer}>
          <Text style={styles.perguntaTexto}>Você deseja cancelar a aula?</Text>
          
          <View style={styles.acoesRow}>
            <Pressable 
              style={({ pressed }) => [styles.btnAcao, styles.btnNao, pressed && styles.pressionado]} 
              onPress={() => router.back()}
            >
              <Text style={styles.btnAcaoTexto}>Não</Text>
            </Pressable>

            <Pressable 
              style={({ pressed }) => [styles.btnAcao, styles.btnSim, pressed && styles.pressionado]} 
              onPress={handleConfirmarCancelamento}
            >
              <Text style={styles.btnAcaoTexto}>Sim</Text>
            </Pressable>
          </View>
        </View>
      </View>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 16, paddingBottom: 40, gap: 20 },
  cardForm: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardHeaderTitle: { fontSize: 14, fontWeight: '700', color: palette.title },
  badgeAgendada: { backgroundColor: '#FFE082', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  badgeTexto: { fontSize: 10, fontWeight: '700', color: '#B7791F' },
  infoRow: { gap: 2 },
  linhaDupla: { flexDirection: 'row', gap: 10 },
  label: { fontSize: 11, fontWeight: '600', color: palette.textMuted },
  valor: { fontSize: 13, fontWeight: '600', color: palette.title },
  divisor: { height: 1, backgroundColor: palette.line, marginVertical: 4 },
  confirmacaoContainer: { alignItems: 'center', gap: 12, marginTop: 4 },
  perguntaTexto: { fontSize: 13, fontWeight: '700', color: palette.title },
  acoesRow: { flexDirection: 'row', gap: 12, width: '100%' },
  btnAcao: {
    flex: 1,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnNao: { backgroundColor: '#C62828' },
  btnSim: { backgroundColor: '#2E7D32' },
  btnAcaoTexto: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },
  pressionado: { opacity: 0.8 },
});