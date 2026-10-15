import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("SETTINGS")
                        .font(.system(size: 28, weight: .bold))
                        .tracking(1.4)
                        .foregroundStyle(Theme.cyan)
                    Text("Saved on this device.")
                        .font(Theme.body)
                        .foregroundStyle(Theme.muted)
                }

                settingsGroup(title: "Notifications", symbol: "bell") {
                    toggle("Match alerts", "When a companion is ready to talk.", key: \.matchAlerts)
                    toggle("Message notifications", "When a text thread has something new.", key: \.messageNotifications)
                    toggle("Product updates", "GirlfriendGPT announcements on \(DeviceCopy.machine).", key: \.productUpdates)
                }
                settingsGroup(title: "Privacy", symbol: "lock") {
                    toggle("Show online status", "Let a companion session show you as here.", key: \.showOnline)
                    toggle("Public profile", "Keep your name available in Discover.", key: \.publicProfile)
                }
                settingsGroup(title: "Appearance", symbol: "paintbrush") {
                    toggle("Animations", "Motion on the talk ring and live marks.", key: \.animations)
                }
                settingsGroup(title: "Discovery", symbol: "eye") {
                    toggle("Show voice companions", "Lena and other voice rooms.", key: \.showVoice)
                    toggle("Show text companions", "Nia and other text threads.", key: \.showText)
                }

                Text("GirlfriendGPT · Local stack")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Theme.faint)
                    .frame(maxWidth: .infinity)
            }
            .padding(24)
            .frame(maxWidth: 680)
            .frame(maxWidth: .infinity)
        }
        .rootScreen()
        .navigationTitle("Settings")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }

    private func settingsGroup(title: String, symbol: String, @ViewBuilder rows: () -> some View) -> some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: 14) {
                Label(title.uppercased(), systemImage: symbol)
                    .font(.system(size: 11, weight: .bold))
                    .tracking(1.6)
                    .foregroundStyle(Theme.cyan)
                rows()
            }
        }
    }

    private func toggle(_ title: String, _ detail: String, key: WritableKeyPath<AppSettings, Bool>) -> some View {
        Toggle(isOn: Binding(
            get: { model.settings[keyPath: key] },
            set: { newValue in
                model.settings[keyPath: key] = newValue
                model.saveSettings()
            }
        )) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 15, weight: .medium))
                Text(detail)
                    .font(.system(size: 12))
                    .foregroundStyle(Theme.muted)
            }
        }
        .tint(Theme.cyan)
    }
}
