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
  const [isRunning, setIsRunning] = useState(false);

  const loadStatus = () => {
    serverAPI.callPluginMethod("get_status", {})
      .then((res: any) => {
        if (res?.success && res?.result) {
          setIsRunning(res.result.running || false);
          setIp(res.result.deck_ip || "");
          setStatus(res.result.running ? "Running" : "Stopped");
        }
      })
      .catch(() => setStatus("Error"));
  };

  useEffect(() => { loadStatus(); }, []);

  const handleStart = () => {
    serverAPI.callPluginMethod("start_sharing", { port: 9090 })
      .then(() => loadStatus())
      .catch(() => setStatus("Start failed"));
  };

  const handleStop = () => {
    serverAPI.callPluginMethod("stop_sharing", {})
      .then(() => loadStatus())
      .catch(() => setStatus("Stop failed"));
  };

  return (
    <PanelSection title="Controller Sharing">
      <PanelSectionRow>
        <div>Status: {status}</div>
      </PanelSectionRow>
      {!isRunning && ip && (
        <PanelSectionRow>
          <div>Deck IP: {ip}</div>
        </PanelSectionRow>
      )}
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={isRunning ? handleStop : handleStart}
        >
          {isRunning ? "Stop" : "Start"}
        </ButtonItem>
      </PanelSectionRow>
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
