import { LinearGradient } from "expo-linear-gradient";
import { styles } from "@/screens/Arquivos/arquivos.styles";
import { Alert, Linking, Platform, SafeAreaView, ScrollView, Pressable, StatusBar, Text, TextInput, View } from "react-native";
import { router } from 'expo-router';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useMemo, useState } from "react";
import DateTimePicker, { type DateTimePickerEvent } from "@react-native-community/datetimepicker";
import { List_item_Arquivo } from "@/components/list_item";
import { downloadDocument } from "../utils/downloadDocument";

type FileEntry = {
    name: string;
    url: string;
    details: string;
    sizeBytes: number;
    modifiedAt: string;
};

type FilterPanel = "name" | "size" | "date" | null;
type DateFilterTarget = "start" | "end";

const demoFolder = {
    name: "Materiais de demonstração",
    documentCount: 1,
};

const demoDocument: FileEntry = {
    name: "Documento de demonstração.pdf",
    url: "https://pdfobject.com/pdf/sample.pdf",
    details: "PDF · Arquivo público de demonstração",
    sizeBytes: 18810,
    modifiedAt: "2025-04-26",
};

const standaloneDocument: FileEntry = {
    name: "Documento sem pasta.pdf",
    url: "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    details: "PDF · Arquivo público de demonstração",
    sizeBytes: 13264,
    modifiedAt: "2007-08-27",
};

const demoDocuments = [demoDocument, standaloneDocument];

function parseSizeInput(value: string): number | null {
    const normalized = value.trim().replace(",", ".");
    if (!normalized) return null;
    const size = Number(normalized);
    return Number.isFinite(size) && size >= 0 ? size : null;
}

function getLocalDate(value: string): Date | null {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
    if (!match) return null;
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

function formatFilterDate(value: Date | null): string {
    return value?.toLocaleDateString("pt-BR") ?? "";
}

export default function Arquivos_View() {
    const [folderOpen, setFolderOpen] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [filterPanel, setFilterPanel] = useState<FilterPanel>(null);
    const [nameFilter, setNameFilter] = useState("");
    const [minimumSize, setMinimumSize] = useState("");
    const [maximumSize, setMaximumSize] = useState("");
    const [startDate, setStartDate] = useState<Date | null>(null);
    const [endDate, setEndDate] = useState<Date | null>(null);
    const [datePickerTarget, setDatePickerTarget] = useState<DateFilterTarget | null>(null);

    const parsedMinimumSize = parseSizeInput(minimumSize);
    const parsedMaximumSize = parseSizeInput(maximumSize);
    const invalidSizeInput = (minimumSize.trim() !== "" && parsedMinimumSize === null)
        || (maximumSize.trim() !== "" && parsedMaximumSize === null);
    const invalidSizeRange = invalidSizeInput || (
        parsedMinimumSize !== null
        && parsedMaximumSize !== null
        && parsedMinimumSize > parsedMaximumSize
    );
    const invalidDateRange = startDate !== null
        && endDate !== null
        && startDate.getTime() > endDate.getTime();

    const filteredDocuments = useMemo(() => {
        if (invalidSizeRange || invalidDateRange) return [];

        const normalizedName = nameFilter.trim().toLocaleLowerCase("pt-BR");
        return demoDocuments.filter((document) => {
            if (!document.name.toLocaleLowerCase("pt-BR").includes(normalizedName)) {
                return false;
            }

            const sizeKb = document.sizeBytes / 1024;
            if (parsedMinimumSize !== null && sizeKb < parsedMinimumSize) return false;
            if (parsedMaximumSize !== null && sizeKb > parsedMaximumSize) return false;

            const modifiedAt = getLocalDate(document.modifiedAt);
            if (!modifiedAt) return false;
            if (startDate && modifiedAt < startDate) return false;
            if (endDate && modifiedAt > endDate) return false;
            return true;
        });
    }, [
        endDate,
        invalidDateRange,
        invalidSizeRange,
        nameFilter,
        parsedMaximumSize,
        parsedMinimumSize,
        startDate,
    ]);

    const toggleFilterPanel = (panel: Exclude<FilterPanel, null>) => {
        setDatePickerTarget(null);
        setFilterPanel((current) => current === panel ? null : panel);
    };

    const resetFilters = () => {
        setNameFilter("");
        setMinimumSize("");
        setMaximumSize("");
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

    const sizeFilterLabel = parsedMinimumSize !== null || parsedMaximumSize !== null
        ? `${parsedMinimumSize ?? 0}–${parsedMaximumSize ?? "∞"} KB`
        : "TAMANHO";
    const dateFilterLabel = startDate || endDate
        ? `${startDate?.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) ?? "..."}–${endDate?.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) ?? "..."}`
        : "DATA";

    const openDocument = async (documentUrl: string) => {
        try {
            await Linking.openURL(documentUrl);
        } catch (error) {
            console.error("Erro ao abrir documento:", error);
            Alert.alert("Erro", "Não foi possível abrir o documento.");
        }
    };

    const handleDownload = async (document: { name: string; url: string }) => {
        setDownloading(true);
        try {
            await downloadDocument(document.url, document.name);
            Alert.alert("Download concluído", "O documento foi baixado.");
        } catch (error) {
            console.error("Erro ao baixar documento:", error);
            Alert.alert(
                "Erro no download",
                error instanceof Error ? error.message : "Não foi possível baixar o documento.",
            );
        } finally {
            setDownloading(false);
        }
    };

    return(
        <SafeAreaView style={styles.container}>
            <StatusBar barStyle="light-content" backgroundColor="#7B0087" />

            <LinearGradient
                colors={['#7B0087', '#980070', '#C40E35']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.header}
            >
                <View style={styles.headerContent}>
                    {folderOpen ? (
                        <Pressable
                            onPress={() => setFolderOpen(false)}
                            hitSlop={12}
                            accessibilityRole="button"
                            accessibilityLabel="Voltar para pastas"
                            style={({ pressed }) => [
                                styles.headerAction,
                                pressed && styles.menuButtonPressed,
                            ]}
                        >
                            <Ionicons name="chevron-back" size={25} color="#FFFFFF" />
                        </Pressable>
                    ) : (
                        <View style={styles.headerActionPlaceholder} />
                    )}

                    <View style={styles.headerText}>
                        <Text style={styles.textPage}>Arquivos</Text>
                    </View>

                    <Pressable
                        onPress={() => router.push('/Menu')}
                        hitSlop={12}
                        accessibilityRole="button"
                        accessibilityLabel="Abrir menu"
                        style={({ pressed }) => [
                            styles.headerAction,
                            pressed && styles.menuButtonPressed,
                        ]}
                    >
                        <Feather name="menu" size={34} color="#FFFFFF" />
                    </Pressable>
                </View>
            </LinearGradient>

            <ScrollView
                contentContainerStyle={styles.content}
                showsVerticalScrollIndicator={false}
            >
                <View style={styles.filterContainer}>
                    <Pressable
                        style={[styles.filterButton, filterPanel === "name" && styles.filterButtonActive]}
                        onPress={() => toggleFilterPanel("name")}
                        accessibilityRole="button"
                        accessibilityLabel={`Filtrar por nome${nameFilter ? `: ${nameFilter}` : ""}`}
                    >
                        <Text numberOfLines={1} style={styles.filterText}>
                            {nameFilter.trim() || "NOME"}
                        </Text>
                        <Feather name="filter" size={14} color="#FFFFFF" style={styles.filterIcon} />
                    </Pressable>

                    <Pressable
                        style={[styles.filterButton, filterPanel === "size" && styles.filterButtonActive]}
                        onPress={() => toggleFilterPanel("size")}
                        accessibilityRole="button"
                        accessibilityLabel={`Filtrar por tamanho: mínimo ${parsedMinimumSize ?? "sem limite"} KB, máximo ${parsedMaximumSize ?? "sem limite"} KB`}
                    >
                        <Text numberOfLines={1} style={styles.filterText}>{sizeFilterLabel}</Text>
                        <Feather name="filter" size={14} color="#FFFFFF" style={styles.filterIcon} />
                    </Pressable>

                    <Pressable
                        style={[styles.filterButton, filterPanel === "date" && styles.filterButtonActive]}
                        onPress={() => toggleFilterPanel("date")}
                        accessibilityRole="button"
                        accessibilityLabel={`Filtrar por data: ${startDate ? formatFilterDate(startDate) : "sem data inicial"} a ${endDate ? formatFilterDate(endDate) : "sem data final"}`}
                    >
                        <Text numberOfLines={1} style={styles.filterText}>{dateFilterLabel}</Text>
                        <Feather name="filter" size={14} color="#FFFFFF" style={styles.filterIcon} />
                    </Pressable>
                </View>

                {filterPanel && (
                    <View style={styles.filterPanel}>
                        {filterPanel === "name" && (
                            <>
                                <Text style={styles.filterPanelTitle}>Filtrar por nome</Text>
                                <TextInput
                                    value={nameFilter}
                                    onChangeText={setNameFilter}
                                    placeholder="Digite o nome do arquivo"
                                    accessibilityLabel="Nome do arquivo"
                                    autoCapitalize="none"
                                    style={styles.rangeInput}
                                />
                            </>
                        )}

                        {filterPanel === "size" && (
                            <>
                                <Text style={styles.filterPanelTitle}>Tamanho do arquivo (KB)</Text>
                                <View style={styles.rangeInputs}>
                                    <View style={styles.rangeInputGroup}>
                                        <Text style={styles.rangeInputLabel}>Mínimo</Text>
                                        <TextInput
                                            value={minimumSize}
                                            onChangeText={setMinimumSize}
                                            placeholder="0"
                                            keyboardType="decimal-pad"
                                            accessibilityLabel="Tamanho mínimo em KB"
                                            style={styles.rangeInput}
                                        />
                                    </View>
                                    <View style={styles.rangeInputGroup}>
                                        <Text style={styles.rangeInputLabel}>Máximo</Text>
                                        <TextInput
                                            value={maximumSize}
                                            onChangeText={setMaximumSize}
                                            placeholder="Sem limite"
                                            keyboardType="decimal-pad"
                                            accessibilityLabel="Tamanho máximo em KB"
                                            style={styles.rangeInput}
                                        />
                                    </View>
                                </View>
                                {invalidSizeInput && (
                                    <Text style={styles.filterError}>
                                        Informe um tamanho válido, em KB.
                                    </Text>
                                )}
                                {!invalidSizeInput && invalidSizeRange && (
                                    <Text style={styles.filterError}>
                                        O tamanho mínimo não pode superar o máximo.
                                    </Text>
                                )}
                            </>
                        )}

                        {filterPanel === "date" && (
                            <>
                                <Text style={styles.filterPanelTitle}>Período de modificação</Text>
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
                                                {startDate ? formatFilterDate(startDate) : "Data inicial"}
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
                                                {endDate ? formatFilterDate(endDate) : "Data final"}
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

                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>
                        {folderOpen ? demoFolder.name : "Pastas e arquivos"}
                    </Text>
                </View>

                {folderOpen ? (
                    <>
                        {filteredDocuments
                            .filter((document) => document.name === demoDocument.name)
                            .map((document) => (
                                <List_item_Arquivo
                                    key={document.name}
                                    tipoArquivo="arquivo"
                                    titulo={document.name}
                                    detalhes={`${document.details} · ${(document.sizeBytes / 1024).toFixed(1)} KB · ${formatFilterDate(getLocalDate(document.modifiedAt))}`}
                                    onPress={() => openDocument(document.url)}
                                    onDownload={() => handleDownload(document)}
                                    downloadLoading={downloading}
                                />
                            ))}
                        {filteredDocuments.filter((document) => document.name === demoDocument.name).length === 0 && (
                            <Text style={styles.emptyState}>Nenhum arquivo corresponde aos filtros.</Text>
                        )}
                    </>
                ) : (
                    <>
                        {demoFolder.name.toLocaleLowerCase("pt-BR").includes(nameFilter.trim().toLocaleLowerCase("pt-BR")) && (
                            <List_item_Arquivo
                                tipoArquivo="pasta"
                                titulo={demoFolder.name}
                                detalhes={`${demoFolder.documentCount} documento`}
                                onPress={() => setFolderOpen(true)}
                            />
                        )}
                        {filteredDocuments
                            .filter((document) => document.name !== demoDocument.name)
                            .map((document) => (
                                <List_item_Arquivo
                                    key={document.name}
                                    tipoArquivo="arquivo"
                                    titulo={document.name}
                                    detalhes={`${document.details} · ${(document.sizeBytes / 1024).toFixed(1)} KB · ${formatFilterDate(getLocalDate(document.modifiedAt))}`}
                                    onPress={() => openDocument(document.url)}
                                    onDownload={() => handleDownload(document)}
                                    downloadLoading={downloading}
                                />
                            ))}
                        {filteredDocuments.length === 0
                            && !demoFolder.name.toLocaleLowerCase("pt-BR").includes(nameFilter.trim().toLocaleLowerCase("pt-BR"))
                            && <Text style={styles.emptyState}>Nenhum arquivo ou pasta corresponde aos filtros.</Text>}
                    </>
                )}

                <View style={styles.demoNotice}>
                    <Feather name="info" size={17} color="#6C5B73" />
                    <Text style={styles.demoNoticeText}>
                        Lista de demonstração. O PDF é público e não contém documentos da sua conta.
                    </Text>
                </View>
            </ScrollView>

        </SafeAreaView>
    )
};