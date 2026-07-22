import { useState } from "react";
import { motion } from "framer-motion";
import { HiSparkles } from "react-icons/hi2";
import { FaBell, FaShieldAlt, FaEye, FaPalette } from "react-icons/fa";
import { PRODUCT_NAME } from "@/config/brand";

interface ToggleProps {
  enabled: boolean;
  onToggle: () => void;
}

function Toggle({ enabled, onToggle }: ToggleProps) {
  return (
    <button
      onClick={onToggle}
      className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
        enabled ? "bg-[#00ffff]/30" : "bg-gray-700"
      }`}
    >
      <div
        className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full transition-all duration-200 ${
          enabled ? "translate-x-5 bg-[#00ffff]" : "translate-x-0 bg-gray-400"
        }`}
      />
    </button>
  );
}

const sections = [
  {
    title: "Notifications",
    icon: FaBell,
    settings: [
      { key: "matchAlerts", label: "Match Alerts", description: "Get notified when someone matches with you" },
      { key: "messageNotifs", label: "Message Notifications", description: "Alerts for new messages" },
      { key: "eventUpdates", label: "Product Updates", description: `${PRODUCT_NAME} announcements` },
    ],
  },
  {
    title: "Privacy",
    icon: FaShieldAlt,
    settings: [
      { key: "showOnline", label: "Show Online Status", description: "Let others see when you're active" },
      { key: "showProfile", label: "Public Profile", description: "Allow your profile to appear in Discover" },
    ],
  },
  {
    title: "Appearance",
    icon: FaPalette,
    settings: [
      { key: "animations", label: "Animations", description: "Enable interface animations and transitions" },
    ],
  },
  {
    title: "Discovery",
    icon: FaEye,
    settings: [
      { key: "showAI", label: "Show AI Profiles", description: "Include AI companions in your matches" },
      { key: "showHumans", label: "Show Human Profiles", description: "Include human profiles in your matches" },
    ],
  },
];

export default function SettingsPage() {
  const [toggles, setToggles] = useState<Record<string, boolean>>({
    matchAlerts: true,
    messageNotifs: true,
    eventUpdates: false,
    showOnline: true,
    showProfile: true,
    animations: true,
    showAI: true,
    showHumans: true,
  });

  const toggle = (key: string) => {
    setToggles((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex-1 py-8 pb-20">
      <div className="max-w-2xl mx-auto px-4 sm:px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2 font-display tracking-wider">
            <span className="text-[#00ffff] neon-glow-cyan">SETTINGS</span>
          </h1>
          <p className="text-gray-400 font-body text-sm">
            Customize your experience
          </p>
        </motion.div>

        <div className="space-y-6">
          {sections.map((section, sIdx) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: sIdx * 0.1, duration: 0.4 }}
              className="glass-panel rounded-2xl p-6"
            >
              <div className="flex items-center gap-2 mb-5">
                <section.icon className="text-[#00ffff] text-sm" />
                <span className="text-xs text-gray-400 tracking-widest font-display font-bold">
                  {section.title.toUpperCase()}
                </span>
              </div>

              <div className="space-y-4">
                {section.settings.map((setting) => (
                  <div
                    key={setting.key}
                    className="flex items-center justify-between gap-4"
                  >
                    <div className="min-w-0">
                      <p className="text-sm text-white font-body font-medium">
                        {setting.label}
                      </p>
                      <p className="text-xs text-gray-500 font-body mt-0.5">
                        {setting.description}
                      </p>
                    </div>
                    <Toggle
                      enabled={toggles[setting.key] ?? false}
                      onToggle={() => toggle(setting.key)}
                    />
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 text-center"
        >
          <div className="flex items-center justify-center gap-2 text-gray-600 text-xs font-body">
            <HiSparkles className="text-[#00ffff]/40" />
            <span>Settings are saved locally for this demo</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
