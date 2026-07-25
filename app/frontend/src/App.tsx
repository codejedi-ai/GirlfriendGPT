import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";
import { Layout } from "@/Layout";
import { AuthenticatedLayout } from "@/AuthenticatedLayout";
import { VoiceTalkProvider } from "@/contexts/VoiceTalkContext";
import { AgentVoiceBridge } from "@/components/AgentVoiceBridge";
import LandingPage from "@/pages/LandingPage";
import DiscoverPage from "@/pages/DiscoverPage";
import ProfileDetailPage from "@/pages/ProfileDetailPage";
import MyProfilePage from "@/pages/MyProfilePage";
import SettingsPage from "@/pages/SettingsPage";
import TalkPage from "@/pages/TalkPage";
import cyberpunkTheme from "@/theme/theme";

/** Local GirlfriendGPT UI — no accounts, no sign-in. */
function App() {
  return (
    <ThemeProvider theme={cyberpunkTheme}>
      <CssBaseline />
      <Router>
        <VoiceTalkProvider>
          <AgentVoiceBridge />
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<LandingPage />} />
            </Route>

            <Route element={<AuthenticatedLayout />}>
              <Route path="/discover" element={<DiscoverPage />} />
              <Route path="/my-profile" element={<MyProfilePage />} />
              <Route path="/profile/:id" element={<ProfileDetailPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>

            <Route path="/talk" element={<TalkPage />} />
            <Route path="/login" element={<Navigate to="/discover" replace />} />
            <Route path="/signup" element={<Navigate to="/discover" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </VoiceTalkProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
