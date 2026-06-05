import { useEffect, useState } from "react";
import { getJson } from "./lib/api";

type Agent = { name: string; department: string; role: string };
type Task = { id: string; message: string; status: string; selected_agent: { name: string } };

const sections = ["Dashboard", "Agents", "Tasks", "Approvals", "Memory", "Knowledge", "Logs", "Settings"];

export default function App() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [health, setHealth] = useState("loading");

  useEffect(() => {
    getJson<{ status: string }>("/health").then((data) => setHealth(data.status)).catch(() => setHealth("offline"));
    getJson<{ agents: Agent[] }>("/agents").then((data) => setAgents(data.agents.slice(0, 8))).catch(() => setAgents([]));
    getJson<{ tasks: Task[] }>("/tasks").then((data) => setTasks(data.tasks.slice(0, 8))).catch(() => setTasks([]));
  }, []);

  return (
    <div className="min-h-screen text-ink">
      <div className="mx-auto flex max-w-7xl gap-6 px-6 py-8">
        <aside className="w-72 rounded-3xl border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
          <p className="text-xs uppercase tracking-[0.3em] text-ember">Jarvis Desktop</p>
          <h1 className="mt-3 text-3xl font-semibold">LKP Command Layer</h1>
          <p className="mt-2 text-sm text-black/65">Tauri + React frontend connected to the local-first Python brain.</p>
          <nav className="mt-8 space-y-2">
            {sections.map((section) => (
              <div key={section} className="rounded-2xl border border-black/5 bg-sand/60 px-4 py-3 text-sm font-medium">
                {section}
              </div>
            ))}
          </nav>
        </aside>
        <main className="flex-1 space-y-6">
          <section className="grid gap-4 md:grid-cols-3">
            <Card title="Brain Health" value={health} accent="bg-moss" />
            <Card title="Visible Agents" value={String(agents.length)} accent="bg-ember" />
            <Card title="Recent Tasks" value={String(tasks.length)} accent="bg-ink" />
          </section>
          <section className="grid gap-6 lg:grid-cols-2">
            <Panel title="Agents">
              {agents.map((agent) => (
                <Row key={agent.name} title={agent.name} subtitle={`${agent.department} • ${agent.role}`} />
              ))}
            </Panel>
            <Panel title="Tasks">
              {tasks.map((task) => (
                <Row key={task.id} title={task.selected_agent.name} subtitle={`${task.status} • ${task.message}`} />
              ))}
            </Panel>
          </section>
        </main>
      </div>
    </div>
  );
}

function Card({ title, value, accent }: { title: string; value: string; accent: string }) {
  return (
    <div className="rounded-3xl border border-black/10 bg-white/75 p-5 shadow-sm">
      <div className={`h-2 w-16 rounded-full ${accent}`} />
      <p className="mt-4 text-sm uppercase tracking-[0.2em] text-black/45">{title}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-3xl border border-black/10 bg-white/75 p-6 shadow-sm">
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="mt-4 space-y-3">{children}</div>
    </div>
  );
}

function Row({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="rounded-2xl border border-black/10 bg-sand/60 px-4 py-3">
      <p className="font-medium">{title}</p>
      <p className="text-sm text-black/60">{subtitle}</p>
    </div>
  );
}

