import { StyleSheet } from "react-native";
import { paleta } from "@/components/theme/colors";

export const styles = StyleSheet.create({
    containerList: {
        backgroundColor: "#fff",
        width: "100%",
        height: 95,
        flexDirection: "row",
        alignItems: "center",
        borderRadius: 8,
        overflow: "hidden",
        elevation: 3, 
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.15,
        shadowRadius: 10,
    },

    lateralBar: {
        backgroundColor: paleta.purple01,
        height: "100%",
        width: 12, // Ajustado para ficar proporcional
    },

    containerInfos: {
        flex: 1,
        flexDirection: "row",
        alignItems: "center",
        gap: 15,
        paddingHorizontal: 15,
    },

    iconContainer: {
        width: 45,
        height: 45,
        backgroundColor: paleta.purple01 + "20", // Fundo translúcido opcional
        borderRadius: 8,
        alignItems: "center",
        justifyContent: "center",
    },
    
    mainTitle: {
        fontSize: 16,
        fontWeight: "bold",
        textAlign: "left",
        color: "#333",
    },
    
    infosList: {
        fontSize: 14,
        color: paleta.gray,
        textAlign: "left",
    }
});