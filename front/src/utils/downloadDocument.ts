import { Platform } from "react-native";
import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";

export async function downloadDocument(url: string, fileName: string): Promise<void> {
    const safeFileName = fileName.replace(/[\\/:*?"<>|]/g, "_");

    if (Platform.OS === "web") {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Não foi possível baixar o documento (HTTP ${response.status}).`);
        }

        const objectUrl = URL.createObjectURL(await response.blob());
        const link = document.createElement("a");
        link.href = objectUrl;
        link.download = safeFileName;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
        return;
    }

    if (!(await Sharing.isAvailableAsync())) {
        throw new Error("O compartilhamento de arquivos não está disponível neste dispositivo.");
    }

    const destination = new File(Paths.document, safeFileName);
    const downloadedFile = await File.downloadFileAsync(url, destination, { idempotent: true });

    await Sharing.shareAsync(downloadedFile.uri, {
        mimeType: "application/pdf",
        dialogTitle: `Salvar ${safeFileName}`,
    });
}
