import { View, Text, Pressable } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { styles } from "@/screens/Home/list.styles";

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