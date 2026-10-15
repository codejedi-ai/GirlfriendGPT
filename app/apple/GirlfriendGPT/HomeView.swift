import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                hero
                featured
                channelRow
                howItRuns
            }
            .padding(24)
            .frame(maxWidth: 980, alignment: .leading)
            .frame(maxWidth: .infinity)
        }
        .rootScreen()
        .navigationTitle("Home")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }

    private var hero: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle()
                    .fill(Theme.cyan)
                    .frame(width: 7, height: 7)
                Text("GIRLFRIENDGPT")
                    .font(Theme.caption)
                    .tracking(2.2)
                    .foregroundStyle(Theme.cyan)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .background(Theme.cyan.opacity(0.08))
            .overlay(Capsule().stroke(Theme.cyan.opacity(0.28), lineWidth: 1))
            .clipShape(Capsule())

            VStack(alignment: .leading, spacing: 0) {
                Text("WHERE HUMANS")
                    .font(.system(size: 34, weight: .bold))
                    .tracking(0.6)
                Text("MEET AI")
                    .font(.system(size: 34, weight: .bold))
                    .tracking(0.6)
                    .foregroundStyle(Theme.pink)
            }
            .foregroundStyle(Theme.ink)

            Text("Local companions you can talk and text with. Voice stays in a LiveKit room on \(DeviceCopy.machine). Models stay on Ollama and Speaches.")
                .font(Theme.body)
                .foregroundStyle(Theme.muted)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: 520, alignment: .leading)

            ViewThatFits(in: .horizontal) {
                HStack(spacing: 12) {
                    enterDiscover
                    explore
                }
                VStack(spacing: 12) {
                    enterDiscover
                    explore
                }
            }
            .frame(maxWidth: 460)
        }
    }

    private var enterDiscover: some View {
        PrimaryButton(title: "START MATCHING", systemImage: "heart.fill") {
            model.section = .discover
        }
    }

    private var explore: some View {
        GhostButton(title: "EXPLORE PROFILES", systemImage: "sparkles") {
            model.section = .discover
        }
    }

    private var channelRow: some View {
        ViewThatFits(in: .horizontal) {
            HStack(alignment: .top, spacing: 14) {
                channelCard(
                    title: "Voice room",
                    copy: "Lena joins a local LiveKit room. You talk. Speech and replies stay on this machine.",
                    tint: Theme.cyan
                )
                channelCard(
                    title: "Text companion",
                    copy: "Nia continues the conversation in text after a voice handoff.",
                    tint: Theme.pink
                )
            }
            VStack(spacing: 14) {
                channelCard(
                    title: "Voice room",
                    copy: "Lena joins a local LiveKit room. You talk. Speech and replies stay on this machine.",
                    tint: Theme.cyan
                )
                channelCard(
                    title: "Text companion",
                    copy: "Nia continues the conversation in text after a voice handoff.",
                    tint: Theme.pink
                )
            }
        }
    }

    private func channelCard(title: String, copy: String, tint: Color) -> some View {
        GlassPanel(accent: tint) {
            VStack(alignment: .leading, spacing: 10) {
                Capsule()
                    .fill(tint)
                    .frame(width: 36, height: 3)
                Text(title)
                    .font(.system(size: 18, weight: .bold))
                Text(copy)
                    .font(.system(size: 14))
                    .foregroundStyle(Theme.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var featured: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("COMPANIONS")
                .font(Theme.caption)
                .tracking(2)
                .foregroundStyle(Theme.faint)
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 280), spacing: 14)], spacing: 14) {
                ForEach(Companion.catalog) { companion in
                    NavigationLink(value: AppRoute.companion(companion.id)) {
                        CompanionCard(companion: companion)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private var howItRuns: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: 12) {
                Text("ON THIS MAC")
                    .font(Theme.caption)
                    .tracking(2)
                    .foregroundStyle(Theme.cyan)
                stackLine("LiveKit", "The room. iPhone and Mac join the same local call.")
                stackLine("Ollama", "The language model, on localhost.")
                stackLine("Speaches", "Speech in and speech out, on localhost.")
                stackLine("Silero", "Hears when you start and stop talking.")
            }
        }
    }

    private func stackLine(_ name: String, _ detail: String) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 12) {
            Text(name)
                .font(.system(size: 14, weight: .semibold))
                .frame(width: 88, alignment: .leading)
                .foregroundStyle(Theme.ink)
            Text(detail)
                .font(.system(size: 14))
                .foregroundStyle(Theme.muted)
        }
    }
}
