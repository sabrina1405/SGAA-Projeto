import { Ionicons } from '@expo/vector-icons';
import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';

import { palette } from '@/constants/palette';
import { SummaryCard } from '@/features/financeiro/components/summary-card';

export default function InicioScreen() {
    return (
        <ScrollView style={styles.container} contentContainerStyle={styles.conteudo}>

            {/* Cabeçalho Superior Roxo */}
            <View style={styles.headerContainer}>
                <View style={styles.headerTopRow}>
                    <View>
                        <Text style={styles.logoText}>Logo</Text>
                        <Text style={styles.welcomeSubtitle}>Seja Bem-Vindo(a) de volta</Text>
                    </View>
                    <Pressable accessibilityRole="button" accessibilityLabel="Menu" onPress={() => { }}>
                        <Ionicons name="menu" size={26} color="#ffffff" />
                    </Pressable>
                </View>
                <Text style={styles.userName}>Olá, Professora</Text>
            </View>

            <View style={styles.bodyContent}>
                {/* Seção: Resumo Financeiro */}
                <View style={styles.sectionContainer}>
                    <Text style={styles.sectionTitle}>Resumo Financeiro</Text>
                    <View style={styles.cardsRow}>
                        <SummaryCard
                            titulo="Saldo"
                            valor={250.00}
                            fundo={palette.saldo.fundo}
                            corValor={palette.saldo.valor}
                        />
                        <SummaryCard
                            titulo="Previsão de entradas:"
                            valor={4300.00}
                            fundo={palette.previsao.fundo}
                            corValor={palette.previsao.valor}
                        />
                    </View>
                </View>

                {/* Seção: Próximas Aulas */}
                <View style={styles.sectionContainer}>
                    <Text style={styles.sectionTitle}>Próximas Aulas</Text>

                    <View style={styles.cardItem}>
                        <View style={styles.indicatorBarBlue} />
                        <View style={styles.iconBoxBlue}>
                            <Ionicons name="school" size={20} color="#0288D1" />
                        </View>
                        <View style={styles.itemInfo}>
                            <Text style={styles.itemTitle}>Aula Espanhol 03</Text>
                            <Text style={styles.itemSubtitle}>Nome do Aluno</Text>
                            <Text style={styles.itemTime}>22/09 ás 15:00</Text>
                        </View>
                        <View style={styles.badgeIcon}>
                            <Ionicons name="bulb-outline" size={16} color="#D32F2F" />
                        </View>
                    </View>

                    <View style={styles.cardItem}>
                        <View style={styles.indicatorBarBlue} />
                        <View style={styles.iconBoxBlue}>
                            <Ionicons name="school" size={20} color="#0288D1" />
                        </View>
                        <View style={styles.itemInfo}>
                            <Text style={styles.itemTitle}>Aula Espanhol 03</Text>
                            <Text style={styles.itemSubtitle}>Nome do Aluno</Text>
                            <Text style={styles.itemTime}>22/09 ás 15:00</Text>
                        </View>
                        <View style={styles.badgeIcon}>
                            <Ionicons name="bulb-outline" size={16} color="#D32F2F" />
                        </View>
                    </View>
                </View>

                {/* Seção: Próximas Atividades */}
                <View style={styles.sectionContainer}>
                    <Text style={styles.sectionTitle}>Próximas Atividades</Text>

                    <View style={styles.cardItem}>
                        <View style={styles.indicatorBarPurple} />
                        <View style={styles.iconBoxPurple}>
                            <Ionicons name="create-outline" size={20} color="#8E24AA" />
                        </View>
                        <View style={styles.itemInfo}>
                            <Text style={styles.itemTitle}>Atividade Espanhol 03</Text>
                            <Text style={styles.itemSubtitle}>Nome do Aluno</Text>
                            <Text style={styles.itemTime}>22/09 ás 15:00</Text>
                        </View>
                    </View>
                </View>

            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: palette.background },
    conteudo: { paddingBottom: 40 },

    /* Cabeçalho */
    headerContainer: {
        backgroundColor: palette.header,
        paddingTop: 48,
        paddingHorizontal: 20,
        paddingBottom: 24,
        borderBottomLeftRadius: 20,
        borderBottomRightRadius: 20,
    },
    headerTopRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    logoText: { color: '#ffffff', fontSize: 14, fontWeight: '600' },
    welcomeSubtitle: { color: 'rgba(255,255,255,0.8)', fontSize: 11 },
    userName: { color: '#ffffff', fontSize: 16, fontWeight: '700', marginTop: 4 },

    bodyContent: { padding: 16, gap: 20 },
    sectionContainer: { gap: 12 },
    sectionTitle: { fontSize: 15, fontWeight: '700', color: palette.title },
    cardsRow: { flexDirection: 'row', gap: 12 },

    /* Cards de Listagem (Aulas e Atividades) */
    cardItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
        borderRadius: 14,
        padding: 12,
        borderWidth: 1,
        borderColor: palette.line,
        overflow: 'hidden',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.04,
        shadowRadius: 3,
        elevation: 2,
    },
    indicatorBarBlue: {
        position: 'absolute',
        left: 0,
        top: 0,
        bottom: 0,
        width: 5,
        backgroundColor: '#6A1B9A', // Detalhe roxo lateral igual ao print
    },
    indicatorBarPurple: {
        position: 'absolute',
        left: 0,
        top: 0,
        bottom: 0,
        width: 5,
        backgroundColor: '#AB47BC',
    },
    iconBoxBlue: {
        width: 42,
        height: 42,
        borderRadius: 10,
        backgroundColor: '#E1F5FE',
        justifyContent: 'center',
        alignItems: 'center',
        marginLeft: 8,
        marginRight: 12,
    },
    iconBoxPurple: {
        width: 42,
        height: 42,
        borderRadius: 10,
        backgroundColor: '#F3E5F5',
        justifyContent: 'center',
        alignItems: 'center',
        marginLeft: 8,
        marginRight: 12,
    },
    itemInfo: { flex: 1, gap: 2 },
    itemTitle: { fontSize: 13, fontWeight: '700', color: palette.title },
    itemSubtitle: { fontSize: 11, color: palette.textMuted },
    itemTime: { fontSize: 11, color: palette.textMuted, fontWeight: '500' },
    badgeIcon: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: '#FFEBEE',
        justifyContent: 'center',
        alignItems: 'center',
    },
});