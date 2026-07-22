import { useEffect } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { HiSparkles } from "react-icons/hi2";
import {
  FaCompass,
  FaUserCircle,
  FaCog,
  FaSignOutAlt,
  FaChevronLeft,
  FaChevronRight,
  FaBars,
  FaTimes,
} from "react-icons/fa";
import { useAuth } from "@/contexts/AuthContext";
import { PRODUCT_NAME, PRODUCT_STACK_LABEL } from "@/config/brand";

const navItems = [
  { path: "/discover", label: "Discover", icon: FaCompass },
  { path: "/my-profile", label: "My Profile", icon: FaUserCircle },
  { path: "/settings", label: "Settings", icon: FaCog },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileToggle: () => void;
}

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileToggle }: SidebarProps) {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (mobileOpen) onMobileToggle();
  }, [location.pathname]);

  const handleSignOut = async () => {
    await signOut();
    navigate("/");
  };

  const showText = !collapsed || mobileOpen;

  const sidebarContent = (
    <>
      <div className="flex items-center justify-between px-4 h-16 border-b border-[#00ffff]/8">
        <button
          onClick={onToggle}
          className="flex items-center gap-3 group min-w-0 cursor-pointer bg-transparent border-none p-0 hidden sm:flex"
        >
          <div className="relative w-9 h-9 rounded-lg bg-gradient-to-br from-[#00ffff] to-[#0099cc] flex items-center justify-center flex-shrink-0 group-hover:shadow-lg group-hover:shadow-[#00ffff]/20 transition-all">
            <HiSparkles className="text-black text-lg" />
          </div>
          {showText && (
            <div className="flex items-center gap-2 min-w-0">
              <div className="flex flex-col min-w-0">
                <span className="font-display text-sm font-bold text-white tracking-wider leading-none truncate">
                  {PRODUCT_NAME}
                </span>
                <span className="text-[9px] text-[#00ffff]/60 tracking-[0.2em] font-body">
                  {PRODUCT_STACK_LABEL}
                </span>
              </div>
              <div className="text-gray-500 group-hover:text-[#00ffff] transition-colors">
                {collapsed ? (
                  <FaChevronRight className="text-[10px]" />
                ) : (
                  <FaChevronLeft className="text-[10px]" />
                )}
              </div>
            </div>
          )}
        </button>
        <div className="flex items-center gap-3 min-w-0 sm:hidden">
          <div className="relative w-9 h-9 rounded-lg bg-gradient-to-br from-[#00ffff] to-[#0099cc] flex items-center justify-center flex-shrink-0">
            <HiSparkles className="text-black text-lg" />
          </div>
          {showText && (
            <div className="flex flex-col min-w-0">
              <span className="font-display text-sm font-bold text-white tracking-wider leading-none truncate">
                {PRODUCT_NAME}
              </span>
              <span className="text-[9px] text-[#00ffff]/60 tracking-[0.2em] font-body">
                {PRODUCT_STACK_LABEL}
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onMobileToggle}
          className="p-1.5 rounded-md text-gray-500 hover:text-[#00ffff] transition-all sm:hidden"
        >
          <FaTimes className="text-base" />
        </button>
      </div>

      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium tracking-wide transition-all duration-200 ${
                isActive
                  ? "bg-[#00ffff]/8 text-[#00ffff] border border-[#00ffff]/20"
                  : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
              } ${!showText ? "justify-center" : ""}`
            }
            title={!showText ? item.label : undefined}
          >
            <item.icon className="text-base flex-shrink-0" />
            {showText && <span className="font-body truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-[#00ffff]/8">
        <button
          onClick={handleSignOut}
          title={!showText ? "Sign Out" : undefined}
          className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-gray-500 hover:text-red-400 hover:bg-red-400/5 transition-all duration-200 ${
            !showText ? "justify-center" : ""
          }`}
        >
          <FaSignOutAlt className="text-base flex-shrink-0" />
          {showText && <span className="font-body">Sign Out</span>}
        </button>
      </div>
    </>
  );

  return (
    <>
      <motion.aside
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className={`fixed top-0 left-0 h-screen z-40 flex-col bg-[#070919]/95 backdrop-blur-xl border-r border-[#00ffff]/10 transition-all duration-300 hidden sm:flex ${
          collapsed ? "w-[72px]" : "w-[240px]"
        }`}
      >
        {sidebarContent}
      </motion.aside>

      <button
        onClick={onMobileToggle}
        className="fixed top-4 left-4 z-50 p-2.5 rounded-lg bg-[#070919]/90 border border-[#00ffff]/15 text-gray-400 hover:text-[#00ffff] transition-all sm:hidden"
      >
        <FaBars className="text-base" />
      </button>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onMobileToggle}
              className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm sm:hidden"
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed top-0 left-0 h-screen z-50 w-[280px] flex flex-col bg-[#070919]/98 backdrop-blur-xl border-r border-[#00ffff]/10 sm:hidden"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
