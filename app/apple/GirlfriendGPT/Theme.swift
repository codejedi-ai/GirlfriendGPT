import SwiftUI

enum Theme {
    static let background = Color(red: 0.020, green: 0.027, blue: 0.078)
    static let panel = Color(red: 0.039, green: 0.043, blue: 0.102)
    static let cyan = Color(red: 0.0, green: 1.0, blue: 1.0)
    static let cyanDeep = Color(red: 0.0, green: 0.60, blue: 0.80)
    static let pink = Color(red: 1.0, green: 0.0, blue: 0.502)
    static let pinkDeep = Color(red: 0.80, green: 0.0, blue: 0.40)
    static let live = Color(red: 0.0, green: 1.0, blue: 0.533)
    static let ink = Color.white
    static let muted = Color.white.opacity(0.62)
    static let faint = Color.white.opacity(0.38)

    static let display = Font.system(size: 34, weight: .bold)
    static let title = Font.system(size: 22, weight: .bold)
    static let body = Font.system(size: 15, weight: .regular)
    static let caption = Font.system(size: 11, weight: .semibold)
}

struct StageBackground: View {
    var body: some View {
        ZStack {
            Theme.background
            RadialGradient(
                colors: [Theme.cyan.opacity(0.16), .clear],
                center: .topLeading,
                startRadius: 10,
                endRadius: 460
            )
            RadialGradient(
                colors: [Theme.pink.opacity(0.12), .clear],
                center: .bottomTrailing,
                startRadius: 10,
                endRadius: 520
            )
            Canvas { context, size in
                let step: CGFloat = 36
                var path = Path()
                var x: CGFloat = 0
                while x <= size.width {
                    path.move(to: CGPoint(x: x, y: 0))
                    path.addLine(to: CGPoint(x: x, y: size.height))
                    x += step
                }
                var y: CGFloat = 0
                while y <= size.height {
                    path.move(to: CGPoint(x: 0, y: y))
                    path.addLine(to: CGPoint(x: size.width, y: y))
                    y += step
                }
                context.stroke(path, with: .color(Theme.cyan.opacity(0.045)), lineWidth: 1)
            }
        }
        .ignoresSafeArea()
    }
}

struct GlassPanel<Content: View>: View {
    var accent: Color
    var content: Content

    init(accent: Color = Theme.cyan, @ViewBuilder content: () -> Content) {
        self.accent = accent
        self.content = content()
    }

    var body: some View {
        content
            .padding(18)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.panel.opacity(0.88))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(accent.opacity(0.28), lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

struct ChannelPill: View {
    let channel: Companion.Channel

    var body: some View {
        Text(channel.label.uppercased())
            .font(Theme.caption)
            .tracking(1.4)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(channel.tint.opacity(0.16))
            .foregroundStyle(channel.tint)
            .overlay(
                Capsule().stroke(channel.tint.opacity(0.45), lineWidth: 1)
            )
            .clipShape(Capsule())
    }
}

struct PrimaryButton: View {
    let title: String
    let systemImage: String
    var fill: LinearGradient = LinearGradient(
        colors: [Theme.cyan, Theme.cyanDeep],
        startPoint: .leading,
        endPoint: .trailing
    )
    var foreground: Color = .black
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Label(title, systemImage: systemImage)
                .font(.system(size: 13, weight: .bold))
                .tracking(1.1)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(fill)
                .foregroundStyle(foreground)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

struct GhostButton: View {
    let title: String
    let systemImage: String
    var tint: Color = Theme.pink
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Label(title, systemImage: systemImage)
                .font(.system(size: 13, weight: .bold))
                .tracking(1.1)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .foregroundStyle(tint)
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(tint.opacity(0.55), lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
    }
}

extension View {
    /// Root screens draw their own titles. On iPhone the navigation bar would
    /// stack a second title on top of that, so it stays hidden there.
    func rootScreen() -> some View {
        self
            .background(StageBackground())
            .contentMargins(.bottom, 36, for: .scrollContent)
            #if os(iOS)
            .toolbar(.hidden, for: .navigationBar)
            #endif
    }
}

enum DeviceCopy {
    static var machine: String {
        #if os(macOS)
        "this Mac"
        #else
        "this iPhone"
        #endif
    }
}

struct BrandMark: View {
    var compact = false

    var body: some View {
        HStack(spacing: 10) {
            ZStack {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [Theme.cyan, Theme.cyanDeep],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                Image(systemName: "sparkles")
                    .font(.system(size: compact ? 14 : 16, weight: .bold))
                    .foregroundStyle(.black)
            }
            .frame(width: compact ? 28 : 36, height: compact ? 28 : 36)

            if !compact {
                VStack(alignment: .leading, spacing: 1) {
                    Text("GirlfriendGPT")
                        .font(.system(size: 13, weight: .bold))
                        .tracking(0.6)
                        .foregroundStyle(Theme.ink)
                    Text("LOCAL")
                        .font(.system(size: 9, weight: .semibold))
                        .tracking(2.2)
                        .foregroundStyle(Theme.cyan.opacity(0.85))
                }
            }
        }
    }
}
