import { SafeAreaView, ScrollView, StyleSheet, Text, View, Pressable, } from 'react-native';
import { useCallback, useEffect, useRef, useState } from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurTargetView, BlurView } from 'expo-blur';
import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { List_item, StatusConfig, type ListItemCategory, type ListItemStatus, } from '@/components/list_item';
import { obterDadosHome } from '@/services/api';

interface HomeItem {
  id: string;
  titulo: string;
  categoria: ListItemCategory;
  descricao: string;
  dataHora: string;
  nomeAluno?: string;
  status: ListItemStatus;
}

interface LoadedHomeData {
  items: HomeItem[];
  studentName: string;
}

function formatApiDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Data inválida recebida pela API: ${value}`);
  }
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatApiDate(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    throw new Error(`Data inválida recebida pela API: ${value}`);
  }
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
    .toLocaleDateString('pt-BR');
}

const statusLabels: Record<ListItemStatus, string> = {
  vencida: 'Vencida',
  proxima: 'Próxima',
  realizada: 'Realizada',
};

export default function HomeScreen() {
  const blurTargetRef = useRef<View | null>(null);
  const [selectedItem, setSelectedItem] = useState<HomeItem | null>(null);
  const [items, setItems] = useState<HomeItem[]>([]);
  const [studentName, setStudentName] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadHome = useCallback(async (): Promise<LoadedHomeData> => {
    const data = await obterDadosHome();
    const nextItems: HomeItem[] = [
        ...data.aulas.map((aula) => ({
          id: String(aula.id),
          titulo: aula.titulo,
          categoria: 'Aula' as const,
          descricao: aula.descricao,
          dataHora: formatApiDateTime(aula.data_hora),
          nomeAluno: aula.nome_aluno ?? undefined,
          status: aula.status,
        })),
        ...data.atividades.map((atividade) => ({
          id: String(atividade.id),
          titulo: atividade.titulo,
          categoria: 'Atividade' as const,
          descricao: atividade.descricao,
          dataHora: formatApiDateTime(atividade.data_hora),
          nomeAluno: atividade.nome_aluno ?? undefined,
          status: atividade.status,
        })),
        ...data.pagamentos.map((pagamento) => ({
          id: String(pagamento.id),
          titulo: pagamento.titulo,
          categoria: 'Pagamento' as const,
          descricao: pagamento.descricao ?? '',
          dataHora: `Vencimento em ${formatApiDate(pagamento.data_vencimento)}`,
          nomeAluno: pagamento.nome_aluno ?? undefined,
          status: pagamento.status,
        })),
    ];
    return { items: nextItems, studentName: data.usuario.nome_completo };
  }, []);

  const handleHomeError = useCallback((error: unknown) => {
    console.error('Erro ao carregar dados da tela inicial:', error);
    setLoadError(
      error instanceof Error
        ? error.message
        : 'Não foi possível carregar os dados. Tente novamente.',
    );
  }, []);

  const applyHomeData = useCallback((data: LoadedHomeData) => {
    setItems(data.items);
    setStudentName(data.studentName);
  }, []);

  const retryHome = () => {
    setLoading(true);
    setLoadError(null);
    void loadHome()
      .then(applyHomeData)
      .catch(handleHomeError)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let active = true;
    loadHome()
      .then((data) => {
        if (active) applyHomeData(data);
      })
      .catch((error: unknown) => {
        if (active) handleHomeError(error);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [applyHomeData, handleHomeError, loadHome]);

  const renderItems = (categoria: ListItemCategory) =>
    items
      .filter((item) => item.categoria === categoria)
      .map((item) => (
        <List_item
          key={item.id}
          titulo={item.titulo}
          categoria={item.categoria}
          dataHora={item.dataHora}
          nomeAluno={item.nomeAluno}
          status={item.status}
          onPress={() => {
            if (item.categoria === 'Aula' || item.categoria === 'Atividade') {
              setSelectedItem(item);
              return;
            }

            console.log(`Clicou no item: ${item.titulo}`);
          }}
        />
      ));

  return (
    <View style={styles.root}>
      <BlurTargetView ref={blurTargetRef} style={styles.root}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.container}>
            <LinearGradient
              colors={['#7B0087', '#980070', '#C40E35']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.header}
            >
              <View style={styles.headerContent}>
                <View style={styles.headerText}>
                  <Text style={styles.logo}>Logo</Text>

                  <Text style={styles.welcome}>
                    Seja Bem-Vindo(a) de volta
                  </Text>

                  <Text style={styles.studentName}>
                    Olá, {studentName || 'Aluno'}
                  </Text>
                </View>

                <Pressable
                  onPress={() => router.push('/Menu')}
                  hitSlop={12}
                  accessibilityRole="button"
                  accessibilityLabel="Abrir menu"
                  style={({ pressed }) => [
                    styles.menuButton,
                    pressed && styles.menuButtonPressed,
                  ]}
                >
                  <Feather name="menu" size={34} color="#FFFFFF" />
                </Pressable>
              </View>
            </LinearGradient>

            <ScrollView
              style={styles.scroll}
              contentContainerStyle={styles.scrollContent}
              showsVerticalScrollIndicator={false}
            >
              {loading ? (
                <Text style={styles.sectionTitle}>Carregando dados...</Text>
              ) : loadError ? (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>{loadError}</Text>
                  <Pressable onPress={retryHome} accessibilityRole="button">
                    <Text>Tentar novamente</Text>
                  </Pressable>
                </View>
              ) : (
                <>
                  <View style={styles.section}>
                    <Text style={styles.sectionTitle}>PRÓXIMAS AULAS</Text>
                    <View style={styles.listContainer}>{renderItems('Aula')}</View>
                  </View>

                  <View style={styles.separator} />

                  <View style={styles.section}>
                    <Text style={styles.sectionTitle}>PRÓXIMAS ATIVIDADES</Text>
                    <View style={styles.listContainer}>{renderItems('Atividade')}</View>
                  </View>

                  <View style={styles.separator} />

                  <View style={styles.section}>
                    <Text style={styles.sectionTitle}>PRÓXIMOS PAGAMENTOS</Text>
                    <View style={styles.listContainer}>{renderItems('Pagamento')}</View>
                  </View>
                </>
              )}
            </ScrollView>
          </View>
        </SafeAreaView>
      </BlurTargetView>

      {selectedItem && (
        <View style={styles.modalOverlay}>
          <BlurView
            blurTarget={blurTargetRef}
            intensity={70}
            tint="dark"
            blurMethod="dimezisBlurView"
            pointerEvents="none"
            style={StyleSheet.absoluteFill}
          />

          <Pressable
            style={StyleSheet.absoluteFill}
            onPress={() => setSelectedItem(null)}
            accessibilityRole="button"
            accessibilityLabel="Fechar detalhes"
          />

          <View style={styles.modalContent} pointerEvents="box-none">
            <View style={styles.detailCard} accessibilityViewIsModal>
              <View style={styles.detailHeader}>
                <View style={styles.detailHeading}>
                  <Text style={styles.detailEyebrow}>{selectedItem.categoria}</Text>
                  <Text style={styles.detailTitle}>{selectedItem.titulo}</Text>
                </View>

                <Pressable
                  onPress={() => setSelectedItem(null)}
                  accessibilityRole="button"
                  accessibilityLabel="Fechar detalhes"
                  hitSlop={12}
                  style={styles.closeButton}
                >
                  <Feather name="x" size={22} color="#555" />
                </Pressable>
              </View>

              <View style={styles.detailDivider} />

              <View style={styles.detailStatus}>
                <View
                  style={[
                    styles.statusDot,
                    { backgroundColor: StatusConfig[selectedItem.status].cor },
                  ]}
                />
                <Text style={styles.detailStatusText}>
                  {statusLabels[selectedItem.status]}
                </Text>
              </View>

              <View style={styles.detailInfoRow}>
                <Feather name="calendar" size={18} color="#84009A" />
                <Text style={styles.detailInfoText}>{selectedItem.dataHora}</Text>
              </View>

              {selectedItem.nomeAluno && (
                <View style={styles.detailInfoRow}>
                  <Ionicons name="person-outline" size={18} color="#84009A" />
                  <Text style={styles.detailInfoText}>{selectedItem.nomeAluno}</Text>
                </View>
              )}

              <Text style={styles.descriptionLabel}>Descrição</Text>
              <Text style={styles.descriptionText}>{selectedItem.descricao}</Text>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

export const styles = StyleSheet.create({
  root: {
    flex: 1,
  },

  safeArea: {
    flex: 1,
    backgroundColor: '#800080',
  },

  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  
  header: {
    height: 106,
    paddingHorizontal: 13,
    paddingTop: 15,
    paddingBottom: 13,
  },

  headerContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },

  textPage: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: 'bold',
    alignSelf: 'center',
    paddingVertical: 14,
  },

  headerText: {
    flex: 1,
  },
  
  logo: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 22,
    fontWeight: '400',
    marginBottom: 8,
  },
  
  welcome: {
    color: '#FFFFFF',
    fontSize: 14,
    lineHeight: 18,
    fontWeight: '400',
  },
  
  studentName: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 21,
    fontWeight: '700',
  },
  
  menuButton: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    borderRadius: 24,
  },
  
  menuButtonPressed: {
    backgroundColor: 'rgba(255,255,255,0.14)',
  },

  scroll: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  
  scrollContent: {
    paddingTop: 31,
    paddingBottom: 42,
  },
  
  section: {
    paddingHorizontal: 10,
  },
  
  sectionTitle: {
    color: '#626262',
    fontSize: 16,
    lineHeight: 21,
    fontWeight: '400',
    marginLeft: 15,
    marginBottom: 3,
  },
  
  separator: {
    height: 1,
    backgroundColor: '#BDBDBD',
    marginHorizontal: 6,
    marginTop: 35,
    marginBottom: 29,
  },
  
  listContainer: {
    padding: 16,
    gap: 12,
  },

  modalOverlay: {
    ...StyleSheet.absoluteFill,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.18)',
  },

  modalContent: {
    flex: 1,
    width: '100%',
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },

  detailCard: {
    width: '100%',
    maxWidth: 440,
    padding: 24,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    elevation: 8,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 18,
    alignSelf: 'center',
  },

  detailHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },

  detailHeading: {
    flex: 1,
  },
  
  detailEyebrow: {
    marginBottom: 6,
    color: '#84009A',
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  
  detailTitle: {
    color: '#292929',
    fontSize: 20,
    lineHeight: 26,
    fontWeight: '700',
  },

  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F3F0F4',
    alignItems: 'center',
    justifyContent: 'center',
  },

  detailDivider: {
    height: 1,
    marginVertical: 18,
    backgroundColor: '#E8E4E9',
  },

  detailStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },

  statusDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
  },

  detailStatusText: {
    color: '#555',
    fontSize: 14,
    fontWeight: '600',
  },

  detailInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
  },

  detailInfoText: {
    flex: 1,
    color: '#444',
    fontSize: 15,
    lineHeight: 21,
  },

  descriptionLabel: {
    marginTop: 10,
    marginBottom: 6,
    color: '#292929',
    fontSize: 15,
    fontWeight: '700',
  },

  descriptionText: {
    color: '#626262',
    fontSize: 15,
    lineHeight: 22,
  },
});
