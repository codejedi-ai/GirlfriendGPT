import SwiftUI

struct MyProfileView: View {
    @EnvironmentObject private var model: AppModel
    @State private var newInterest = ""

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                VStack(alignment: .leading, spacing: 6) {
                    Text(model.profile.displayName.isEmpty ? "YOU" : model.profile.displayName.uppercased())
                        .font(.system(size: 28, weight: .bold))
                        .tracking(1)
                    Text("Saved on this device. The name shows on your side of a conversation.")
                        .font(Theme.body)
                        .foregroundStyle(Theme.muted)
                }

                GlassPanel {
                    VStack(alignment: .leading, spacing: 14) {
                        field("Name", text: Binding(
                            get: { model.profile.displayName },
                            set: { model.profile.displayName = $0 }
                        ))
                        field("Location", text: Binding(
                            get: { model.profile.location },
                            set: { model.profile.location = $0 }
                        ))
                        VStack(alignment: .leading, spacing: 6) {
                            Text("BIO")
                                .font(.system(size: 10, weight: .bold))
                                .tracking(1.4)
                                .foregroundStyle(Theme.faint)
                            TextField("A short note", text: Binding(
                                get: { model.profile.bio },
                                set: { model.profile.bio = $0 }
                            ), axis: .vertical)
                            .lineLimit(3...6)
                            .textFieldStyle(.plain)
                            .padding(12)
                            .background(Color.white.opacity(0.04))
                            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                        }
                        VStack(alignment: .leading, spacing: 6) {
                            Text("LOOKING FOR")
                                .font(.system(size: 10, weight: .bold))
                                .tracking(1.4)
                                .foregroundStyle(Theme.faint)
                            Picker("Looking for", selection: Binding(
                                get: { model.profile.lookingFor },
                                set: { model.profile.lookingFor = $0 }
                            )) {
                                ForEach(UserProfile.lookingForOptions, id: \.self) { option in
                                    Text(option).tag(option)
                                }
                            }
                            .pickerStyle(.menu)
                            .tint(Theme.cyan)
                        }
                    }
                }

                GlassPanel(accent: Theme.pink) {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("INTERESTS")
                            .font(.system(size: 10, weight: .bold))
                            .tracking(1.4)
                            .foregroundStyle(Theme.faint)
                        FlowTags(tags: model.profile.interests) { tag in
                            model.profile.interests.removeAll { $0 == tag }
                        }
                        HStack(spacing: 8) {
                            TextField("Add an interest", text: $newInterest)
                                .textFieldStyle(.plain)
                                .padding(12)
                                .background(Color.white.opacity(0.04))
                                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                                .onSubmit(addInterest)
                            Button(action: addInterest) {
                                Image(systemName: "plus")
                                    .font(.system(size: 14, weight: .bold))
                                    .foregroundStyle(.black)
                                    .frame(width: 40, height: 40)
                                    .background(Theme.cyan)
                                    .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                PrimaryButton(title: model.savedBanner ? "SAVED" : "SAVE PROFILE", systemImage: "checkmark") {
                    model.saveProfile()
                }
                .frame(maxWidth: 280)

                if model.savedBanner {
                    Text("Saved on this device.")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundStyle(Theme.live)
                }
            }
            .padding(24)
            .frame(maxWidth: 680)
            .frame(maxWidth: .infinity)
        }
        .rootScreen()
        .navigationTitle("My Profile")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .onChange(of: model.profile) { _, _ in
            model.savedBanner = false
        }
    }

    private func field(_ title: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title.uppercased())
                .font(.system(size: 10, weight: .bold))
                .tracking(1.4)
                .foregroundStyle(Theme.faint)
            TextField(title, text: text)
                .textFieldStyle(.plain)
                .padding(12)
                .background(Color.white.opacity(0.04))
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        }
    }

    private func addInterest() {
        let value = newInterest.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty, !model.profile.interests.contains(value) else { return }
        model.profile.interests.append(value)
        newInterest = ""
    }
}

private struct FlowTags: View {
    let tags: [String]
    let remove: (String) -> Void

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(tags, id: \.self) { tag in
                    Button {
                        remove(tag)
                    } label: {
                        HStack(spacing: 6) {
                            Text(tag)
                            Image(systemName: "xmark")
                                .font(.system(size: 9, weight: .bold))
                        }
                        .font(.system(size: 12, weight: .medium))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .foregroundStyle(Theme.ink)
                        .background(Theme.pink.opacity(0.16))
                        .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}
