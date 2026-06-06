import { useEffect, useState } from "react";

import type { NavKey } from "../lib/types";

const DEFAULT_ROUTE: NavKey = "dashboard";

export function useHashRoute(): [NavKey, (next: NavKey) => void] {
  const [route, setRoute] = useState<NavKey>(() => readRoute());

  useEffect(() => {
    const onHashChange = () => setRoute(readRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  function navigate(next: NavKey) {
    window.location.hash = next;
  }

  return [route, navigate];
}

function readRoute(): NavKey {
  const hash = window.location.hash.replace("#", "");
  const routes: NavKey[] = [
    "dashboard",
    "agents",
    "tasks",
    "approvals",
    "projects",
    "memory",
    "knowledge",
    "logs",
    "reports",
    "collaboration",
    "voice",
    "settings",
  ];
  return routes.includes(hash as NavKey) ? (hash as NavKey) : DEFAULT_ROUTE;
}
