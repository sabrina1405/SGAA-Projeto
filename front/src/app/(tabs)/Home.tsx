import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
  Pressable,
} from 'react-native';

import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { List_item, type ListItemCategory } from '@/components/list_item';

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


export default function HomeScreen() {
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
            console.log(`Clicou no item: ${item.titulo}`);
          }}
        />
      ));

  return (
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
  );
}

const styles = StyleSheet.create({
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
    marginTop: -2,
    justifyContent: 'center',
    alignItems: 'center',
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
});