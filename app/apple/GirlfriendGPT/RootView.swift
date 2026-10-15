import SwiftUI

struct RootView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        Group {
            #if os(macOS)
            MacShell()
            #else
            PhoneShell()
            #endif
        }
        .preferredColorScheme(.dark)
        .tint(Theme.cyan)
    }
}

struct AppRouteStack<Root: View>: View {
    @Binding var path: [AppRoute]
    @ViewBuilder var root: () -> Root

    var body: some View {
        NavigationStack(path: $path) {
            root()
                .navigationDestination(for: AppRoute.self) { route in
                    switch route {
                    case .companion(let id):
                        if let companion = Companion.catalog.first(where: { $0.id == id }) {
                            CompanionDetailView(companion: companion)
                        }
                    case .talk(let id):
                        if let companion = Companion.catalog.first(where: { $0.id == id }) {
                            TalkView(companion: companion)
                        }
                    }
                }
        }
    }
}

#if os(macOS)
private struct MacShell: View {
    @EnvironmentObject private var model: AppModel
    @State private var path: [AppRoute] = AppModel.launchPath(
        for: ProcessInfo.processInfo.environment["GIRLFRIENDGPT_SCREEN"]
    )
    @State private var allowPathReset = false

    var body: some View {
        NavigationSplitView {
            VStack(alignment: .leading, spacing: 0) {
                BrandMark()
                    .padding(.horizontal, 16)
                    .padding(.top, 18)
                    .padding(.bottom, 14)

                List(AppSection.allCases, selection: $model.section) { section in
                    Label(section.title, systemImage: section.symbol)
                        .tag(section)
                }
                .listStyle(.sidebar)

                Text("LOCAL")
                    .font(.system(size: 10, weight: .bold))
                    .tracking(2)
                    .foregroundStyle(Theme.faint)
                    .padding(.horizontal, 20)
                    .padding(.bottom, 16)
            }
            .navigationSplitViewColumnWidth(min: 196, ideal: 220, max: 260)
        } detail: {
            AppRouteStack(path: $path) {
                sectionRoot
            }
        }
        .background(StageBackground())
        .frame(minWidth: 960, minHeight: 640)
        .task {
            // A sidebar selection event during launch was popping the talk
            // screen. Hold the deep link long enough to start the call.
            let hold: UInt64 = path.isEmpty ? 400_000_000 : 120_000_000_000
            try? await Task.sleep(nanoseconds: hold)
            allowPathReset = true
        }
        .onChange(of: model.section) { _, _ in
            guard allowPathReset else { return }
            path.removeAll()
        }
    }

    @ViewBuilder
    private var sectionRoot: some View {
        switch model.section {
        case .home:
            HomeView()
        case .discover:
            DiscoverView()
        case .profile:
            MyProfileView()
        case .settings:
            SettingsView()
        }
    }
}
#else
private struct PhoneShell: View {
    @EnvironmentObject private var model: AppModel
    @State private var homePath: [AppRoute] = []
    @State private var discoverPath: [AppRoute] = AppModel.launchPath(
        for: ProcessInfo.processInfo.environment["GIRLFRIENDGPT_SCREEN"]
    )

    var body: some View {
        TabView(selection: $model.section) {
            AppRouteStack(path: $homePath) {
                HomeView()
            }
            .tabItem { Label("Home", systemImage: AppSection.home.symbol) }
            .tag(AppSection.home)

            AppRouteStack(path: $discoverPath) {
                DiscoverView()
            }
            .tabItem { Label("Discover", systemImage: AppSection.discover.symbol) }
            .tag(AppSection.discover)

            NavigationStack {
                MyProfileView()
            }
            .tabItem { Label("You", systemImage: AppSection.profile.symbol) }
            .tag(AppSection.profile)

            NavigationStack {
                SettingsView()
            }
            .tabItem { Label("Settings", systemImage: AppSection.settings.symbol) }
            .tag(AppSection.settings)
        }
        .toolbarBackground(Theme.background, for: .tabBar)
        .toolbarBackground(.visible, for: .tabBar)
    }
}
#endif
