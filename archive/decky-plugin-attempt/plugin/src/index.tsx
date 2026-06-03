import {
  definePlugin,
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  staticClasses,
  ServerAPI,
} from "decky-frontend-lib";
import React, { VFC, useState, useEffect } from "react";
import { FaGamepad } from "react-icons/fa";

const Content: VFC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {
  const [status, setStatus] = useState("Loading...");
  const [ip, setIp] = useState("");
  const [clientIp, setClientIp] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [mode, setMode] = useState<"evdev" | "usbip">("evdev");
  const [usbipInfo, setUsbipInfo] = useState("");

  const loadStatus = () => {
    serverAPI.callPluginMethod("get_status", {})
      .then((res: any) => {
        if (res?.success && res?.result) {
          setIsRunning(res.result.running || false);
          setIp(res.result.deck_ip || "");
          setClientIp(res.result.client_ip || "");
          setMode(res.result.mode || "evdev");
          setUsbipInfo(res.result.usbip_info || "");

          // Update status message
          if (res.result.running) {
            if (res.result.mode === "usbip") {
              setStatus("USB/IP Active");
            } else {
              setStatus(res.result.client_ip ? "Connected" : "Waiting for client...");
            }
          } else {
            setStatus("Stopped");
          }
        }
      })
      .catch(() => setStatus("Error"));
  };

  useEffect(() => {
    loadStatus();
    // Poll status every 2 seconds when running
    const interval = setInterval(() => {
      if (isRunning) {
        loadStatus();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [isRunning]);

  const handleStart = () => {
    const method = mode === "usbip" ? "start_usbip" : "start_sharing";
    serverAPI.callPluginMethod(method, { port: 9090 })
      .then(() => loadStatus())
      .catch(() => setStatus("Start failed"));
  };

  const handleStop = () => {
    const method = mode === "usbip" ? "stop_usbip" : "stop_sharing";
    serverAPI.callPluginMethod(method, {})
      .then(() => loadStatus())
      .catch(() => setStatus("Stop failed"));
  };

  const toggleMode = () => {
    if (!isRunning) {
      setMode(mode === "evdev" ? "usbip" : "evdev");
    }
  };

  return (
    <PanelSection title="Controller Sharing">
      <PanelSectionRow>
        <div>Mode: {mode === "usbip" ? "USB/IP" : "Network (evdev)"}</div>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={toggleMode}
          disabled={isRunning}
        >
          Switch to {mode === "usbip" ? "Network" : "USB/IP"}
        </ButtonItem>
      </PanelSectionRow>
      <PanelSectionRow>
        <div>Status: {status}</div>
      </PanelSectionRow>
      {ip && (
        <PanelSectionRow>
          <div>Deck IP: {ip}</div>
        </PanelSectionRow>
      )}
      {mode === "usbip" && usbipInfo && (
        <PanelSectionRow>
          <div style={{fontSize: "0.9em", color: "#aaa"}}>
            Bus ID: {usbipInfo}
          </div>
        </PanelSectionRow>
      )}
      {clientIp && mode === "evdev" && (
        <PanelSectionRow>
          <div>Client: {clientIp}</div>
        </PanelSectionRow>
      )}
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={isRunning ? handleStop : handleStart}
        >
          {isRunning ? "Stop Sharing" : "Start Sharing"}
        </ButtonItem>
      </PanelSectionRow>
      {mode === "usbip" && !isRunning && (
        <PanelSectionRow>
          <div style={{fontSize: "0.85em", color: "#888", marginTop: "10px"}}>
            USB/IP: Full controller with trackpads. PC must run: sudo usbip attach -r {ip} -b [busid]
          </div>
        </PanelSectionRow>
      )}
    </PanelSection>
  );
};

export default definePlugin((serverAPI: ServerAPI) => {
  return {
    title: <div className={staticClasses.Title}>Deck Controller</div>,
    content: <Content serverAPI={serverAPI} />,
    icon: <FaGamepad />,
  };
});
