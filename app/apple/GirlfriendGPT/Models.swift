import Foundation
import SwiftUI

struct Companion: Identifiable, Hashable {
    enum Channel: String, Hashable {
        case voice
        case text

        var label: String { self == .voice ? "Voice" : "Text" }
        var tint: Color { self == .voice ? Theme.cyan : Theme.pink }
        var symbol: String { self == .voice ? "waveform" : "text.bubble" }
    }

    let id: String
    let name: String
    let channel: Channel
    let summary: String
    let interests: [String]
    let greeting: String
    let stack: String

    var monogram: String {
        let parts = name.split(separator: " ")
        let letters = parts.prefix(2).compactMap { $0.first }
        return String(letters).uppercased()
    }

    static let catalog: [Companion] = [
        Companion(
            id: "e11a0000-0000-4000-8000-000000000001",
            name: "Lena Van Der Meer",
            channel: .voice,
            summary: "Warm companion on the local voice room. She stays present, and she can help you remember medication.",
            interests: ["Voice", "Care", "English"],
            greeting: "Hi! I'm Lena Van Der Meer — glad you're here. How are you feeling today?",
            stack: "LiveKit · Ollama · Speaches · Silero"
        ),
        Companion(
            id: "c11a0000-0000-4000-8000-000000000001",
            name: "Nia",
            channel: .text,
            summary: "Text companion. She picks up after a voice handoff and keeps the conversation going on this Mac.",
            interests: ["Text", "Handoffs", "Care"],
            greeting: "Hello! I'm Nia on the text channel. How are you feeling today?",
            stack: "Text companion · Ollama"
        ),
    ]
}

enum AppRoute: Hashable {
    case companion(String)
    case talk(String)
}

struct UserProfile: Codable, Equatable {
    var displayName: String
    var location: String
    var bio: String
    var lookingFor: String
    var interests: [String]

    static let empty = UserProfile(
        displayName: "Local",
        location: "On this device",
        bio: "Local GirlfriendGPT profile. No cloud account.",
        lookingFor: "Genuine connection",
        interests: ["Voice", "Text"]
    )

    static let lookingForOptions = [
        "Genuine connection",
        "Long-term relationship",
        "Something casual",
        "Friends first",
        "Someone fun",
        "My person",
    ]
}

struct AppSettings: Codable, Equatable {
    var matchAlerts = true
    var messageNotifications = true
    var productUpdates = false
    var showOnline = true
    var publicProfile = true
    var animations = true
    var showVoice = true
    var showText = true
}

enum AppSection: String, CaseIterable, Identifiable, Hashable {
    case home
    case discover
    case profile
    case settings

    var id: String { rawValue }

    var title: String {
        switch self {
        case .home: return "Home"
        case .discover: return "Discover"
        case .profile: return "My Profile"
        case .settings: return "Settings"
        }
    }

    var symbol: String {
        switch self {
        case .home: return "sparkles"
        case .discover: return "safari"
        case .profile: return "person.crop.circle"
        case .settings: return "gearshape"
        }
    }
}

@MainActor
final class AppModel: ObservableObject {
    @Published var section: AppSection = .home
    @Published var profile: UserProfile
    @Published var settings: AppSettings
    @Published var search = ""
    @Published var channelFilter: Companion.Channel?
    @Published var interestFilter = "All"
    @Published var savedBanner = false

    private let profileKey = "girlfriendgpt.profile"
    private let settingsKey = "girlfriendgpt.settings"

    init() {
        let defaults = UserDefaults.standard
        if let data = defaults.data(forKey: profileKey),
           let stored = try? JSONDecoder().decode(UserProfile.self, from: data) {
            profile = stored
        } else {
            profile = .empty
        }
        if let data = defaults.data(forKey: settingsKey),
           let stored = try? JSONDecoder().decode(AppSettings.self, from: data) {
            settings = stored
        } else {
            settings = AppSettings()
        }
        applyLaunchScreen()
    }

    var interestOptions: [String] {
        let tags = Set(Companion.catalog.flatMap(\.interests)).sorted()
        return ["All"] + tags
    }

    var filteredCompanions: [Companion] {
        Companion.catalog.filter { companion in
            if companion.channel == .voice && !settings.showVoice { return false }
            if companion.channel == .text && !settings.showText { return false }
            if let channelFilter, companion.channel != channelFilter { return false }
            if interestFilter != "All" && !companion.interests.contains(interestFilter) { return false }
            let query = search.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            if query.isEmpty { return true }
            return companion.name.lowercased().contains(query)
                || companion.summary.lowercased().contains(query)
                || companion.interests.contains { $0.lowercased().contains(query) }
        }
    }

    func saveProfile() {
        if let data = try? JSONEncoder().encode(profile) {
            UserDefaults.standard.set(data, forKey: profileKey)
        }
        savedBanner = true
    }

    func saveSettings() {
        if let data = try? JSONEncoder().encode(settings) {
            UserDefaults.standard.set(data, forKey: settingsKey)
        }
    }

    private func applyLaunchScreen() {
        switch ProcessInfo.processInfo.environment["GIRLFRIENDGPT_SCREEN"]?.lowercased() {
        case "discover", "detail", "talk":
            section = .discover
        case "profile":
            section = .profile
        case "settings":
            section = .settings
        default:
            break
        }
    }

    static func launchPath(for screen: String?) -> [AppRoute] {
        guard let lena = Companion.catalog.first else { return [] }
        switch screen?.lowercased() {
        case "detail":
            return [.companion(lena.id)]
        case "talk":
            return [.companion(lena.id), .talk(lena.id)]
        default:
            return []
        }
    }
}
