import {useState} from "react";
import {View, Text} from "react-native";

export default function TelaInicial() {
const [userRole, setUserRole] = useState<"professor" | "aluno" | null>(null);
const [userName, setUserName] = useState("");

return(
    <View>
        
    </View>
)
}