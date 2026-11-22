import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Platform, Text, TextInput, View, SafeAreaView, ScrollView, Pressable, StatusBar, } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import DateTimePicker, { type DateTimePickerEvent } from '@react-native-community/datetimepicker';
import { styles } from '@/screens/Financeiro/financeiro.styles';
import { obterMinhasCobrancas, type MinhaCobrancaApi } from '@/services/api';

export const StatusConfig = {
    vencida: {
        icone: "time-outline",
        cor: "#ef4444",
        texto: "Vencida",
        bg: "#ffadad",
    },
    proxima: {
        icone: "time-outline",
        cor: "#f59e0b",
        texto: "Pendente",
        bg: "#ffe599",
    },
    realizada: {
        icone: "checkbox-outline",
        cor: "#10b981",
        texto: "Pago",
        bg: "#d4edda",
    },
    cancelada: {
        icone: "close-circle-outline",
        cor: "#6b7280",
        texto: "Cancelada",
        bg: "#e5e7eb",
    },
} satisfies Record<string, { icone: keyof typeof Ionicons.glyphMap; cor: string; texto: string; bg: string }>;

interface Transacao {
  id: string;
  nome: string;
  vencimento: string;
  dataOriginal: Date | string;
  dataPagamento: string | null;
  valor: number;
  status: keyof typeof StatusConfig;
}

type StatusFilter = keyof typeof StatusConfig | 'todos';
type FilterPanel = 'status' | 'valor' | 'data' | null;
type DateFilterTarget = 'inicio' | 'fim';

const statusOptions: StatusFilter[] = ['todos', 'vencida', 'proxima', 'realizada', 'cancelada'];

function getTransactionDate(value: Transacao['dataOriginal']): Date | null {
  if (typeof value === 'string') {
    const dateOnly = /^(\d{4})-(\d{2})-(\d{2})(?:$|T)/.exec(value);
    if (dateOnly) {
      return new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]));
    }
  }

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function parseCurrencyInput(value: string): number | null {
  const normalized = value.trim().replace(/[^\d,.-]/g, '');
  if (!normalized) {
    return null;
  }

  const amount = normalized.includes(',')
    ? Number(normalized.replace(/\./g, '').replace(',', '.'))
    : Number(normalized);

  return Number.isFinite(amount) ? amount : null;
}

function formatDateFilter(value: Date | null): string {
  return value ? value.toLocaleDateString('pt-BR') : '';
}

function mapearCobranca(cobranca: MinhaCobrancaApi): Transacao {
  const date = getTransactionDate(cobranca.vencimento);
  if (!date) {
    throw new Error(`Data inválida recebida pela API: ${cobranca.vencimento}`);
  }

  return {
    id: String(cobranca.id),
    nome: cobranca.descricao,
    vencimento: date.toLocaleDateString('pt-BR'),
    dataOriginal: cobranca.vencimento,
    dataPagamento: cobranca.paga_em,
    valor: cobranca.valor_centavos / 100,
    status: cobranca.situacao === 'paga'
      ? 'realizada'
      : cobranca.situacao === 'pendente'
        ? 'proxima'
        : cobranca.situacao,
  };
}

export default function FinanceiroScreen() {
  const [transacoes, setTransacoes] = useState<Transacao[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('todos');
  const [minimumAmount, setMinimumAmount] = useState('');
  const [maximumAmount, setMaximumAmount] = useState('');
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [filterPanel, setFilterPanel] = useState<FilterPanel>(null);
  const [datePickerTarget, setDatePickerTarget] = useState<DateFilterTarget | null>(null);

  const loadTransactions = useCallback(
    async () => (await obterMinhasCobrancas()).map(mapearCobranca),
    [],
  );

  const handleLoadError = useCallback((error: unknown) => {
    console.error('Erro ao carregar cobranças:', error);
    setLoadError(
      error instanceof Error
        ? error.message
        : 'Não foi possível carregar as cobranças.',
    );
  }, []);

  const retryTransactions = () => {
    setLoading(true);
    setLoadError(null);
    void loadTransactions()
      .then(setTransacoes)
      .catch(handleLoadError)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let active = true;
    loadTransactions()
      .then((data) => {
        if (active) setTransacoes(data);
      })
      .catch((error: unknown) => {
        if (active) handleLoadError(error);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [handleLoadError, loadTransactions]);

  const parsedMinimum = parseCurrencyInput(minimumAmount);
  const parsedMaximum = parseCurrencyInput(maximumAmount);
  const invalidAmountRange = parsedMinimum !== null
    && parsedMaximum !== null
    && parsedMinimum > parsedMaximum;
  const invalidDateRange = startDate !== null
    && endDate !== null
    && startDate.getTime() > endDate.getTime();

  const filteredTransactions = useMemo(() => {
    if (invalidAmountRange || invalidDateRange) {
      return [];
    }

    return transacoes.filter((item) => {
      if (statusFilter !== 'todos' && item.status !== statusFilter) {
        return false;
      }
      if (parsedMinimum !== null && item.valor < parsedMinimum) {
        return false;
      }
      if (parsedMaximum !== null && item.valor > parsedMaximum) {
        return false;
      }

      if (startDate || endDate) {
        const transactionDate = getTransactionDate(item.dataOriginal);
        if (!transactionDate) {
          return false;
        }
        if (startDate && transactionDate < startDate) {
          return false;
        }
        if (endDate && transactionDate > endDate) {
          return false;
        }
      }

      return true;
    });
  }, [
    endDate,
    invalidAmountRange,
    invalidDateRange,
    parsedMaximum,
    parsedMinimum,
    startDate,
    statusFilter,
    transacoes,
  ]);

  const itensEmAberto = useMemo(() => filteredTransactions
    .filter(item => item.status === 'vencida' || item.status === 'proxima')
    .sort((a, b) => (
      (getTransactionDate(a.dataOriginal)?.getTime() ?? 0)
      - (getTransactionDate(b.dataOriginal)?.getTime() ?? 0)
    )), [filteredTransactions]);

  const totalEmAberto = useMemo(() => {
    return itensEmAberto.reduce((acc, curr) => acc + curr.valor, 0);
  }, [itensEmAberto]);

  const proximoVencimentoItem = itensEmAberto.length > 0 ? itensEmAberto[0] : null;

  // Mantém cobranças pagas e canceladas no histórico.
  const historicoTransacoes = useMemo(() => {
    return filteredTransactions
      .filter(item => item.status === 'realizada' || item.status === 'cancelada')
      .sort((a, b) => (
        (getTransactionDate(b.dataPagamento ?? b.dataOriginal)?.getTime() ?? 0)
        - (getTransactionDate(a.dataPagamento ?? a.dataOriginal)?.getTime() ?? 0)
      ));
  }, [filteredTransactions]);

  const toggleFilterPanel = (panel: Exclude<FilterPanel, null>) => {
    setDatePickerTarget(null);
    setFilterPanel((current) => current === panel ? null : panel);
  };

  const resetFilters = () => {
    setStatusFilter('todos');
    setMinimumAmount('');
    setMaximumAmount('');
    setStartDate(null);
    setEndDate(null);
    setDatePickerTarget(null);
  };

  const handleDateChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
    if (selectedDate && datePickerTarget) {
      const selectedDay = new Date(
        selectedDate.getFullYear(),
        selectedDate.getMonth(),
        selectedDate.getDate(),
      );

      if (datePickerTarget === 'inicio') {
        setStartDate(selectedDay);
        if (endDate && selectedDay > endDate) {
          setEndDate(null);
        }
      } else {
        setEndDate(selectedDay);
        if (startDate && selectedDay < startDate) {
          setStartDate(null);
        }
      }
    }

    if (Platform.OS !== 'ios' || event.type === 'dismissed') {
      setDatePickerTarget(null);
    }
  };

  const getStatusFilterLabel = (filter: StatusFilter) => (
    filter === 'todos' ? 'Todos' : StatusConfig[filter].texto
  );
  const amountFilterLabel = parsedMinimum !== null || parsedMaximum !== null
    ? `${parsedMinimum ?? 0}–${parsedMaximum ?? '∞'}`
    : 'VALOR';
  const dateFilterLabel = startDate || endDate
    ? `${startDate?.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) ?? '...'}–${endDate?.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) ?? '...'}`
    : 'DATA';

  // Renderizador de badge baseado no StatusConfig
  const renderBadge = (statusKey: keyof typeof StatusConfig) => {
    const config = StatusConfig[statusKey];
    if (!config) return null;

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

      <LinearGradient
        colors={['#7B0087', '#980070', '#C40E35']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View style={styles.headerText}>
            <Text style={styles.textPage}>Financeiro</Text>
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

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>

      {loading && <ActivityIndicator color="#7B0087" size="large" />}
      {loadError && (
        <View>
          <Text>{loadError}</Text>
          <Pressable onPress={retryTransactions} accessibilityRole="button">
            <Text>Tentar novamente</Text>
          </Pressable>
        </View>
      )}

      <LinearGradient
        colors={['#7B0087', '#980070', '#C40E35']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.card}
      >
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Total em aberto:</Text>
          <Text style={styles.cardAmount}>
            {totalEmAberto.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </Text>
          <Text style={styles.cardDueDate}>
            {proximoVencimentoItem 
              ? `Próximo do vencimento: ${proximoVencimentoItem.vencimento}` 
              : 'Nenhum vencimento próximo'}
          </Text>
          <Text style={styles.cardDueDate}>O pagamento é realizado fora do app.</Text>
        </View>
        
      </LinearGradient>

        <View style={styles.filterContainer}>
          <Pressable
            style={[styles.filterButton, filterPanel === 'status' && styles.filterButtonActive]}
            onPress={() => toggleFilterPanel('status')}
            accessibilityRole="button"
            accessibilityLabel={`Filtrar por status: ${getStatusFilterLabel(statusFilter)}`}
          >
            <Text numberOfLines={1} style={styles.filterText}>
              {statusFilter === 'todos' ? 'STATUS' : getStatusFilterLabel(statusFilter)}
            </Text>
            <Feather name="filter" size={14} color="#ffffff" style={styles.filterIcon} />
          </Pressable>

          <Pressable
            style={[styles.filterButton, filterPanel === 'valor' && styles.filterButtonActive]}
            onPress={() => toggleFilterPanel('valor')}
            accessibilityRole="button"
            accessibilityLabel={`Filtrar por valor: mínimo ${parsedMinimum ?? 'sem limite'}, máximo ${parsedMaximum ?? 'sem limite'}`}
          >
            <Text numberOfLines={1} style={styles.filterText}>{amountFilterLabel}</Text>
            <Feather name="filter" size={14} color="#ffffff" style={styles.filterIcon} />
          </Pressable>

          <Pressable
            style={[styles.filterButton, filterPanel === 'data' && styles.filterButtonActive]}
            onPress={() => toggleFilterPanel('data')}
            accessibilityRole="button"
            accessibilityLabel={`Filtrar por vencimento: ${startDate ? formatDateFilter(startDate) : 'sem data inicial'} a ${endDate ? formatDateFilter(endDate) : 'sem data final'}`}
          >
            <Text numberOfLines={1} style={styles.filterText}>{dateFilterLabel}</Text>
            <Feather name="filter" size={14} color="#ffffff" style={styles.filterIcon} />
          </Pressable>
        </View>

        {filterPanel && (
          <View style={styles.filterPanel}>
            {filterPanel === 'status' && (
              <>
                <Text style={styles.filterPanelTitle}>Filtrar por status</Text>
                <View style={styles.statusOptions}>
                  {statusOptions.map((option) => {
                    const selected = statusFilter === option;
                    return (
                      <Pressable
                        key={option}
                        style={[styles.statusOption, selected && styles.statusOptionSelected]}
                        onPress={() => setStatusFilter(option)}
                        accessibilityRole="button"
                        accessibilityState={{ selected }}
                      >
                        <Text style={[styles.statusOptionText, selected && styles.statusOptionTextSelected]}>
                          {getStatusFilterLabel(option)}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </>
            )}

            {filterPanel === 'valor' && (
              <>
                <Text style={styles.filterPanelTitle}>Faixa de valor</Text>
                <View style={styles.rangeInputs}>
                  <View style={styles.rangeInputGroup}>
                    <Text style={styles.rangeInputLabel}>Mínimo (R$)</Text>
                    <TextInput
                      value={minimumAmount}
                      onChangeText={setMinimumAmount}
                      placeholder="0,00"
                      keyboardType="decimal-pad"
                      accessibilityLabel="Valor mínimo"
                      style={styles.rangeInput}
                    />
                  </View>
                  <View style={styles.rangeInputGroup}>
                    <Text style={styles.rangeInputLabel}>Máximo (R$)</Text>
                    <TextInput
                      value={maximumAmount}
                      onChangeText={setMaximumAmount}
                      placeholder="Sem limite"
                      keyboardType="decimal-pad"
                      accessibilityLabel="Valor máximo"
                      style={styles.rangeInput}
                    />
                  </View>
                </View>
                {invalidAmountRange && (
                  <Text style={styles.filterError}>O valor mínimo não pode superar o máximo.</Text>
                )}
              </>
            )}

            {filterPanel === 'data' && (
              <>
                <Text style={styles.filterPanelTitle}>Período de vencimento</Text>
                <View style={styles.rangeInputs}>
                  <Pressable
                    style={styles.dateFilterButton}
                    onPress={() => setDatePickerTarget('inicio')}
                    accessibilityRole="button"
                    accessibilityLabel="Selecionar data inicial"
                  >
                    <View>
                      <Text style={styles.dateFilterLabel}>De</Text>
                      <Text style={startDate ? styles.dateFilterValue : styles.dateFilterPlaceholder}>
                        {startDate ? formatDateFilter(startDate) : 'Data inicial'}
                      </Text>
                    </View>
                    <Feather name="calendar" size={19} color="#84009A" />
                  </Pressable>
                  <Pressable
                    style={styles.dateFilterButton}
                    onPress={() => setDatePickerTarget('fim')}
                    accessibilityRole="button"
                    accessibilityLabel="Selecionar data final"
                  >
                    <View>
                      <Text style={styles.dateFilterLabel}>Até</Text>
                      <Text style={endDate ? styles.dateFilterValue : styles.dateFilterPlaceholder}>
                        {endDate ? formatDateFilter(endDate) : 'Data final'}
                      </Text>
                    </View>
                    <Feather name="calendar" size={19} color="#84009A" />
                  </Pressable>
                </View>
                {invalidDateRange && (
                  <Text style={styles.filterError}>A data inicial não pode ser posterior à final.</Text>
                )}
                {datePickerTarget && (
                  <View style={styles.datePickerContainer}>
                    <DateTimePicker
                      value={
                        (datePickerTarget === 'inicio' ? startDate : endDate)
                        ?? (datePickerTarget === 'fim' ? startDate : endDate)
                        ?? new Date()
                      }
                      mode="date"
                      display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                      minimumDate={datePickerTarget === 'fim' ? startDate ?? undefined : undefined}
                      maximumDate={datePickerTarget === 'inicio' ? endDate ?? undefined : undefined}
                      onChange={handleDateChange}
                    />
                    {Platform.OS === 'ios' && (
                      <Pressable
                        style={styles.datePickerDone}
                        onPress={() => setDatePickerTarget(null)}
                        accessibilityRole="button"
                      >
                        <Text style={styles.datePickerDoneText}>Concluir</Text>
                      </Pressable>
                    )}
                  </View>
                )}
              </>
            )}

            <Pressable
              style={styles.clearFiltersButton}
              onPress={resetFilters}
              accessibilityRole="button"
            >
              <Text style={styles.clearFiltersText}>Limpar filtros</Text>
            </Pressable>
          </View>
        )}

        {/* Seção: Em Aberto */}
        <View style={styles.sectionHeaderContainer}>
          <Text style={styles.sectionTitle}>EM ABERTO</Text>
        </View>

        {itensEmAberto.map((item) => (
          <View key={item.id} style={styles.transactionItem}>
            <View style={styles.transactionInfo}>
              <Text style={styles.transactionName}>{item.nome}</Text>
              <Text style={styles.transactionSubText}>
                {item.status === 'vencida' ? `Vencido em ${item.vencimento}` : `Vence em ${item.vencimento}`}
              </Text>
            </View>
            <View style={styles.transactionRight}>
              {renderBadge(item.status)}
              <Text style={[styles.transactionAmount, { color: StatusConfig[item.status].cor }]}>
                {item.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </Text>
            </View>
          </View>
        ))}
        {itensEmAberto.length === 0 && (
          <Text style={styles.emptyState}>Nenhuma cobrança corresponde aos filtros.</Text>
        )}

        {/* Seção: Histórico */}
        <View style={[styles.sectionHeaderContainer, { marginTop: 24 }]}>
          <Text style={styles.sectionTitle}>HISTÓRICO</Text>
        </View>

        {historicoTransacoes.map((item) => (
          <View key={item.id} style={styles.transactionItem}>
            <View style={styles.transactionInfo}>
              <Text style={styles.transactionName}>{item.nome}</Text>
              <Text style={styles.transactionSubText}>
                {item.status === 'cancelada'
                  ? `Cancelada · vencimento em ${item.vencimento}`
                  : item.dataPagamento
                    ? `Paga em ${getTransactionDate(item.dataPagamento)?.toLocaleDateString('pt-BR') ?? item.vencimento}`
                    : `Vencimento em ${item.vencimento}`}
              </Text>
            </View>
            <View style={styles.transactionRight}>
              {renderBadge(item.status)}
              <Text style={[styles.transactionAmount, { color: StatusConfig[item.status].cor }]}>
                {item.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </Text>
            </View>
          </View>
        ))}
        {historicoTransacoes.length === 0 && (
          <Text style={styles.emptyState}>Nenhuma cobrança no histórico corresponde aos filtros.</Text>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
