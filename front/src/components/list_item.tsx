import {View, Text} from "react-native";
import { styles } from "@/screens/Home/list.styles";

/* export type componentList = {
    id: string;
    titulo: string;
    categoria?: "Aula" | "Atividade" | "Pagamento"
    icone: string;
    corIcone: string;
    descricao: string;
    dataHora: String;
    barraLateral: string;
    nomeAluno?: string;

}; */

export default function List_item(){

    
    return(
        <View style={styles.containerList}>
            <View style={styles.lateralBar}>

            </View>

        <View style={styles.containerInfos}>
            <View style={styles.iconContainer}>
                 
            </View>

            <View>
                <Text style={styles.mainTitle}>Título</Text>
                <Text style={styles.infosList}>Aluno</Text>
                <Text style={styles.infosList}>Data e Hora</Text>
            </View>
        </View>

        </View>
    )
}