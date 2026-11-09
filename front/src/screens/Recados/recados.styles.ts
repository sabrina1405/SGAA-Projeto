import { StyleSheet } from "react-native";
import { paleta } from "@/components/theme/colors";

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },

  header: {
    height: 106,
    paddingHorizontal: 13,
    paddingTop: 15,
    paddingBottom: 13,
  },

  headerContent: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },

  headerText: {
    flex: 1,
    alignItems: "center",
  },

  textPage: {
    color: "#FFFFFF",
    fontSize: 22,
    fontWeight: "bold",
    paddingVertical: 14,
  },

  headerAction: {
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 22,
  },

  headerActionPlaceholder: {
    width: 44,
    height: 44,
  },

  menuButtonPressed: {
    opacity: 0.7,
  },

  content: {
    flexGrow: 1,
    paddingHorizontal: 18,
    paddingTop: 24,
    paddingBottom: 36,
    gap: 14,
  },

  sectionHeader: {
    marginBottom: 2,
  },

  historyHeader: {
    marginTop: 10,
  },

  sectionHeading: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },

  sectionIcon: {
    width: 36,
    height: 36,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 11,
    backgroundColor: "#F5EFF7",
  },

  sectionTitle: {
    color: "#302A32",
    fontSize: 18,
    fontWeight: "700",
  },

  generalCard: {
    padding: 18,
    borderWidth: 1,
    borderColor: "#E9DDEC",
    borderRadius: 16,
    backgroundColor: "#FCF9FD",
    elevation: 2,
    shadowColor: "#000000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 7,
  },

  generalCardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
    marginBottom: 14,
  },

  generalBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    backgroundColor: "#F0E3F3",
  },

  generalBadgeText: {
    color: "#7B0087",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.6,
  },

  generalDate: {
    color: "#817887",
    fontSize: 12,
  },

  messageText: {
    color: "#49434C",
    fontSize: 14,
    lineHeight: 22,
  },

  messageLink: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "center",
    gap: 8,
    marginTop: 16,
    paddingVertical: 8,
  },

  messageLinkPressed: {
    opacity: 0.65,
  },

  messageLinkText: {
    color: "#7B0087",
    fontSize: 14,
    fontWeight: "700",
  },

  filterContainer: {
    flexDirection: "row",
    justifyContent: "flex-end",
  },

  filterButton: {
    minWidth: 112,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderRadius: 18,
    backgroundColor: paleta.purple04,
    margin: "auto",
  },

  filterButtonActive: {
    backgroundColor: paleta.purple03,
  },

  filterText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "700",
  },

  filterIcon: {
    marginLeft: 6,
  },

  filterPanel: {
    padding: 14,
    borderRadius: 12,
    backgroundColor: "#F7F1F8",
  },

  filterPanelTitle: {
    marginBottom: 10,
    color: "#333333",
    fontSize: 14,
    fontWeight: "700",
  },

  rangeInputs: {
    flexDirection: "row",
    gap: 10,
  },

  dateFilterButton: {
    flex: 1,
    minHeight: 52,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: "#E3DEE6",
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
  },

  dateFilterLabel: {
    marginBottom: 4,
    color: "#8B8790",
    fontSize: 12,
  },

  dateFilterValue: {
    color: "#28232B",
    fontSize: 14,
  },

  dateFilterPlaceholder: {
    color: "#8B8790",
    fontSize: 13,
  },

  datePickerContainer: {
    marginTop: 10,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#E3DEE6",
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
  },

  datePickerDone: {
    alignItems: "flex-end",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: "#E8E4EA",
  },

  datePickerDoneText: {
    color: "#84009A",
    fontSize: 14,
    fontWeight: "700",
  },

  filterError: {
    marginTop: 8,
    color: "#B42318",
    fontSize: 12,
  },

  clearFiltersButton: {
    alignSelf: "flex-end",
    marginTop: 10,
    paddingVertical: 6,
    paddingHorizontal: 8,
  },

  clearFiltersText: {
    color: "#84009A",
    fontSize: 12,
    fontWeight: "700",
  },

  historyCard: {
    padding: 16,
    borderWidth: 1,
    borderColor: "#ECE8ED",
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
  },

  historyDate: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    marginBottom: 10,
    alignSelf: "flex-end"
  },

  historyDateText: {
    color: "#756C79",
    fontSize: 12,
    fontWeight: "600",
  },

  emptyState: {
    paddingVertical: 12,
    color: "#777777",
    fontSize: 13,
    textAlign: "center",
  },
});
