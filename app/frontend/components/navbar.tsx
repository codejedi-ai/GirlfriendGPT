import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FaHeart, FaBars, FaTimes, FaSignOutAlt, FaUserCircle } from "react-icons/fa";
import { HiSparkles } from "react-icons/hi2";
import { useAuth } from "@/contexts/AuthContext";
import { PRODUCT_NAME, PRODUCT_STACK_LABEL } from "@/config/brand";

const navLinks = [
  { path: "/", label: "HOME" },
  { path: "/discover", label: "DISCOVER" },
];

export function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const handleSignOut = async () => {
    await signOut();
    navigate("/");
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#050714]/95 backdrop-blur-xl border-b border-[#00ffff]/10 shadow-lg shadow-[#050714]/50"
          : "bg-transparent"
      }`}
    >
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="relative w-9 h-9 rounded-lg bg-gradient-to-br from-[#00ffff] to-[#0099cc] flex items-center justify-center group-hover:shadow-lg group-hover:shadow-[#00ffff]/20 transition-all">
              <HiSparkles className="text-black text-lg" />
            </div>
            <div className="flex flex-col">
                <span className="font-display text-base font-bold text-white tracking-wider leading-none">
                  {PRODUCT_NAME}
                </span>
              <span className="text-[9px] text-[#00ffff]/60 tracking-[0.2em] font-body">{PRODUCT_STACK_LABEL}</span>
            </div>
          </Link>

          <div className="hidden sm:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`relative px-4 py-2 text-xs font-medium tracking-wider transition-all duration-300 font-display rounded-lg ${
                    isActive
                      ? "text-[#00ffff]"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="nav-active"
                      className="absolute inset-0 bg-[#00ffff]/8 border border-[#00ffff]/20 rounded-lg"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10">{link.label}</span>
                </Link>
              );
            })}
          </div>

          <div className="hidden sm:flex items-center gap-3">
            {user ? (
              <>
                <Link
                  to="/my-profile"
                  className={`flex items-center gap-2 px-4 py-2 border font-bold text-xs tracking-wider rounded-lg transition-all duration-300 font-display ${
                    location.pathname === "/my-profile"
                      ? "border-[#00ffff]/50 text-[#00ffff] bg-[#00ffff]/8"
                      : "border-[#00ffff]/30 text-[#00ffff] hover:bg-[#00ffff]/10 hover:border-[#00ffff]"
                  }`}
                >
                  <FaUserCircle className="text-sm" />
                  PROFILE
                </Link>
                <button
                  onClick={handleSignOut}
                  className="flex items-center gap-2 px-4 py-2 border border-gray-600/50 text-gray-400 hover:text-white hover:border-gray-400 font-bold text-xs tracking-wider rounded-lg transition-all duration-300 font-display"
                >
                  <FaSignOutAlt className="text-[10px]" />
                  SIGN OUT
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="flex items-center gap-2 px-5 py-2 border border-[#00ffff]/30 text-[#00ffff] hover:bg-[#00ffff]/10 hover:border-[#00ffff] font-bold text-xs tracking-wider rounded-lg transition-all duration-300 font-display"
                >
                  SIGN IN
                </Link>
                <Link
                  to="/signup"
                  className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-[#ff0080] to-[#cc0066] text-white font-bold text-xs tracking-wider rounded-lg transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-[#ff0080]/20 font-display"
                >
                  <FaHeart className="text-[10px]" />
                  SIGN UP
                </Link>
              </>
            )}
          </div>

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="sm:hidden p-2 text-gray-400 hover:text-white transition-colors"
          >
            {mobileOpen ? <FaTimes className="text-lg" /> : <FaBars className="text-lg" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="sm:hidden bg-[#050714]/98 backdrop-blur-xl border-b border-[#00ffff]/10 overflow-hidden"
          >
            <div className="px-4 py-4 space-y-1">
              {navLinks.map((link) => {
                const isActive = location.pathname === link.path;
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={`block px-4 py-3 text-sm font-medium tracking-wider rounded-lg transition-all font-display ${
                      isActive
                        ? "text-[#00ffff] bg-[#00ffff]/8"
                        : "text-gray-400 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}

              {user ? (
                <>
                  <Link
                    to="/my-profile"
                    className={`flex items-center justify-center gap-2 mt-2 px-5 py-3 border font-bold text-xs tracking-wider rounded-lg font-display transition-all ${
                      location.pathname === "/my-profile"
                        ? "border-[#00ffff]/50 text-[#00ffff] bg-[#00ffff]/8"
                        : "border-[#00ffff]/30 text-[#00ffff] hover:bg-[#00ffff]/10"
                    }`}
                  >
                    <FaUserCircle className="text-sm" />
                    MY PROFILE
                  </Link>
                  <button
                    onClick={handleSignOut}
                    className="flex items-center justify-center gap-2 w-full mt-2 px-5 py-3 border border-gray-600/50 text-gray-400 hover:text-white font-bold text-xs tracking-wider rounded-lg font-display transition-all"
                  >
                    <FaSignOutAlt className="text-[10px]" />
                    SIGN OUT
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="flex items-center justify-center gap-2 mt-3 px-5 py-3 border border-[#00ffff]/30 text-[#00ffff] font-bold text-xs tracking-wider rounded-lg font-display"
                  >
                    SIGN IN
                  </Link>
                  <Link
                    to="/signup"
                    className="flex items-center justify-center gap-2 mt-2 px-5 py-3 bg-gradient-to-r from-[#ff0080] to-[#cc0066] text-white font-bold text-xs tracking-wider rounded-lg font-display"
                  >
                    <FaHeart className="text-[10px]" />
                    SIGN UP
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
