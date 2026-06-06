import type { NavKey } from "./types";

export type Locale = "en" | "si";

type Dictionary = {
  appTitle: string;
  appSubtitle: string;
  pages: Record<NavKey, string>;
  commandPlaceholder: string;
  offline: string;
};

const dictionaries: Record<Locale, Dictionary> = {
  en: {
    appTitle: "LKP Command Layer",
    appSubtitle: "Desktop command center for Jarvis operations, approvals, and collaboration.",
    pages: {
      dashboard: "Dashboard",
      agents: "Agents",
      tasks: "Tasks",
      approvals: "Approvals",
      projects: "Projects",
      memory: "Memory",
      knowledge: "Knowledge",
      logs: "Logs",
      reports: "Reports",
      collaboration: "Collaboration",
      voice: "Voice",
      settings: "Settings",
    },
    commandPlaceholder: "Search tasks, agents, memory, and logs",
    offline: "Offline cache mode",
  },
  si: {
    appTitle: "LKP Command Layer",
    appSubtitle: "Jarvis operations, approvals සහ collaboration එකම desktop command center එකකින්.",
    pages: {
      dashboard: "Dashboard",
      agents: "Agents",
      tasks: "Tasks",
      approvals: "Approvals",
      projects: "Projects",
      memory: "Memory",
      knowledge: "Knowledge",
      logs: "Logs",
      reports: "Reports",
      collaboration: "Collaboration",
      voice: "Voice",
      settings: "Settings",
    },
    commandPlaceholder: "Tasks, agents, memory, logs search කරන්න",
    offline: "Offline cache mode",
  },
};

export function t(locale: Locale): Dictionary {
  return dictionaries[locale];
}
