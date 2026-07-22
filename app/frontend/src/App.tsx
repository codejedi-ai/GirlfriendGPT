import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";
import { Layout } from "@/Layout";
import { AuthenticatedLayout } from "@/AuthenticatedLayout";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import LandingPage from "@/pages/LandingPage";
import DiscoverPage from "@/pages/DiscoverPage";
import ProfileDetailPage from "@/pages/ProfileDetailPage";
import LoginPage from "@/pages/LoginPage";
import SignUpPage from "@/pages/SignUpPage";
import MyProfilePage from "@/pages/MyProfilePage";
import SettingsPage from "@/pages/SettingsPage";
import TalkPage from "@/pages/TalkPage";
import cyberpunkTheme from "@/theme/theme";

/** If already signed in, skip landing auth screens. */
function RedirectIfAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/discover" replace />;
  return <>{children}</>;
}

/**
 * Default UI = GirlfriendGPT (Landing + Discover shell).
 * Voice talk fills the main pane beside the sidebar (not a modal overlay).
 */
function App() {
  return (
    <ThemeProvider theme={cyberpunkTheme}>
      <CssBaseline />
      <Router>
        <AuthProvider>
          <Routes>
            <Route element={<RedirectIfAuth><Layout /></RedirectIfAuth>}>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignUpPage />} />
            </Route>

            <Route element={<AuthenticatedLayout />}>
              <Route path="/discover" element={<DiscoverPage />} />
              <Route path="/my-profile" element={<MyProfilePage />} />
              <Route path="/profile/:id" element={<ProfileDetailPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>

            <Route path="/talk" element={<TalkPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
