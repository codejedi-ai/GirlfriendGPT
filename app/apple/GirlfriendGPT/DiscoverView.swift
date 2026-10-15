import SwiftUI

struct CompanionCard: View {
    let companion: Companion

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ZStack(alignment: .topLeading) {
                LinearGradient(
                    colors: [
                        companion.channel.tint.opacity(0.35),
                        Theme.panel,
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .frame(height: 148)

                Text(companion.monogram)
                    .font(.system(size: 42, weight: .bold))
                    .tracking(2)
                    .foregroundStyle(.white.opacity(0.88))
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                    .padding(16)

                HStack {
                    ChannelPill(channel: companion.channel)
                    Spacer()
                    Text("LOCAL")
                        .font(Theme.caption)
                        .tracking(1.4)
                        .foregroundStyle(Theme.cyan)
                }
                .padding(12)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text(companion.name)
                    .font(.system(size: 18, weight: .bold))
                    .foregroundStyle(Theme.ink)
                Text(companion.summary)
                    .font(.system(size: 13))
                    .foregroundStyle(Theme.muted)
                    .lineLimit(3)
                    .fixedSize(horizontal: false, vertical: true)
                HStack(spacing: 6) {
                    ForEach(companion.interests, id: \.self) { interest in
                        Text(interest.uppercased())
                            .font(.system(size: 10, weight: .semibold))
                            .tracking(0.8)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .foregroundStyle(Theme.faint)
                            .overlay(Capsule().stroke(Color.white.opacity(0.12), lineWidth: 1))
                    }
                }
                .padding(.top, 4)
            }
            .padding(16)
        }
        .background(Theme.panel.opacity(0.92))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(companion.channel.tint.opacity(0.28), lineWidth: 1)
        )
    }
}

struct DiscoverView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("DISCOVER")
                        .font(.system(size: 28, weight: .bold))
                        .tracking(1.2)
                    Text("CONNECTIONS")
                        .font(.system(size: 28, weight: .bold))
                        .tracking(1.2)
                        .foregroundStyle(Theme.cyan)
                    Text("Local companions on this machine.")
                        .font(Theme.body)
                        .foregroundStyle(Theme.muted)
                }

                HStack(spacing: 10) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(Theme.faint)
                    TextField("Name or interest", text: $model.search)
                        .textFieldStyle(.plain)
                        .font(Theme.body)
                }
                .padding(12)
                .background(Theme.panel.opacity(0.9))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(Theme.cyan.opacity(0.2), lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                filterRow(title: "CHANNEL") {
                    filterChip("ALL", selected: model.channelFilter == nil) {
                        model.channelFilter = nil
                    }
                    filterChip("VOICE", selected: model.channelFilter == .voice, tint: Theme.cyan) {
                        model.channelFilter = .voice
                    }
                    filterChip("TEXT", selected: model.channelFilter == .text, tint: Theme.pink) {
                        model.channelFilter = .text
                    }
                }

                filterRow(title: "INTEREST") {
                    ForEach(model.interestOptions, id: \.self) { interest in
                        filterChip(interest.uppercased(), selected: model.interestFilter == interest) {
                            model.interestFilter = interest
                        }
                    }
                }

                Text("\(model.filteredCompanions.count) companion\(model.filteredCompanions.count == 1 ? "" : "s")")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Theme.faint)

                if model.filteredCompanions.isEmpty {
                    GlassPanel {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("No companions match")
                                .font(.system(size: 16, weight: .semibold))
                            Text("Clear the search, or turn voice and text back on in Settings.")
                                .font(.system(size: 13))
                                .foregroundStyle(Theme.muted)
                        }
                    }
                } else {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 280), spacing: 14)], spacing: 14) {
                        ForEach(model.filteredCompanions) { companion in
                            NavigationLink(value: AppRoute.companion(companion.id)) {
                                CompanionCard(companion: companion)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }
            .padding(24)
            .frame(maxWidth: 980)
            .frame(maxWidth: .infinity)
        }
        .rootScreen()
        .navigationTitle("Discover")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }

    private func filterRow(title: String, @ViewBuilder chips: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 10, weight: .bold))
                .tracking(1.6)
                .foregroundStyle(Theme.faint)
            LazyVGrid(
                columns: [GridItem(.adaptive(minimum: 108), spacing: 8, alignment: .leading)],
                alignment: .leading,
                spacing: 8
            ) {
                chips()
            }
        }
    }

    private func filterChip(_ title: String, selected: Bool, tint: Color = Theme.cyan, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 11, weight: .semibold))
                .tracking(1)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .foregroundStyle(selected ? tint : Theme.faint)
                .background(selected ? tint.opacity(0.14) : Color.clear)
                .overlay(
                    Capsule().stroke(selected ? tint.opacity(0.5) : Color.white.opacity(0.12), lineWidth: 1)
                )
                .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }
}
