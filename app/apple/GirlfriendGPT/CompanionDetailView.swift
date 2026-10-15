import SwiftUI

struct CompanionDetailView: View {
    let companion: Companion

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                ZStack(alignment: .bottomLeading) {
                    LinearGradient(
                        colors: [companion.channel.tint.opacity(0.45), Theme.background],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                    .frame(height: 220)
                    .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))

                    VStack(alignment: .leading, spacing: 10) {
                        ChannelPill(channel: companion.channel)
                        Text(companion.name)
                            .font(.system(size: 32, weight: .bold))
                            .tracking(0.4)
                        Text(companion.monogram)
                            .font(.system(size: 13, weight: .semibold))
                            .tracking(3)
                            .foregroundStyle(.white.opacity(0.7))
                    }
                    .padding(22)
                }

                GlassPanel(accent: companion.channel.tint) {
                    VStack(alignment: .leading, spacing: 14) {
                        Text(companion.summary)
                            .font(Theme.body)
                            .foregroundStyle(Theme.muted)
                            .fixedSize(horizontal: false, vertical: true)

                        Text(companion.stack)
                            .font(.system(size: 12, weight: .semibold))
                            .tracking(0.4)
                            .foregroundStyle(companion.channel.tint)

                        HStack(spacing: 8) {
                            ForEach(companion.interests, id: \.self) { interest in
                                Text(interest)
                                    .font(.system(size: 12, weight: .medium))
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(Color.white.opacity(0.05))
                                    .clipShape(Capsule())
                            }
                        }

                        NavigationLink(value: AppRoute.talk(companion.id)) {
                            Label(
                                companion.channel == .voice ? "TALK" : "CONTINUE IN TEXT",
                                systemImage: companion.channel == .voice ? "phone.fill" : "text.bubble.fill"
                            )
                            .font(.system(size: 13, weight: .bold))
                            .tracking(1.1)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(
                                LinearGradient(
                                    colors: companion.channel == .voice
                                        ? [Theme.cyan, Theme.cyanDeep]
                                        : [Theme.pink, Theme.pinkDeep],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .foregroundStyle(companion.channel == .voice ? Color.black : Color.white)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding(24)
            .frame(maxWidth: 720)
            .frame(maxWidth: .infinity)
        }
        .background(StageBackground())
        .navigationTitle(companion.name)
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }
}
