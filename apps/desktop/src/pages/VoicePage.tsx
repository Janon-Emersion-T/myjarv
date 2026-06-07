import { useEffect, useMemo, useState } from "react";

import { createSocket } from "../lib/api";
import type { VoiceDashboard, VoiceSession } from "../lib/types";
import { Badge } from "../components/Badge";
import { Panel } from "../components/Panel";
import { InfoRow, StatusBadge } from "../components/Rows";

export function VoicePage({
  dashboard,
  sessions,
  onCreateSession,
  onSendCommand,
  onInterrupt,
  onResume,
  onReplay,
}: {
  dashboard: VoiceDashboard | null;
  sessions: VoiceSession[];
  onCreateSession: (payload: { mode: string; text?: string; locale?: string; speaker_id?: string }) => Promise<VoiceSession>;
  onSendCommand: (sessionId: string, payload: { text: string; requested_action?: string; locale?: string; speaker_id?: string }) => Promise<unknown>;
  onInterrupt: (sessionId: string) => Promise<void>;
  onResume: (sessionId: string) => Promise<void>;
  onReplay: (sessionId: string) => Promise<void>;
}) {
  const [mode, setMode] = useState("desktop_assistant");
  const [command, setCommand] = useState("Jarvis, show me the latest approvals");
  const [selectedId, setSelectedId] = useState<string | null>(sessions[0]?.id ?? null);
  const [liveEvent, setLiveEvent] = useState<string>("Waiting for voice activity");

  const selectedSession = useMemo(
    () => sessions.find((session) => session.id === selectedId) ?? sessions[0] ?? null,
    [selectedId, sessions],
  );

  useEffect(() => {
    if (!selectedSession) {
      return;
    }
    setSelectedId(selectedSession.id);
    const socket = createSocket(`/ws/voice/${selectedSession.id}`);
    socket.addEventListener("message", (event) => {
      const packet = JSON.parse(event.data) as { type: string; payload?: { message?: string } };
      if (packet.type === "event" && packet.payload?.message) {
        setLiveEvent(packet.payload.message);
      }
      if (packet.type === "snapshot") {
        setLiveEvent("Voice session snapshot connected.");
      }
    });
    return () => socket.close();
  }, [selectedSession?.id]);

  return (
    <div className="space-y-6">
      <Panel title="Voice Interaction Dashboard">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Metric title="Sessions" value={String(dashboard?.analytics.total_sessions ?? sessions.length)} />
          <Metric title="Average Confidence" value={String(dashboard?.analytics.average_confidence ?? 0)} />
          <Metric title="Emergency Sessions" value={String(dashboard?.analytics.emergency_sessions ?? 0)} />
          <Metric title="Personality Engine" value={String(dashboard?.config.personality_engine ?? "jarvis")} />
        </div>
      </Panel>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Panel title="STT / TTS Controls">
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm font-medium text-slate-700">Mode</span>
                <select value={mode} onChange={(event) => setMode(event.target.value)} className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm">
                  {(dashboard?.modes ?? ["command", "conversation", "desktop_assistant", "emergency"]).map((entry) => (
                    <option key={entry} value={entry}>
                      {entry}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-2">
                <span className="text-sm font-medium text-slate-700">Live Event</span>
                <div className="rounded-2xl border border-black/10 bg-sand/55 px-4 py-3 text-sm text-slate-700">{liveEvent}</div>
              </label>
            </div>
            <label className="space-y-2">
              <span className="text-sm font-medium text-slate-700">Voice Command</span>
              <textarea
                value={command}
                onChange={(event) => setCommand(event.target.value)}
                className="min-h-32 w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={async () => {
                  const session = await onCreateSession({ mode, text: command });
                  setSelectedId(session.id);
                }}
                className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-white"
              >
                Start Session
              </button>
              {selectedSession ? (
                <>
                  <button
                    type="button"
                    onClick={() => void onSendCommand(selectedSession.id, { text: command, requested_action: mode })}
                    className="rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm font-medium text-slate-700"
                  >
                    Send Command
                  </button>
                  <button type="button" onClick={() => void onInterrupt(selectedSession.id)} className="rounded-2xl bg-amber-500 px-4 py-3 text-sm font-medium text-white">
                    Interrupt
                  </button>
                  <button type="button" onClick={() => void onResume(selectedSession.id)} className="rounded-2xl bg-moss px-4 py-3 text-sm font-medium text-white">
                    Resume
                  </button>
                  <button type="button" onClick={() => void onReplay(selectedSession.id)} className="rounded-2xl bg-ember px-4 py-3 text-sm font-medium text-white">
                    Replay
                  </button>
                </>
              ) : null}
            </div>
          </div>
        </Panel>

        <Panel title="Audio Devices and Voice Security">
          <div className="space-y-3">
            <InfoRow title="Microphones" subtitle={(dashboard?.devices.inputs ?? []).map((item) => String(item["label"])).join(", ")} />
            <InfoRow title="Speakers" subtitle={(dashboard?.devices.outputs ?? []).map((item) => String(item["label"])).join(", ")} />
            <InfoRow title="Security" subtitle="Authorized speakers, voice risk scoring, and emergency command restrictions are active." />
            <InfoRow title="Wake Word Provider" subtitle={String(dashboard?.config.wake_word_provider ?? "porcupine")} />
            <InfoRow title="Personality Stance" subtitle={String(dashboard?.config.personality_stance ?? "calm, direct, approval-aware")} />
            <InfoRow title="Response Contract" subtitle={String(dashboard?.config.response_contract ?? "traceable operator support")} />
            <InfoRow title="Mobile Assistant Architecture" subtitle={String(dashboard?.config.mobile_architecture ?? "transport-ready for cross-device sync, Android/iOS integration, and Flutter clients.")} />
            <InfoRow
              title="Tone Distribution"
              subtitle={
                Object.entries((dashboard?.analytics.tone_counts as Record<string, number> | undefined) ?? {})
                  .map(([tone, count]) => `${tone}:${count}`)
                  .join(" • ") || "No tone data yet"
              }
            />
          </div>
        </Panel>
      </div>

      <Panel title="Voice Sessions">
        <div className="space-y-4">
          {sessions.map((session) => (
            <div key={session.id} className="rounded-2xl border border-black/10 bg-sand/55 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <button type="button" onClick={() => setSelectedId(session.id)} className="text-left text-lg font-semibold text-slate-900">
                    {session.mode} • {session.speaker_id}
                  </button>
                  <p className="mt-1 text-sm text-slate-600">
                    {session.stt_provider} → {session.tts_provider} • {session.transport} • wake word {session.wake_word}
                  </p>
                  <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                    {String(session.analytics?.["tone_profile"] ?? "conversational")} tone • {String(session.analytics?.["response_style"] ?? "guided")} style •{" "}
                    {String(session.analytics?.["guardrail_state"] ?? "policy active")}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={session.status} />
                  <Badge tone={session.speaker_authorized ? "success" : "danger"}>{session.speaker_authorized ? "authorized" : "blocked"}</Badge>
                </div>
              </div>
              <div className="mt-4 grid gap-3 xl:grid-cols-2">
                {(session.interactions ?? []).slice(0, 4).map((item) => (
                  <InfoRow
                    key={item.id}
                    title={`${item.intent} • ${(item.confidence * 100).toFixed(0)}%`}
                    subtitle={`${item.input_text} → ${item.response_text}`}
                    meta={<StatusBadge status={item.risk_level.toLowerCase()} />}
                  />
                ))}
                {(session.events ?? []).slice(0, 4).map((event) => (
                  <InfoRow key={event.id} title={event.event_type} subtitle={event.message} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-black/10 bg-sand/55 p-4">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{title}</p>
      <p className="mt-3 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
