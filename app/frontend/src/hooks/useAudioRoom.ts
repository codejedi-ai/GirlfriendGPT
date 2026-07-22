import { useState, useCallback, useRef, useEffect } from "react";
import {
  Room,
  RoomEvent,
  ConnectionState,
  Track,
  RemoteTrackPublication,
  RemoteParticipant,
  LocalParticipant,
} from "livekit-client";

export type LogEntry = {
  id: number;
  time: string;
  message: string;
  type: "info" | "error" | "success";
};

export type RoomStatus = "disconnected" | "connecting" | "connected";

export function useAudioRoom() {
  const [status, setStatus] = useState<RoomStatus>("disconnected");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [micEnabled, setMicEnabled] = useState(true);
  const roomRef = useRef<Room | null>(null);
  const logIdRef = useRef(0);

  const addLog = useCallback(
    (message: string, type: LogEntry["type"] = "info") => {
      const id = ++logIdRef.current;
      const time = new Date().toLocaleTimeString("en-US", {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      setLogs((prev) => [...prev.slice(-49), { id, time, message, type }]);
    },
    []
  );

  const handleTrackSubscribed = useCallback(
    (
      track: RemoteTrackPublication["track"],
      _pub: RemoteTrackPublication,
      participant: RemoteParticipant
    ) => {
      if (track && track.kind === Track.Kind.Audio) {
        const el = track.attach();
        el.id = `audio-${participant.identity}-${track.sid}`;
        document.body.appendChild(el);
        addLog(
          `Subscribed to audio from ${participant.identity}`,
          "success"
        );
      }
    },
    [addLog]
  );

  const handleTrackUnsubscribed = useCallback(
    (
      track: RemoteTrackPublication["track"]
    ) => {
      if (track) {
        track.detach().forEach((el) => el.remove());
      }
    },
    []
  );

  const connect = useCallback(
    async (url: string, token: string) => {
      if (roomRef.current) {
        await roomRef.current.disconnect();
      }

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      roomRef.current = room;

      room.on(RoomEvent.ConnectionStateChanged, (state: ConnectionState) => {
        const stateMap: Record<string, RoomStatus> = {
          [ConnectionState.Connecting]: "connecting",
          [ConnectionState.Connected]: "connected",
          [ConnectionState.Reconnecting]: "connecting",
          [ConnectionState.Disconnected]: "disconnected",
        };
        const mapped = stateMap[state] || "disconnected";
        setStatus(mapped);
        addLog(`Connection state: ${state}`, mapped === "connected" ? "success" : "info");
      });

      room.on(
        RoomEvent.TrackSubscribed,
        handleTrackSubscribed as (...args: unknown[]) => void
      );

      room.on(
        RoomEvent.TrackUnsubscribed,
        handleTrackUnsubscribed as (...args: unknown[]) => void
      );

      room.on(RoomEvent.Disconnected, () => {
        setStatus("disconnected");
        addLog("Disconnected from room", "info");
      });

      try {
        setStatus("connecting");
        addLog("Connecting...");
        await room.connect(url, token);
        addLog(`Joined room: ${room.name}`, "success");

        await room.localParticipant.setMicrophoneEnabled(true);
        setMicEnabled(true);
        addLog("Microphone published", "success");
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        addLog(`Connection failed: ${msg}`, "error");
        setStatus("disconnected");
        roomRef.current = null;
      }
    },
    [addLog, handleTrackSubscribed, handleTrackUnsubscribed]
  );

  const disconnect = useCallback(async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
    }
    setStatus("disconnected");
  }, []);

  const toggleMic = useCallback(async () => {
    if (!roomRef.current?.localParticipant) return;
    const lp: LocalParticipant = roomRef.current.localParticipant;
    const next = !micEnabled;
    await lp.setMicrophoneEnabled(next);
    setMicEnabled(next);
    addLog(`Microphone ${next ? "enabled" : "muted"}`, "info");
  }, [micEnabled, addLog]);

  useEffect(() => {
    return () => {
      roomRef.current?.disconnect();
    };
  }, []);

  return { status, logs, micEnabled, connect, disconnect, toggleMic, addLog };
}
