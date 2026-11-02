import { SafeAreaView, ScrollView, StyleSheet, Text, View, Pressable, } from 'react-native';
import { useRef, useState } from 'react';
import styles from '@/screens/Home/home.styles';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurTargetView, BlurView } from 'expo-blur';
import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { List_item, StatusConfig, type ListItemCategory, type ListItemStatus, } from '@/components/list_item';

const mockData = [
    {
        id: "1",
        titulo: "Introdução ao React Native",
        categoria: "Aula" as const,
        descricao: "Explicação sobre componentes e props.",
        dataHora: "01/11/26 as 14:00",
        nomeAluno: "Carlos Silva",
        status: "proxima" as const,
    },
    {
        id: "2",
        titulo: "Exercício de Fixação - Flexbox",
        categoria: "Atividade" as const,
        descricao: "Criar um layout utilizando alinhamentos.",
        dataHora: "02/11/26 as 10:30",
        nomeAluno: "Ana Souza",
        status: "proxima" as const,
    },
    {
        id: "3",
        titulo: "Mensalidade - Novembro",
        categoria: "Pagamento" as const,
        descricao: "Referente ao plano mensal.",
        dataHora: "Vencimento em 10/11",
        nomeAluno: "Marcos Lima",
        status: "proxima" as const,
    },
    {
        id: "4",
        titulo: "Aula de Navegação (Stack)",
        categoria: "Aula" as const,
        descricao: "Entendendo rotas e parâmetros.",
        dataHora: "02/11/26 as 16:00",
        nomeAluno: "Juliana Pereira",
        status: "proxima" as const,
    },
];

const statusLabels: Record<ListItemStatus, string> = {
  vencida: 'Vencida',
  proxima: 'Próxima',
  realizada: 'Realizada',
};

type HomeItem = (typeof mockData)[number];

export default function HomeScreen() {
  const blurTargetRef = useRef<View | null>(null);
  const [selectedItem, setSelectedItem] = useState<HomeItem | null>(null);

  const renderItems = (categoria: ListItemCategory) =>
    mockData
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
                    Ola, Aluno
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
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>
                  PRÓXIMAS AULAS
                </Text>

                <View style={styles.listContainer}>{renderItems('Aula')}</View>
              </View>

              <View style={styles.separator} />

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>
                  PRÓXIMAS ATIVIDADES
                </Text>

                <View style={styles.listContainer}>{renderItems('Atividade')}</View>
              </View>

              <View style={styles.separator} />

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>
                  PRÓXIMOS PAGAMENTOS
                </Text>
                <View style={styles.listContainer}>{renderItems('Pagamento')}</View>
              </View>
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
