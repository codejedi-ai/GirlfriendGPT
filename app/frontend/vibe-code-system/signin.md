import { useState } from "react"
import { Link } from "react-router-dom"
import { FaRobot, FaEye, FaEyeSlash, FaGoogle, FaDiscord, FaGithub } from "react-icons/fa"
import { HiSparkles } from "react-icons/hi2"

export function SignIn() {
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    // TODO: Implement authentication logic here
    console.log("Sign in attempt:", { email, password })
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
    }, 2000)
  }

  const handleSocialLogin = (provider: string) => {
    console.log(`Sign in with ${provider}`)
    // TODO: Implement social login
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#050714] relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#050714]/80 via-transparent to-[#050714]/80"></div>
      <div className="absolute inset-0" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2300ffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        opacity: 0.2
      }}></div>
      
      {/* Scan line effect */}
      <div className="scan-line opacity-30"></div>

      <div className="relative z-10 w-full max-w-md p-8">
        {/* Auth Card */}
        <div className="comic-panel p-8 backdrop-blur-md">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <FaRobot className="text-3xl text-[#00ffff]" />
              <h1 className="font-cyber text-2xl text-white">SIGN IN</h1>
              <HiSparkles className="text-2xl text-[#ff0080] animate-pulse" />
            </div>
            <p className="text-gray-300">
              Welcome back to <span className="text-[#00ffff]">Friends Wanted</span>
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Connect with your AI companions
            </p>
          </div>

          {/* Social Login Buttons */}
          <div className="space-y-3 mb-6">
            <button
              onClick={() => handleSocialLogin('google')}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 bg-white/10 border border-white/20 rounded-lg text-white hover:bg-white/20 transition-all duration-300 hover:scale-105"
            >
              <FaGoogle className="text-lg" />
              Continue with Google
            </button>
            
            <button
              onClick={() => handleSocialLogin('discord')}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 bg-[#5865F2]/20 border border-[#5865F2]/50 rounded-lg text-white hover:bg-[#5865F2]/30 transition-all duration-300 hover:scale-105"
            >
              <FaDiscord className="text-lg" />
              Continue with Discord
            </button>
            
            <button
              onClick={() => handleSocialLogin('github')}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 bg-gray-800/50 border border-gray-600/50 rounded-lg text-white hover:bg-gray-800/70 transition-all duration-300 hover:scale-105"
            >
              <FaGithub className="text-lg" />
              Continue with GitHub
            </button>
          </div>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-[#1f2937] text-gray-400">Or continue with email</span>
            </div>
          </div>

          {/* Email/Password Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-black/30 border border-[#00ffff]/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#00ffff] focus:ring-1 focus:ring-[#00ffff] transition-all duration-300"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 pr-12 bg-black/30 border border-[#00ffff]/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#00ffff] focus:ring-1 focus:ring-[#00ffff] transition-all duration-300"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-[#00ffff] transition-colors duration-300"
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember"
                  type="checkbox"
                  className="w-4 h-4 text-[#00ffff] bg-black/30 border-[#00ffff]/30 rounded focus:ring-[#00ffff] focus:ring-2"
                />
                <label htmlFor="remember" className="ml-2 block text-sm text-gray-300">
                  Remember me
                </label>
              </div>
              <Link
                to="/auth/forgot-password"
                className="text-sm text-[#00ffff] hover:text-[#c0fdff] transition-colors duration-300"
              >
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#00ffff] hover:bg-[#c0fdff] text-black font-bold py-3 px-4 rounded-lg transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-[#00ffff]/50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                  Signing In...
                </div>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Sign Up Link */}
          <div className="mt-6 text-center">
            <p className="text-gray-400">
              Don't have an account?{" "}
              <Link
                to="/auth/signup"
                className="text-[#00ffff] hover:text-[#c0fdff] font-medium transition-colors duration-300"
              >
                Sign up here
              </Link>
            </p>
          </div>

          {/* Back to Home */}
          <div className="mt-4 text-center">
            <Link
              to="/"
              className="text-sm text-gray-500 hover:text-gray-300 transition-colors duration-300"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
