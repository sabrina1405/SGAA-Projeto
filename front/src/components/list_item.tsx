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
            <View>{/* Barra Lateral */}</View>

            <View>
                {/* Fundo Icone */}
                <View>{/* Icone */}</View>
            </View>

            <View>
                <Text>Título</Text>
                <Text>Aluno</Text>
                <Text>Data e Hora</Text>
            </View>

        </View>
    )
}