import AVFoundation
import Foundation
import LiveKit
import SwiftUI

/// Testing only. The Apple app joins the LiveKit container published on this Mac.
enum LocalTestLiveKit {
    static let tokenEndpoint = URL(string: "http://127.0.0.1:8080/api/token")!
    static let roomURL = "ws://127.0.0.1:7880"

    static var clientSessionID: String {
        let key = "girlfriendgpt.apple.client_session"
        if let existing = UserDefaults.standard.string(forKey: key), !existing.isEmpty {
            return existing
        }
        let created = "apple-\(UUID().uuidString.lowercased())"
        UserDefaults.standard.set(created, forKey: key)
        return created
    }
}

@MainActor
final class LocalRoomSession: ObservableObject {
    @Published var live = false
    @Published var busy = false
    @Published var failed = false
    @Published var micLive = false
    @Published var level: Double = 0
    @Published var status = "Ready"
    @Published var lines: [TalkLine] = []

    private var room: Room?
    private var generation = 0
    private var levelTask: Task<Void, Never>?

    func start(companion: Companion, callerName: String) {
        guard !busy, !live else { return }
        generation += 1
        let ticket = generation
        busy = true
        failed = false
        lines = []
        level = 0
        status = "Connecting to LiveKit on this Mac…"

        Task {
            do {
                try await connect(companion: companion, callerName: callerName, ticket: ticket)
            } catch {
                guard ticket == generation else { return }
                await tearDownRoom()
                failed = true
                live = false
                micLive = false
                level = 0
                status = Self.message(for: error, companion: companion)
            }
            if ticket == generation {
                busy = false
            }
        }
    }

    func stop() {
        generation += 1
        busy = false
        failed = false
        live = false
        micLive = false
        level = 0
        status = "Ended"
        Task { await tearDownRoom() }
    }

    func sendText(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard live, let room, !trimmed.isEmpty else { return }
        let id = UUID().uuidString
        lines.append(TalkLine(id: id, who: .user, text: trimmed))
        Task {
            do {
                _ = try await room.localParticipant.sendText(trimmed, for: "lk.chat")
            } catch {
                failed = true
                status = "Could not send that message."
            }
        }
    }

    private func connect(companion: Companion, callerName: String, ticket: Int) async throws {
        let token = try await Self.mintToken(agentID: companion.id, callerName: callerName)
        guard ticket == generation else { return }

        #if os(iOS)
        let audio = AVAudioSession.sharedInstance()
        try audio.setCategory(.playAndRecord, mode: .voiceChat, options: [.defaultToSpeaker, .allowBluetooth])
        try audio.setActive(true)
        #endif

        let next = Room()
        room = next
        try await next.registerTextStreamHandler(for: "lk.transcription") { [weak self] reader, identity in
            let segmentID = reader.info.attributes["lk.segment_id"] ?? reader.info.id
            let trackID = reader.info.attributes["lk.transcribed_track_id"]
            let speaker = identity.stringValue
            var text = ""
            do {
                for try await chunk in reader {
                    text += chunk
                    let snapshot = text
                    await self?.applyTranscript(
                        id: segmentID,
                        speaker: speaker,
                        trackID: trackID,
                        text: snapshot,
                        ticket: ticket
                    )
                }
            } catch {
                return
            }
        }
        guard ticket == generation else {
            await next.disconnect()
            return
        }

        try await next.connect(url: LocalTestLiveKit.roomURL, token: token.token)
        guard ticket == generation else {
            await next.disconnect()
            return
        }

        if companion.channel == .voice {
            try await next.localParticipant.setMicrophone(enabled: true)
            micLive = true
            watchLevel(ticket: ticket)
        }

        live = true
        status = "In the room on this Mac — waiting for \(companion.name)…"

        let joined = await waitForAgent(in: next, ticket: ticket)
        guard ticket == generation else { return }
        if !joined {
            throw LocalRoomError.agentMissing(companion.name)
        }
        status = companion.channel == .voice
            ? "Listening with \(companion.name)"
            : "In the room with \(companion.name)"
    }

    private func applyTranscript(
        id: String,
        speaker: String,
        trackID: String?,
        text: String,
        ticket: Int
    ) {
        guard ticket == generation else { return }
        let localIdentity = room?.localParticipant.identity?.stringValue ?? ""
        let mine = (!localIdentity.isEmpty && speaker == localIdentity) || isLocalTrack(trackID)
        let who: TalkLine.Who = mine ? .user : .companion
        if let index = lines.firstIndex(where: { $0.id == id }) {
            lines[index].text = text
            lines[index].who = who
        } else if !text.isEmpty {
            lines.append(TalkLine(id: id, who: who, text: text))
        }
    }

    private func isLocalTrack(_ trackID: String?) -> Bool {
        guard let trackID, let room else { return false }
        return room.localParticipant.trackPublications.values.contains { publication in
            publication.sid.stringValue == trackID
        }
    }

    private func waitForAgent(in room: Room, ticket: Int) async -> Bool {
        let deadline = Date().addingTimeInterval(20)
        while Date() < deadline {
            if ticket != generation { return false }
            if room.remoteParticipants.values.contains(where: { participant in
                participant.identity?.stringValue.hasPrefix("agent-") == true
            }) {
                return true
            }
            try? await Task.sleep(nanoseconds: 300_000_000)
        }
        return room.remoteParticipants.values.contains { $0.identity?.stringValue.hasPrefix("agent-") == true }
    }

    private func watchLevel(ticket: Int) {
        levelTask?.cancel()
        levelTask = Task { @MainActor in
            while !Task.isCancelled, ticket == generation {
                if let room, micLive {
                    level = min(1, Double(room.localParticipant.audioLevel) * 3)
                }
                try? await Task.sleep(nanoseconds: 80_000_000)
            }
        }
    }

    private func tearDownRoom() async {
        levelTask?.cancel()
        levelTask = nil
        let current = room
        room = nil
        await current?.disconnect()
    }

    private static func mintToken(agentID: String, callerName: String) async throws -> TokenReply {
        var request = URLRequest(url: LocalTestLiveKit.tokenEndpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15
        let body = TokenBody(
            agent_id: agentID,
            name: callerName.isEmpty ? "You" : callerName,
            client_session_id: LocalTestLiveKit.clientSessionID,
            greeting_context: "web_session"
        )
        request.httpBody = try JSONEncoder().encode(body)
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw LocalRoomError.tokenServerDown
        }
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw LocalRoomError.tokenRejected
        }
        return try JSONDecoder().decode(TokenReply.self, from: data)
    }

    private static func message(for error: Error, companion: Companion) -> String {
        if let local = error as? LocalRoomError {
            switch local {
            case .tokenServerDown:
                return "The token server is not running on this Mac (127.0.0.1:8080)."
            case .tokenRejected:
                return "This Mac refused the room token."
            case .agentMissing(let name):
                return "\(name) did not join. Start the voice worker on this Mac, then try again."
            }
        }
        let text = error.localizedDescription
        if text.localizedCaseInsensitiveContains("permission")
            || text.localizedCaseInsensitiveContains("microphone") {
            return "Microphone access is off for GirlfriendGPT."
        }
        return text
    }
}

private struct TokenBody: Encodable {
    let agent_id: String
    let name: String
    let client_session_id: String
    let greeting_context: String
}

private struct TokenReply: Decodable {
    let token: String
}

private enum LocalRoomError: Error {
    case tokenServerDown
    case tokenRejected
    case agentMissing(String)
}
