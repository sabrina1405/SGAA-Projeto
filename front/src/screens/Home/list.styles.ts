import { StyleSheet } from "react-native";
import {paleta} from "@/components/theme/colors"

export const styles = StyleSheet.create({
    containerList: {
        backgroundColor: "#fff",
        width: "100%",
        height: 95,
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        gap: 20,
        borderRadius: 8,
        boxShadow: '0px 4px 10px 0px rgba(0, 0, 0, 0.15)',
    },

    lateralBar: {
        backgroundColor: paleta.purple01,
        height: 95,
        width: 25,
        borderBottomLeftRadius: 8,
        borderTopLeftRadius: 8,
    },

    containerInfos: {
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-evenly",
        gap: 20,
        padding: 10,
    },

    iconContainer: {
        width: 45,
        height: 45,
        backgroundColor: paleta.purple01,
        padding: 5,
        borderRadius: 8,
        alignItems: "center",
        justifyContent: "center",
    },
    
    mainTitle: {
        fontSize: 16,
        fontWeight: "bold",
        textAlign: "left",
        
    },
    
    infosList: {
        fontSize: 14,
        color: paleta.gray,
        textAlign: "left",
    }
});
