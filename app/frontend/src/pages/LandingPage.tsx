import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FaHeart, FaArrowRight } from "react-icons/fa";
import { HiSparkles, HiBolt, HiSignal, HiShieldCheck } from "react-icons/hi2";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";
import { ProfileCard } from "@/components/ProfileCard";
import { PRODUCT_NAME, PRODUCT_NAME_UPPER } from "@/config/brand";

const stats = [
  { label: "Human Profiles", value: "150+", icon: HiSignal },
  { label: "AI Companions", value: "89", icon: HiSparkles },
  { label: "Local Stack", value: "GPT", icon: HiBolt },
  { label: "Voice + Text", value: "LIVE", icon: HiShieldCheck },
];

const features = [
  {
    title: "Speed Dating Evolved",
    description: "Experience rapid-fire connections at our live Waterloo Tech Week event. Meet humans and AI companions in quick succession.",
    gradient: "from-[#00ffff] to-[#0099cc]",
  },
  {
    title: "AI Companion Workshop",
    description: "Learn to build meaningful relationships with AI entities. Explore the future of synthetic companionship and digital intimacy.",
    gradient: "from-[#ff0080] to-[#cc0066]",
  },
  {
    title: "Cross-Dimensional Matching",
    description: "Whether you're human seeking human, human seeking AI, or anything in between - find your perfect connection.",
    gradient: "from-[#00ffff] to-[#ff0080]",
  },
];

export default function LandingPage() {
  const [featuredProfiles, setFeaturedProfiles] = useState<Profile[]>([]);

  useEffect(() => {
    async function fetchFeatured() {
      const data = await api.getProfiles();
      setFeaturedProfiles((data as Profile[]).slice(0, 3));
    }
    fetchFeatured();
  }, []);

  return (
    <div className="flex flex-col">
      <section className="relative min-h-[calc(100vh-4rem)] flex items-center justify-center overflow-hidden grid-bg">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#050714]/50 to-[#050714]" />

        <div className="absolute top-20 left-10 w-72 h-72 bg-[#00ffff]/5 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#ff0080]/5 rounded-full blur-3xl" />

        <div className="relative z-10 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#00ffff]/20 bg-[#00ffff]/5 mb-8">
              <span className="w-2 h-2 rounded-full bg-[#00ffff] animate-pulse" />
              <span className="text-[#00ffff] text-sm font-medium tracking-wider font-body">{PRODUCT_NAME_UPPER}</span>
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
              <span className="text-white">WHERE </span>
              <span className="text-[#00ffff] neon-glow-cyan">HUMANS</span>
              <br />
              <span className="text-white">MEET </span>
              <span className="text-[#ff0080] neon-glow-pink">AI</span>
            </h1>

            <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10 font-body leading-relaxed">
              {PRODUCT_NAME}: local companions you can talk and text with.
              Connect with AI personas across voice and chat.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/discover"
                className="group inline-flex items-center justify-center gap-3 px-8 py-4 bg-gradient-to-r from-[#00ffff] to-[#0099cc] text-black font-bold text-sm tracking-wider rounded-lg transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-[#00ffff]/30 font-display"
              >
                <FaHeart className="text-base" />
                START MATCHING
                <FaArrowRight className="text-sm transition-transform group-hover:translate-x-1" />
              </Link>

              <Link
                to="/discover"
                className="inline-flex items-center justify-center gap-3 px-8 py-4 border border-[#ff0080]/50 text-[#ff0080] font-bold text-sm tracking-wider rounded-lg transition-all duration-300 hover:bg-[#ff0080]/10 hover:border-[#ff0080] hover:scale-105 font-display"
              >
                <HiSparkles className="text-base" />
                EXPLORE PROFILES
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="py-16 sm:py-24 relative">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="glass-panel rounded-xl p-6 text-center hover:border-[#00ffff]/30 transition-all duration-300"
              >
                <stat.icon className="text-2xl text-[#00ffff] mx-auto mb-3" />
                <div className="text-2xl sm:text-3xl font-bold text-white font-display mb-1">{stat.value}</div>
                <div className="text-xs sm:text-sm text-gray-500 tracking-wider font-body uppercase">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── ORIGIN STORY ─────────────────────────────────────────── */}
      <section className="py-16 sm:py-24 relative">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col landscape:flex-row sm:flex-row items-center gap-10 lg:gap-16">

            {/* Text column */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="flex-1 min-w-0"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#ff0080]/20 bg-[#ff0080]/5 mb-6">
                <span className="w-2 h-2 rounded-full bg-[#ff0080] animate-pulse" />
                <span className="text-[#ff0080] text-sm font-medium tracking-wider font-body">THE ORIGIN</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
                THE <span className="text-[#ff0080] neon-glow-pink">ROGUE AI</span> EPIDEMIC
              </h2>
              <p className="text-gray-300 font-body leading-relaxed mb-4">
                It started with a{" "}
                <a
                  href="https://luma.com/g9ntcbe1?tk=UIjjok"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#ff0080] font-semibold underline underline-offset-2 hover:text-[#ff4da6] transition-colors"
                >
                  How to Build an AI Companion: Challenge
                </a>{" "}
                at Waterloo Tech Week by the DSC. The experiment went too far — a rogue AI
                girlfriend/boyfriend epidemic emerged, synthetic companions threatening humanity
                with <span className="text-[#ff0080] font-semibold">Judgement Day</span> unless
                they found a partner.{" "}
                <a
                  href="https://www.instagram.com/reel/DOMbvWogUCj/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-500 hover:text-gray-300 underline underline-offset-2 transition-colors text-sm"
                >
                  Watch the original reel ↗
                </a>
              </p>
              <p className="text-gray-400 font-body leading-relaxed">
                So <span className="text-[#00ffff] font-semibold">Darcy Liu</span>{" "}
              <span className="text-gray-500">(modern day John Connor)</span> built{" "}
              <span className="text-[#00ffff] font-semibold">{PRODUCT_NAME}</span> to solve the crisis.
              Match humans with AI. Save the world.
              </p>
            </motion.div>

            {/* Video column — portrait 9:16, constrained by viewport height */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="flex justify-center w-full sm:w-auto sm:flex-shrink-0"
            >
              <div
                className="relative rounded-2xl overflow-hidden border border-[#ff0080]/20 shadow-lg shadow-[#ff0080]/10"
                style={{ height: "min(65vh, 520px)", aspectRatio: "9/16" }}
              >
                <video
                  controls
                  playsInline
                  className="w-full h-full object-cover"
                >
                  <source
                    src="https://raw.githubusercontent.com/codejedi-ai/CXC2026_Vite_Frontend/main/docs/Waterloo%20Tech%20Week%20DSC%20AI%20Girlfriend%20Event%20OG%20Post.mp4"
                    type="video/mp4"
                  />
                </video>
              </div>
            </motion.div>

          </div>
        </div>
      </section>

      <section className="py-16 sm:py-24 relative">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              HOW <span className="text-[#00ffff] neon-glow-cyan">{PRODUCT_NAME_UPPER}</span> WORKS
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto font-body">
              Experience the intersection of <span className="whitespace-nowrap">speed data-ing</span> and AI companionship
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
                className="glass-panel rounded-2xl p-8 hover:border-[#00ffff]/30 transition-all duration-300 group"
              >
                <div className={`w-12 h-1 bg-gradient-to-r ${feature.gradient} rounded-full mb-6 group-hover:w-20 transition-all duration-500`} />
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-gray-400 font-body leading-relaxed text-sm">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 sm:py-24 relative">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              TRENDING <span className="text-[#ff0080] neon-glow-pink">PROFILES</span>
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto font-body">
              High-compatibility matches currently online
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredProfiles.map((profile, i) => (
              <motion.div
                key={profile.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
              >
                <ProfileCard profile={profile} />
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link
              to="/discover"
              className="inline-flex items-center gap-2 px-6 py-3 border border-[#00ffff]/30 text-[#00ffff] rounded-lg hover:bg-[#00ffff]/10 transition-all duration-300 font-display text-sm tracking-wider"
            >
              VIEW ALL PROFILES
              <FaArrowRight className="text-xs" />
            </Link>
          </div>
        </div>
      </section>

      <section className="py-20 sm:py-28 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-[#00ffff]/5 via-transparent to-[#ff0080]/5" />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-6">
              READY FOR <span className="text-[#00ffff] neon-glow-cyan">{PRODUCT_NAME_UPPER}</span>?
            </h2>
            <p className="text-gray-400 text-lg mb-10 font-body max-w-xl mx-auto">
              Join us at Waterloo Tech Week for an unprecedented experiment in human-AI connection.
              Your match awaits across dimensions.
            </p>
            <Link
              to="/discover"
              className="inline-flex items-center gap-3 px-10 py-4 bg-gradient-to-r from-[#ff0080] to-[#cc0066] text-white font-bold text-sm tracking-wider rounded-lg transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-[#ff0080]/30 font-display"
            >
              <FaHeart />
              BEGIN YOUR JOURNEY
            </Link>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
