import { useState } from "react"
import { Link } from "react-router-dom"
import { FaRobot, FaEye, FaEyeSlash, FaGoogle, FaDiscord, FaGithub, FaCheck } from "react-icons/fa"
import { HiSparkles } from "react-icons/hi2"

export function SignUp() {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: ""
  })
  const [agreedToTerms, setAgreedToTerms] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (formData.password !== formData.confirmPassword) {
      alert("Passwords don't match!")
      return
    }
    
    if (!agreedToTerms) {
      alert("Please agree to the terms and conditions")
      return
    }
    
    setIsLoading(true)
    
    // TODO: Implement registration logic here
    console.log("Sign up attempt:", formData)
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
    }, 2000)
  }

  const handleSocialLogin = (provider: string) => {
    console.log(`Sign up with ${provider}`)
    // TODO: Implement social login
  }

  const passwordsMatch = formData.password && formData.confirmPassword && formData.password === formData.confirmPassword

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#050714] relative overflow-hidden py-12">
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
              <h1 className="font-cyber text-2xl text-white">SIGN UP</h1>
              <HiSparkles className="text-2xl text-[#ff0080] animate-pulse" />
            </div>
            <p className="text-gray-300">
              Join <span className="text-[#00ffff]">Friends Wanted</span>
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Start connecting with AI companions
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
              <span className="px-4 bg-[#1f2937] text-gray-400">Or create account with email</span>
            </div>
          </div>

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">
                Full Name
              </label>
              <input
                id="name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-3 bg-black/30 border border-[#00ffff]/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#00ffff] focus:ring-1 focus:ring-[#00ffff] transition-all duration-300"
                placeholder="Enter your full name"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
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
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 pr-12 bg-black/30 border border-[#00ffff]/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#00ffff] focus:ring-1 focus:ring-[#00ffff] transition-all duration-300"
                  placeholder="Create a strong password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-[#00ffff] transition-colors duration-300"
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
              <div className="mt-2 text-xs text-gray-400">
                Password should be at least 8 characters long
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  required
                  className={`w-full px-4 py-3 pr-12 bg-black/30 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-1 transition-all duration-300 ${
                    formData.confirmPassword 
                      ? passwordsMatch 
                        ? "border-green-500 focus:border-green-500 focus:ring-green-500" 
                        : "border-red-500 focus:border-red-500 focus:ring-red-500"
                      : "border-[#00ffff]/30 focus:border-[#00ffff] focus:ring-[#00ffff]"
                  }`}
                  placeholder="Confirm your password"
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
                  {formData.confirmPassword && passwordsMatch && (
                    <FaCheck className="text-green-500" />
                  )}
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="text-gray-400 hover:text-[#00ffff] transition-colors duration-300"
                  >
                    {showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
                  </button>
                </div>
              </div>
              {formData.confirmPassword && !passwordsMatch && (
                <div className="mt-2 text-xs text-red-400">
                  Passwords don't match
                </div>
              )}
            </div>

            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="terms"
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  className="w-4 h-4 text-[#00ffff] bg-black/30 border-[#00ffff]/30 rounded focus:ring-[#00ffff] focus:ring-2"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="terms" className="text-gray-300">
                  I agree to the{" "}
                  <Link to="/terms" className="text-[#00ffff] hover:text-[#c0fdff] transition-colors duration-300">
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link to="/privacy" className="text-[#00ffff] hover:text-[#c0fdff] transition-colors duration-300">
                    Privacy Policy
                  </Link>
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !agreedToTerms}
              className="w-full bg-[#00ffff] hover:bg-[#c0fdff] text-black font-bold py-3 px-4 rounded-lg transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-[#00ffff]/50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                  Creating Account...
                </div>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          {/* Sign In Link */}
          <div className="mt-6 text-center">
            <p className="text-gray-400">
              Already have an account?{" "}
              <Link
                to="/auth/signin"
                className="text-[#00ffff] hover:text-[#c0fdff] font-medium transition-colors duration-300"
              >
                Sign in here
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
