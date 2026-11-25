import React from "react";
import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { ToolsPage } from "./pages/ToolsPage";
import { ItemsPage } from "./pages/ItemsPage";
import { ProvidersPage } from "./pages/ProvidersPage";
import { InterestsPage } from "./pages/InterestsPage";
import { RunLogsPage } from "./pages/RunLogsPage";
import { ChatPlaygroundPage } from "./pages/ChatPlaygroundPage";

export const App: React.FC = () => {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/tools" element={<ToolsPage />} />
        <Route path="/items" element={<ItemsPage />} />
        <Route path="/providers" element={<ProvidersPage />} />
        <Route path="/interests" element={<InterestsPage />} />
        <Route path="/logs" element={<RunLogsPage />} />
        <Route path="/chat" element={<ChatPlaygroundPage />} />
      </Routes>
    </Layout>
  );
};
