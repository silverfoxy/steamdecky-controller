import { callable, definePlugin } from "@decky/api";
import { ButtonItem, Field, PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { useEffect, useState } from "react";
import { FaGamepad } from "react-icons/fa";

// ── backend callables ────────────────────────────────────────────────────────

type Status = { running: boolean; busid: string | null; ip: string };
type Result = { success: boolean; error?: string; busid?: string; ip?: string };
type Deps   = { ready: boolean; usbipd: boolean; usbip: boolean; modules: boolean };

const getStatus    = callable<[], Status> ("get_status");
const startSharing = callable<[], Result> ("start_sharing");
const stopSharing  = callable<[], Result> ("stop_sharing");
const checkDeps    = callable<[], Deps>   ("check_deps");

// ── component ────────────────────────────────────────────────────────────────

function Content() {
  const [running, setRunning] = useState(false);
  const [ip,      setIp]      = useState("...");
  const [busid,   setBusid]   = useState<string | null>(null);
  const [error,   setError]   = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [deps,    setDeps]    = useState<Deps | null>(null);

  const refresh = async () => {
    const s = await getStatus();
    setRunning(s.running);
    setIp(s.ip);
    setBusid(s.busid);
  };

  useEffect(() => {
    refresh();
    checkDeps().then(setDeps);
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, []);

  const handleToggle = async () => {
    setLoading(true);
    setError(null);
    const res = running ? await stopSharing() : await startSharing();
    if (!res.success) setError(res.error ?? "Unknown error");
    await refresh();
    setLoading(false);
  };

  const depsReady = deps?.ready ?? true;

  return (
    <PanelSection title="Controller Sharing">

      <PanelSectionRow>
        <Field label="Status">
          <span style={{ color: running ? "#4caf50" : "#9e9e9e" }}>
            {running ? "● Sharing" : "○ Stopped"}
          </span>
        </Field>
      </PanelSectionRow>

      <PanelSectionRow>
        <Field label="Deck IP">{ip}</Field>
      </PanelSectionRow>

      {running && busid && (
        <PanelSectionRow>
          <Field
            label="Connect from PC"
            description={`sudo usbip attach -r ${ip} -b ${busid}`}
          />
        </PanelSectionRow>
      )}

      {deps && !depsReady && (
        <PanelSectionRow>
          <Field
            label="⚠ Missing dependencies"
            description={[
              !deps.usbipd  && "usbipd not found",
              !deps.usbip   && "usbip not found",
              !deps.modules && "kernel modules unavailable",
            ].filter(Boolean).join(" · ")}
          />
        </PanelSectionRow>
      )}

      {error && (
        <PanelSectionRow>
          <Field label="Error" description={error} />
        </PanelSectionRow>
      )}

      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={handleToggle}
          disabled={loading || !depsReady}
        >
          {loading ? "Working…" : running ? "Stop Sharing" : "Start Sharing"}
        </ButtonItem>
      </PanelSectionRow>

      {running && (
        <PanelSectionRow>
          <Field
            label="Note"
            description="The physical controller is exported to your PC. Steam UI navigation on the Deck won't work while sharing."
          />
        </PanelSectionRow>
      )}

    </PanelSection>
  );
}

// ── plugin entry ─────────────────────────────────────────────────────────────

export default definePlugin(() => ({
  title:   <div className={staticClasses.Title}>Deck Controller</div>,
  content: <Content />,
  icon:    <FaGamepad />,
}));
