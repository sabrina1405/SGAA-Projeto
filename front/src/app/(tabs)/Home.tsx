import { SafeAreaView, ScrollView, StyleSheet, Text, View, Pressable, } from 'react-native';
import { useCallback, useEffect, useRef, useState } from 'react';
import { styles } from '@/screens/Home/home.styles';
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
