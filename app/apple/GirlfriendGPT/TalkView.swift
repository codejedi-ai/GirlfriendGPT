import SwiftUI

struct TalkLine: Identifiable, Equatable {
    enum Who { case user, companion }
    let id: String
    var who: Who
    var text: String
}

struct TalkView: View {
    let companion: Companion
    @EnvironmentObject private var model: AppModel
    @StateObject private var session = LocalRoomSession()
    @State private var lines: [TalkLine] = []
    @State private var draft = ""

    private var voice: Bool { companion.channel == .voice }
    private var live: Bool { voice ? session.live : textLive }
    @State private var textLive = false

    private var shownLines: [TalkLine] { voice ? session.lines : lines }
    private var status: String {
        if voice { return session.status }
        return textLive ? "Text thread on this device" : "Ready"
    }
    private var meterLevel: Double { voice ? session.level : 0 }
    private var meterLive: Bool { voice ? session.micLive : false }

    var body: some View {
        VStack(spacing: 0) {
            header
            transcript
            composer
        }
        .background(StageBackground())
        .navigationTitle(companion.channel == .voice ? "Talk" : "Text")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .onDisappear {
            if voice { session.stop() }
        }
    }

    private var header: some View {
        HStack(spacing: 12) {
            VoiceRing(level: meterLevel, live: live, tint: companion.channel.tint)
            VStack(alignment: .leading, spacing: 2) {
                Text(companion.name)
                    .font(.system(size: 16, weight: .bold))
                    .tracking(0.4)
                Text(status)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(session.failed ? Color.red : (live ? Theme.live : Theme.muted))
            }
            Spacer()
            ChannelPill(channel: companion.channel)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 14)
    }

    private var transcript: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 10) {
                    if shownLines.isEmpty {
                        Text(voice
                             ? "Start talking. This joins the LiveKit room on this Mac."
                             : "Start the thread. Nia greets you, then you write back.")
                            .font(Theme.body)
                            .foregroundStyle(Theme.faint)
                            .frame(maxWidth: .infinity)
                            .padding(.top, 48)
                            .multilineTextAlignment(.center)
                    }
                    ForEach(shownLines) { line in
                        bubble(line)
                            .id(line.id)
                    }
                }
                .padding(20)
                .frame(maxWidth: 680)
                .frame(maxWidth: .infinity)
            }
            .onChange(of: shownLines) { _, updated in
                if let last = updated.last {
                    withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                }
            }
        }
    }

    private func bubble(_ line: TalkLine) -> some View {
        let mine = line.who == .user
        return HStack {
            if mine { Spacer(minLength: 48) }
            VStack(alignment: .leading, spacing: 4) {
                Text(mine ? (model.profile.displayName.isEmpty ? "You" : model.profile.displayName) : companion.name)
                    .font(.system(size: 10, weight: .bold))
                    .tracking(1.1)
                    .foregroundStyle(mine ? Theme.pink : Theme.cyan)
                Text(line.text)
                    .font(.system(size: 15))
                    .foregroundStyle(Theme.ink)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(12)
            .background((mine ? Theme.pink : Theme.cyan).opacity(0.12))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke((mine ? Theme.pink : Theme.cyan).opacity(0.35), lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            if !mine { Spacer(minLength: 48) }
        }
    }

    private var composer: some View {
        VStack(spacing: 12) {
            if companion.channel == .voice {
                HStack(spacing: 8) {
                    Text(meterLive ? "MIC" : "OFF")
                        .font(.system(size: 10, weight: .bold))
                        .tracking(1.2)
                        .foregroundStyle(Theme.faint)
                        .frame(width: 32, alignment: .trailing)
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Capsule().fill(Color.white.opacity(0.08))
                            Capsule()
                                .fill(
                                    LinearGradient(
                                        colors: [Theme.cyan, Theme.pink],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .frame(width: max(6, geo.size.width * CGFloat(meterLevel)))
                        }
                    }
                    .frame(height: 6)
                }
            } else {
                HStack(spacing: 8) {
                    TextField("Write to \(companion.name)", text: $draft)
                        .textFieldStyle(.plain)
                        .padding(12)
                        .background(Theme.panel)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .stroke(Theme.pink.opacity(0.3), lineWidth: 1)
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                        .onSubmit(sendDraft)
                    Button(action: sendDraft) {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 28))
                            .foregroundStyle(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? Theme.faint : Theme.pink)
                    }
                    .buttonStyle(.plain)
                    .disabled(!live || draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }

            if live {
                GhostButton(title: "END", systemImage: "phone.down.fill", tint: .red, action: end)
            } else {
                PrimaryButton(
                    title: session.busy ? "CONNECTING…" : (voice ? "START TALKING" : "START THREAD"),
                    systemImage: voice ? "phone.fill" : "text.bubble.fill",
                    fill: LinearGradient(
                        colors: voice ? [Theme.cyan, Theme.cyanDeep] : [Theme.pink, Theme.pinkDeep],
                        startPoint: .leading,
                        endPoint: .trailing
                    ),
                    foreground: voice ? .black : .white,
                    action: start
                )
                .disabled(session.busy)
                .opacity(session.busy ? 0.55 : 1)
            }
        }
        .padding(16)
        .background(Theme.background.opacity(0.92))
    }

    private func start() {
        if voice {
            session.start(companion: companion, callerName: model.profile.displayName)
        } else {
            textLive = true
            lines = [TalkLine(id: "greeting", who: .companion, text: companion.greeting)]
        }
    }

    private func end() {
        if voice {
            session.stop()
        } else {
            textLive = false
            lines = []
        }
    }

    private func sendDraft() {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard textLive, !text.isEmpty else { return }
        lines.append(TalkLine(id: UUID().uuidString, who: .user, text: text))
        draft = ""
    }
}

struct VoiceRing: View {
    var level: Double
    var live: Bool
    var tint: Color

    var body: some View {
        ZStack {
            Circle()
                .stroke(tint.opacity(0.25), lineWidth: 2)
                .frame(width: 46, height: 46)
            Circle()
                .stroke(tint.opacity(live ? 0.9 : 0.25), lineWidth: 2)
                .frame(width: 46 + CGFloat(level) * 18, height: 46 + CGFloat(level) * 18)
            Image(systemName: live ? "waveform" : "waveform.slash")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(tint)
        }
        .frame(width: 68, height: 68)
        .animation(live ? .easeOut(duration: 0.12) : .default, value: level)
    }
}

