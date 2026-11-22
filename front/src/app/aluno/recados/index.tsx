import { LinearGradient } from "expo-linear-gradient";
import { Alert, Linking, Platform, Pressable, SafeAreaView, ScrollView, StatusBar, Text, View, } from "react-native";
import DateTimePicker, { type DateTimePickerEvent } from "@react-native-community/datetimepicker";
import { router } from "expo-router";
import { Feather, Ionicons } from "@expo/vector-icons";
import { useMemo, useState } from "react";
import { styles } from "@/screens/Recados/recados.styles";

type Recado = {
  id: string;
  data: string;
  texto: string;
  link?: string;
};

type DateFilterTarget = "start" | "end";

const demoRecado: Recado = {
  id: "boas-vindas",
  data: "2003-08-14",
  texto:
    "Queridos alunos, sejam todos bem-vindos à nossa plataforma de estudos. Aqui vocês poderão consultar a agenda, pagamentos, calendário e eventos.",
  link: "https://meet.jit.si/ElCaminoIdiomas",
};

const recadosHistorico: Recado[] = [demoRecado];

function getLocalDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;

  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  if (
    date.getFullYear() !== Number(match[1])
    || date.getMonth() !== Number(match[2]) - 1
    || date.getDate() !== Number(match[3])
  ) {
    return null;
  }
  return date;
}

function formatDate(value: Date | null): string {
  return value?.toLocaleDateString("pt-BR") ?? "";
}

export default function Recados_View() {
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [filterOpen, setFilterOpen] = useState(false);
  const [datePickerTarget, setDatePickerTarget] = useState<DateFilterTarget | null>(null);

  const invalidDateRange = startDate !== null
    && endDate !== null
    && startDate.getTime() > endDate.getTime();

  const filteredRecados = useMemo(() => {
    if (invalidDateRange) return [];

    return recadosHistorico.filter((recado) => {
      const date = getLocalDate(recado.data);
      if (!date) return false;
      if (startDate && date < startDate) return false;
      if (endDate && date > endDate) return false;
      return true;
    });
  }, [endDate, invalidDateRange, startDate]);

  const dateFilterLabel = startDate || endDate
    ? `${startDate?.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) ?? "..."}–${endDate?.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) ?? "..."}`
    : "DATA";

  const handleDateChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
    if (selectedDate && datePickerTarget) {
      const selectedDay = new Date(
        selectedDate.getFullYear(),
        selectedDate.getMonth(),
        selectedDate.getDate(),
      );

      if (datePickerTarget === "start") {
        setStartDate(selectedDay);
        if (endDate && selectedDay > endDate) setEndDate(null);
      } else {
        setEndDate(selectedDay);
        if (startDate && selectedDay < startDate) setStartDate(null);
      }
    }

    if (Platform.OS !== "ios" || event.type === "dismissed") {
      setDatePickerTarget(null);
    }
  };

  const openMeetingLink = async () => {
    if (!demoRecado.link) return;
    try {
      await Linking.openURL(demoRecado.link);
    } catch (error) {
      console.error("Erro ao abrir o link do recado:", error);
      Alert.alert("Erro", "Não foi possível abrir o link do recado.");
    }
  };

  const clearDateFilter = () => {
    setStartDate(null);
    setEndDate(null);
    setDatePickerTarget(null);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#7B0087" />

      <LinearGradient
        colors={["#7B0087", "#980070", "#C40E35"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View style={styles.headerActionPlaceholder} />
          <View style={styles.headerText}>
            <Text style={styles.textPage}>Mural de Recados</Text>
          </View>
          <Pressable
            onPress={() => router.push("/Menu")}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Abrir menu"
            style={({ pressed }) => [styles.headerAction, pressed && styles.menuButtonPressed]}
          >
            <Feather name="menu" size={30} color="#FFFFFF" />
          </Pressable>
        </View>
      </LinearGradient>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.sectionHeader}>
          <View style={styles.sectionHeading}>
            <View style={styles.sectionIcon}>
              <Ionicons name="megaphone-outline" size={19} color="#84009A" />
            </View>
            <Text style={styles.sectionTitle}>Recado Geral</Text>
          </View>
        </View>

        <View style={styles.generalCard}>
          <View style={styles.generalCardHeader}>
            <View style={styles.generalBadge}>
              <Text style={styles.generalBadgeText}>COMUNICADO</Text>
            </View>
              <View style={styles.historyDate}>
                <Feather name="calendar" size={14} color="#84009A" />
                <Text style={styles.historyDateText}>{formatDate(getLocalDate(demoRecado.data))}</Text>
              </View>

          </View>
          <Text style={styles.messageText}>{demoRecado.texto}</Text>
          {demoRecado.link && (
            <Pressable
              onPress={() => void openMeetingLink()}
              accessibilityRole="link"
              accessibilityLabel="Abrir link das aulas"
              style={({ pressed }) => [styles.messageLink, pressed && styles.messageLinkPressed]}
            >
              <Feather name="video" size={16} color="#7B0087" />
              <Text style={styles.messageLinkText}>Acessar link das aulas</Text>
              <Feather name="external-link" size={14} color="#7B0087" />
            </Pressable>
          )}
        </View>

        <View style={[styles.sectionHeader, styles.historyHeader]}>
          <View style={styles.sectionHeading}>
            <View style={styles.sectionIcon}>
              <Feather name="clock" size={18} color="#84009A" />
            </View>
            <Text style={styles.sectionTitle}>Histórico de Recados</Text>
          </View>
        </View>

        <View style={styles.filterContainer}>
          <Pressable
            style={[styles.filterButton, filterOpen && styles.filterButtonActive]}
            onPress={() => {
              setFilterOpen((current) => !current);
              setDatePickerTarget(null);
            }}
            accessibilityRole="button"
            accessibilityLabel={`Filtrar recados por data${startDate || endDate ? `: ${dateFilterLabel}` : ""}`}
          >
            <Text numberOfLines={1} style={styles.filterText}>{dateFilterLabel}</Text>
            <Feather name="filter" size={14} color="#FFFFFF" style={styles.filterIcon} />
          </Pressable>
        </View>

        {filterOpen && (
          <View style={styles.filterPanel}>
            <Text style={styles.filterPanelTitle}>Período dos recados</Text>
            <View style={styles.rangeInputs}>
              <Pressable
                style={styles.dateFilterButton}
                onPress={() => setDatePickerTarget("start")}
                accessibilityRole="button"
                accessibilityLabel="Selecionar data inicial"
              >
                <View>
                  <Text style={styles.dateFilterLabel}>De</Text>
                  <Text style={startDate ? styles.dateFilterValue : styles.dateFilterPlaceholder}>
                    {startDate ? formatDate(startDate) : "Data inicial"}
                  </Text>
                </View>
                <Feather name="calendar" size={19} color="#84009A" />
              </Pressable>
              <Pressable
                style={styles.dateFilterButton}
                onPress={() => setDatePickerTarget("end")}
                accessibilityRole="button"
                accessibilityLabel="Selecionar data final"
              >
                <View>
                  <Text style={styles.dateFilterLabel}>Até</Text>
                  <Text style={endDate ? styles.dateFilterValue : styles.dateFilterPlaceholder}>
                    {endDate ? formatDate(endDate) : "Data final"}
                  </Text>
                </View>
                <Feather name="calendar" size={19} color="#84009A" />
              </Pressable>
            </View>
            {invalidDateRange && (
              <Text style={styles.filterError}>
                A data inicial não pode ser posterior à final.
              </Text>
            )}
            {datePickerTarget && (
              <View style={styles.datePickerContainer}>
                <DateTimePicker
                  value={
                    (datePickerTarget === "start" ? startDate : endDate)
                    ?? startDate
                    ?? endDate
                    ?? new Date()
                  }
                  mode="date"
                  display={Platform.OS === "ios" ? "spinner" : "default"}
                  minimumDate={datePickerTarget === "end" ? startDate ?? undefined : undefined}
                  maximumDate={datePickerTarget === "start" ? endDate ?? undefined : undefined}
                  onChange={handleDateChange}
                />
                {Platform.OS === "ios" && (
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
            <Pressable
              style={styles.clearFiltersButton}
              onPress={clearDateFilter}
              accessibilityRole="button"
            >
              <Text style={styles.clearFiltersText}>Limpar filtro</Text>
            </Pressable>
          </View>
        )}

        {filteredRecados.map((recado) => {
          const date = getLocalDate(recado.data);
          return (
            <View key={recado.id} style={styles.historyCard}>
              <View style={styles.historyDate}>
                <Feather name="calendar" size={14} color="#84009A" />
                <Text style={styles.historyDateText}>{formatDate(date)}</Text>
              </View>
              <Text style={styles.messageText}>{recado.texto}</Text>
            </View>
          );
        })}
        {filteredRecados.length === 0 && (
          <Text style={styles.emptyState}>Nenhum recado encontrado nesse período.</Text>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
