import SwiftUI
#if os(macOS)
import AppKit
import ObjectiveC
#endif

@main
struct GirlfriendGPTApp: App {
    #if os(macOS)
    init() { NSWindow.pinOntoThisDesktop() }
    #endif

    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(model)
                #if os(macOS)
                .background(MacWindowOnThisDesktop())
                #endif
        }
        #if os(macOS)
        .defaultSize(width: 1120, height: 760)
        #endif
    }
}

#if os(macOS)
extension NSWindow {
    /// Chrome is occupying a fullscreen space. A normal window opens on another
    /// desktop and disappears as soon as focus leaves. Mark every window before
    /// it is ordered on so it stays on the space in front of Darcy.
    static func pinOntoThisDesktop() {
        let behavior: NSWindow.CollectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        let cls: AnyClass = NSWindow.self
        for sel in [#selector(NSWindow.orderFront(_:)), #selector(NSWindow.makeKeyAndOrderFront(_:))] {
            guard let method = class_getInstanceMethod(cls, sel) else { continue }
            let original = method_getImplementation(method)
            typealias Order = @convention(c) (AnyObject, Selector, Any?) -> Void
            let call = unsafeBitCast(original, to: Order.self)
            let block: @convention(block) (AnyObject, Any?) -> Void = { object, sender in
                (object as? NSWindow)?.collectionBehavior.formUnion(behavior)
                call(object, sel, sender)
            }
            method_setImplementation(method, imp_implementationWithBlock(block))
        }
    }
}

/// Keep the window on the desktop Darcy is looking at. A previous fullscreen
/// session left the app assigned to another Space, so a normal launch opened
/// off-screen.
private struct MacWindowOnThisDesktop: NSViewRepresentable {
    func makeNSView(context: Context) -> NSView {
        let view = NSView(frame: .zero)
        DispatchQueue.main.async { Self.pin(view) }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        DispatchQueue.main.async { Self.pin(nsView) }
    }

    private static var didPin = false

    private static func pin(_ view: NSView) {
        guard let window = view.window else { return }
        window.level = .floating
        window.collectionBehavior.formUnion([.canJoinAllSpaces, .fullScreenAuxiliary])
        guard !didPin else { return }
        didPin = true
        if window.frame.origin.x < 0 {
            window.setFrame(NSRect(x: 196, y: 122, width: 1120, height: 760), display: true)
        }
        window.orderFrontRegardless()
        NSApp.activate(ignoringOtherApps: true)
        Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in
            window.level = .floating
            window.collectionBehavior.formUnion([.canJoinAllSpaces, .fullScreenAuxiliary])
            if window.frame.origin.x < 40 {
                window.setFrame(NSRect(x: 196, y: 122, width: 1120, height: 760), display: true)
            }
            window.orderFrontRegardless()
        }
    }
}
#endif
