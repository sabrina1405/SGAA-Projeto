import React from 'react';
import { Text, View, SafeAreaView, ScrollView, Pressable, StatusBar, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as Clipboard from 'expo-clipboard';
import { styles } from '@/screens/Home/Financeiro/financeiro.styles';

interface Transacao {
  id: string;
  nome: string;
  vencimento: string;
  valor: number;
  status: keyof typeof StatusConfig;
}

const StatusConfig = {
  vencida: {
    icone: 'time-outline',
    cor: '#ef4444',
    texto: 'Vencida',
    bg: '#ffadad',
  },
  proxima: {
    icone: 'time-outline',
    cor: '#f59e0b',
    texto: 'Pendente',
    bg: '#ffe599',
  },
  realizada: {
    icone: 'checkbox-outline',
    cor: '#10b981',
    texto: 'Pago',
    bg: '#d4edda',
  },
} satisfies Record<
  string,
  { icone: keyof typeof Ionicons.glyphMap; cor: string; texto: string; bg: string }
>;

interface DadosPagamentoResponse {
  totalEmAberto: number;
  chavePix: string;
  itensEmAberto: Transacao[];
}

const dadosPagamentoMock: DadosPagamentoResponse = {
  totalEmAberto: 500,
  chavePix: 'pagamentos@exemplo.com',
  itensEmAberto: [
    {
      id: 'mock-1',
      nome: 'Mensalidade - Espanhol',
      vencimento: '22/09/2026',
      valor: 250,
      status: 'vencida',
    },
    {
      id: 'mock-2',
      nome: 'Mensalidade - Espanhol',
      vencimento: '15/11/2026',
      valor: 250,
      status: 'proxima',
    },
  ],
};

export default function InformacoesPagamentoScreen() {
  const dados = dadosPagamentoMock;

  const copiarChavePix = async (chave: string) => {
    await Clipboard.setStringAsync(chave);
    Alert.alert('Sucesso', 'Chave PIX copiada para a área de transferência!');
  };

  const renderBadge = (status: Transacao['status']) => {
    const config = StatusConfig[status];

    return (
      <View style={[styles.badge, { backgroundColor: config.bg }]}>
        <Ionicons name={config.icone} size={12} color={config.cor} style={styles.badgeIcon} />
        <Text style={[styles.badgeText, { color: config.cor }]}>{config.texto}</Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#7B0087" />

      {/* Header */}
      <LinearGradient
        colors={['#7B0087', '#980070', '#C40E35']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <Pressable
            onPress={() => router.back()}
            hitSlop={12}
            style={({ pressed }) => [pressed && { opacity: 0.7 }]}
          >
            <Feather name="chevron-left" size={32} color="#FFFFFF" 
            style={{paddingVertical: 14,
            }}/>
          </Pressable>

          <View style={styles.headerText}>
            <Text style={styles.textPage}>Informações de Pagamento</Text>
          </View>

          <Pressable
            onPress={() => router.push('/Menu')}
            hitSlop={12}
            style={({ pressed }) => [pressed && { opacity: 0.7 }]}
          >
            <Feather name="menu" size={30} color="#FFFFFF"
            style={{paddingVertical: 14}}/>
          </Pressable>
        </View>
      </LinearGradient>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        
        <LinearGradient
          colors={['#7B0087', '#980070', '#C40E35']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.card}
        >
          <View style={styles.card}>
            <Text style={styles.cardLabel}>Total em aberto:</Text>
            <Text style={styles.cardAmount}>
              {dados.totalEmAberto.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
            </Text>
          </View>
        </LinearGradient>

        <View style={{ marginTop: 24 }}>
          <Text style={styles.sectionTitle}>Valores em aberto</Text>
          {dados.itensEmAberto.map((item) => (
            <View key={item.id} style={[styles.transactionItem, { alignItems: 'flex-start' }]}>
              <View style={styles.transactionInfo}>
                <Text style={styles.transactionName}>{item.nome}</Text>
                <Text style={styles.transactionSubText}>
                  {item.status === 'vencida' ? `Vencido em ${item.vencimento}` : `Vence em ${item.vencimento}`}
                </Text>
              </View>
              <View style={styles.transactionRight}>
                {renderBadge(item.status)}
                <Text style={[styles.transactionAmount, { color: '#000000' }]}>
                  {item.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </Text>
              </View>
            </View>
          ))}
        </View>

        <View style={{ alignItems: 'center', marginTop: 28 }}>
          <Text style={{ fontSize: 16, color: '#333333', fontWeight: '700' }}>
            Chave PIX
          </Text>
          <Text
            selectable
            style={{ marginTop: 8, fontSize: 15, color: '#555555', textAlign: 'center' }}
          >
            {dados.chavePix}
          </Text>

          <Pressable
            onPress={() => copiarChavePix(dados.chavePix)}
            accessibilityRole="button"
            accessibilityLabel="Copiar chave PIX"
            style={[styles.payButton, { padding: 20, overflow: 'hidden' }]}
          >
            <LinearGradient
              start={{ x: 0.65, y: 0 }}
              end={{ x: 0.35, y: 1 }}
              colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
              style={{
                flex: 1,
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 12,
                padding: 15,
                borderRadius: 8,
              }}
            >
              <Text style={styles.payButtonText}>
                Copiar chave PIX
              </Text>
              <Ionicons name="copy-outline" size={18} color="#ffffff" />
            </LinearGradient>
          </Pressable>
        </View>

        <View style={styles.rodape}>
          <Text style={styles.rodapeText}>
            Envie o valor total em aberto para esta chave PIX.
            Caso já tenha realizado o pagamento aguarde a mudança de status de pagamento ou contate o professor.
          </Text>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}