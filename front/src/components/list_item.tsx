import { ActivityIndicator, View, Text, Pressable } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { styles } from "@/screens/Home/list.styles";
import { fileStyles } from "@/screens/list_item.styles";

export type ListItemCategory = "Aula" | "Atividade" | "Pagamento";

export const StatusConfig = {
    vencida: {
        icone: "time-outline",
        cor: "#ef4444",
    },
    proxima: {
        icone: "time-outline",
        cor: "#f59e0b",
    },
    realizada: {
        icone: "checkbox-outline",
        cor: "#10b981",
    },
} satisfies Record<string, { icone: keyof typeof Ionicons.glyphMap; cor: string }>;

export type ListItemStatus = keyof typeof StatusConfig;

type ComponentList = {
    titulo: string;
    categoria: ListItemCategory;
    dataHora: string;
    nomeAluno?: string;
    status: ListItemStatus;
    onPress: () => void;
};

type FolderListItem = {
    titulo: string;
    tipoArquivo: "pasta";
    detalhes?: string;
    onPress: () => void;
};

type DocumentListItem = {
    titulo: string;
    tipoArquivo: "arquivo";
    detalhes?: string;
    onPress: () => void;
    onDownload: () => void;
    downloadLoading?: boolean;
};

type FileListItem = FolderListItem | DocumentListItem;

export function List_item({
    titulo,
    dataHora,
    nomeAluno,
    status,
    onPress
}: ComponentList) {
    const currentConfig = StatusConfig[status];

    return (
        <Pressable
            style={styles.containerList}
            onPress={onPress}
        >
            <View style={[styles.lateralBar, { backgroundColor: currentConfig.cor }]} />

            <View style={styles.containerInfos}>
                <View style={[styles.iconContainer, { backgroundColor: currentConfig.cor + "20" }]}>
                    <Ionicons name={currentConfig.icone} size={24} color={currentConfig.cor} />
                </View>

                <View>
                    <Text style={styles.mainTitle}>{titulo}</Text>
                    {nomeAluno && <Text style={styles.infosList}>{nomeAluno}</Text>}
                    <Text style={styles.infosList}>{dataHora}</Text>
                </View>
            </View>
        </Pressable>
    );
}

export function List_item_Arquivo(props: FileListItem) {
    if (props.tipoArquivo === "pasta") {
        return (
            <Pressable
                style={({ pressed }) => [fileStyles.folder, pressed && fileStyles.pressed]}
                onPress={props.onPress}
                accessibilityRole="button"
                accessibilityLabel={`Abrir pasta ${props.titulo}`}
            >
                <View style={fileStyles.iconFolder}>
                    <Ionicons name="folder" size={27} color="#B77900" />
                </View>
                <View style={fileStyles.fileInfo}>
                    <Text style={fileStyles.fileTitle} numberOfLines={1}>{props.titulo}</Text>
                    {props.detalhes && <Text style={fileStyles.fileDetails}>{props.detalhes}</Text>}
                </View>
                <Ionicons name="chevron-forward" size={20} color="#8A8290" />
            </Pressable>
        );
    }

    return (
        <View style={fileStyles.document}>
            <Pressable
                style={({ pressed }) => [fileStyles.documentMain, pressed && fileStyles.pressed]}
                onPress={props.onPress}
                accessibilityRole="button"
                accessibilityLabel={`Abrir ${props.titulo}`}
            >
                <View style={fileStyles.iconDocument}>
                    <Ionicons name="document-text" size={25} color="#B4233A" />
                </View>
                <View style={fileStyles.fileInfo}>
                    <Text style={fileStyles.fileTitle} numberOfLines={1}>{props.titulo}</Text>
                    {props.detalhes && <Text style={fileStyles.fileDetails}>{props.detalhes}</Text>}
                </View>
            </Pressable>
            <Pressable
                style={({ pressed }) => [
                    fileStyles.downloadButton,
                    pressed && fileStyles.pressed,
                    props.downloadLoading && fileStyles.disabled,
                ]}
                onPress={props.onDownload}
                disabled={props.downloadLoading}
                accessibilityRole="button"
                accessibilityLabel={`Baixar ${props.titulo}`}
                accessibilityState={{ disabled: props.downloadLoading }}
            >
                {props.downloadLoading ? (
                    <ActivityIndicator size="small" color="#7B0087" />
                ) : (
                    <Ionicons name="download-outline" size={22} color="#7B0087" />
                )}
            </Pressable>
        </View>
    );
}