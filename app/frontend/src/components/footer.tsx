import { Link } from "react-router-dom";
import { HiSparkles } from "react-icons/hi2";
import { FaHeart } from "react-icons/fa";
import { PRODUCT_FOOTER_CREDIT, PRODUCT_NAME } from "@/config/brand";

export function Footer() {
  return (
    <footer className="border-t border-[#00ffff]/8 bg-[#050714]/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
          <div>
            <Link to="/" className="flex items-center gap-3 mb-4 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00ffff] to-[#0099cc] flex items-center justify-center">
                <HiSparkles className="text-black text-sm" />
              </div>
              <span className="font-display text-sm font-bold text-white tracking-wider">{PRODUCT_NAME}</span>
            </Link>
            <p className="text-gray-500 text-sm font-body leading-relaxed">
              Local AI companions. Voice and text chat with personas you run yourself.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold text-gray-400 tracking-wider mb-4 uppercase">Experience</h4>
            <div className="space-y-2.5">
              <Link to="/discover" className="block text-sm text-gray-500 hover:text-[#00ffff] transition-colors font-body">Discover</Link>
              <span className="block text-sm text-gray-600 font-body">Voice talk</span>
              <span className="block text-sm text-gray-600 font-body">Text chat</span>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold text-gray-400 tracking-wider mb-4 uppercase">Company</h4>
            <div className="space-y-2.5">
              <span className="block text-sm text-gray-600 font-body">About</span>
              <span className="block text-sm text-gray-600 font-body">Careers</span>
              <span className="block text-sm text-gray-600 font-body">Press</span>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold text-gray-400 tracking-wider mb-4 uppercase">Legal</h4>
            <div className="space-y-2.5">
              <span className="block text-sm text-gray-600 font-body">Privacy Policy</span>
              <span className="block text-sm text-gray-600 font-body">Terms of Service</span>
              <span className="block text-sm text-gray-600 font-body">Safety</span>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-gray-800/50 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-600 font-body">
            {PRODUCT_FOOTER_CREDIT}
          </p>
          <p className="flex items-center gap-1.5 text-xs text-gray-600 font-body">
            Made with <FaHeart className="text-[#ff0080] text-[10px]" /> for humans & AI
          </p>
        </div>
      </div>
    </footer>
  );
}
