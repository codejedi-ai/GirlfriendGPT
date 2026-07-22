import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { HiSparkles } from "react-icons/hi2";
import { FaEnvelope, FaLock, FaArrowRight } from "react-icons/fa";
import { useAuth } from "@/contexts/AuthContext";
import { PRODUCT_NAME } from "@/config/brand";

export default function SignUpPage() {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    const { error: err } = await signUp(email, password);
    setLoading(false);

    if (err) {
      setError(err);
    } else {
      navigate("/discover");
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-20 grid-bg relative">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#050714]/50 to-[#050714]" />
      <div className="absolute top-20 right-10 w-72 h-72 bg-[#ff0080]/5 rounded-full blur-3xl" />
      <div className="absolute bottom-20 left-10 w-96 h-96 bg-[#00ffff]/5 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="glass-panel rounded-2xl p-8 sm:p-10">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#ff0080] to-[#cc0066] flex items-center justify-center mb-4 shadow-lg shadow-[#ff0080]/20">
              <HiSparkles className="text-white text-2xl" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-wider font-display">
              CREATE ACCOUNT
            </h1>
            <p className="text-gray-500 text-sm mt-2 font-body">
              Join the {PRODUCT_NAME} network
            </p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-400 text-sm font-body text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs text-gray-400 tracking-wider font-display mb-2">
                EMAIL
              </label>
              <div className="relative">
                <FaEnvelope className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 rounded-lg bg-[#0a0b1a]/80 border border-[#ff0080]/15 text-white text-sm font-body placeholder-gray-600 focus:outline-none focus:border-[#ff0080]/50 focus:shadow-[0_0_12px_rgba(255,0,128,0.1)] transition-all"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-400 tracking-wider font-display mb-2">
                PASSWORD
              </label>
              <div className="relative">
                <FaLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 rounded-lg bg-[#0a0b1a]/80 border border-[#ff0080]/15 text-white text-sm font-body placeholder-gray-600 focus:outline-none focus:border-[#ff0080]/50 focus:shadow-[0_0_12px_rgba(255,0,128,0.1)] transition-all"
                  placeholder="Minimum 6 characters"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-400 tracking-wider font-display mb-2">
                CONFIRM PASSWORD
              </label>
              <div className="relative">
                <FaLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 rounded-lg bg-[#0a0b1a]/80 border border-[#ff0080]/15 text-white text-sm font-body placeholder-gray-600 focus:outline-none focus:border-[#ff0080]/50 focus:shadow-[0_0_12px_rgba(255,0,128,0.1)] transition-all"
                  placeholder="Re-enter your password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 py-3.5 bg-gradient-to-r from-[#ff0080] to-[#cc0066] text-white font-bold text-xs tracking-wider rounded-lg transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-[#ff0080]/30 font-display disabled:opacity-50 disabled:hover:scale-100"
            >
              {loading ? "CREATING ACCOUNT..." : "CREATE ACCOUNT"}
              {!loading && <FaArrowRight className="text-[10px]" />}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-gray-500 text-sm font-body">
              Already have an account?{" "}
              <Link
                to="/login"
                className="text-[#ff0080] hover:text-[#ff66b3] transition-colors font-medium"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
