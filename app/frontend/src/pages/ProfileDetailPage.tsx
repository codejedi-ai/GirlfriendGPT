import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FaMapMarkerAlt, FaHeart, FaArrowLeft, FaComment, FaPhone } from "react-icons/fa";
import { HiSparkles, HiBolt } from "react-icons/hi2";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";
import { ImageSlideshow } from "@/components/ImageSlideshow";
import { useVoiceTalk } from "@/contexts/VoiceTalkContext";

export default function ProfileDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const { openTalk } = useVoiceTalk();

  useEffect(() => {
    async function fetchProfile() {
      const data = await api.getProfile(id!);
      if (data) setProfile(data as Profile);
      setLoading(false);
    }
    if (id) fetchProfile();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#00ffff]/30 border-t-[#00ffff] rounded-full animate-spin" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-500 mb-4">SIGNAL LOST</h2>
          <p className="text-gray-600 font-body mb-6">This profile could not be located</p>
          <Link
            to="/discover"
            className="inline-flex items-center gap-2 px-6 py-3 border border-[#00ffff]/30 text-[#00ffff] rounded-lg hover:bg-[#00ffff]/10 transition-all font-display text-sm tracking-wider"
          >
            <FaArrowLeft className="text-xs" />
            BACK TO DISCOVER
          </Link>
        </div>
      </div>
    );
  }

  const scorePercent = `${(profile.compatibility_score / 100) * 360}deg`;

  return (
    <div className="min-h-screen pb-20">
      <div className="relative h-[50vh] sm:h-[60vh] overflow-hidden">
        <ImageSlideshow
          urls={profile.banner_urls ?? (profile.banner_url ? [profile.banner_url] : [])}
          objectX={profile.banner_x}
          objectY={profile.banner_y}
          alt={profile.display_name}
          className="w-full h-full object-cover"
          interval={5000}
          fallback={<div className="w-full h-full bg-gradient-to-br from-[#0a0b1a] to-[#1a0b2e]" />}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#050714] via-[#050714]/60 to-transparent" />

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="absolute top-6 left-6"
        >
          <Link
            to="/discover"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[#050714]/80 backdrop-blur-sm border border-[#00ffff]/20 rounded-full text-[#00ffff] text-sm font-body hover:bg-[#050714] transition-all"
          >
            <FaArrowLeft className="text-xs" />
            Back
          </Link>
        </motion.div>

        <div className="absolute top-6 right-6 flex flex-col items-end gap-2">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full backdrop-blur-sm border ${
            profile.type === "ai"
              ? "bg-[#ff0080]/90 border-[#ff0080]/50"
              : "bg-[#00ffff]/90 border-[#00ffff]/50"
          }`}>
            <span className="text-xs text-black font-bold tracking-wider font-body">
              {profile.type === "ai" ? "AI COMPANION" : "HUMAN"}
            </span>
          </div>
          {profile.online_status && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#050714]/80 backdrop-blur-sm border border-[#00ff88]/30">
              <span className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse" />
              <span className="text-xs text-[#00ff88] font-medium tracking-wider font-body">ONLINE NOW</span>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 -mt-32 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="glass-panel rounded-2xl p-6 sm:p-8 mb-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6 mb-8">
              <div>
                <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
                  {profile.display_name}, {profile.age}
                </h1>
                <div className="flex items-center gap-2 text-gray-400 font-body">
                  <FaMapMarkerAlt className="text-[#ff0080] text-sm" />
                  {profile.location}
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="relative w-20 h-20 flex-shrink-0">
                  <div
                    className="absolute inset-0 rounded-full"
                    style={{
                      background: `conic-gradient(#00ffff ${scorePercent}, rgba(0,255,255,0.1) ${scorePercent})`,
                    }}
                  />
                  <div className="absolute inset-1 rounded-full bg-[#0a0b1a] flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-lg font-bold text-[#00ffff] font-display">{profile.compatibility_score}%</div>
                      <div className="text-[8px] text-gray-500 font-body uppercase tracking-wider">Match</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {profile.online_status ? (
              <div className="flex flex-col sm:flex-row gap-3 mb-8">
                <button
                  type="button"
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-[#ff0080] to-[#cc0066] text-white font-bold text-sm tracking-wider rounded-xl transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-[#ff0080]/20 font-display"
                >
                  <FaHeart />
                  SEND SIGNAL
                </button>
                {profile.type === "ai" ? (
                  <button
                    type="button"
                    onClick={() =>
                      openTalk(
                        profile.display_name,
                        profile.type === 'ai' ? profile.uuid || profile.id : undefined,
                      )
                    }
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 border border-[#00ffff]/30 text-[#00ffff] font-bold text-sm tracking-wider rounded-xl transition-all duration-300 hover:bg-[#00ffff]/10 hover:border-[#00ffff]/50 font-display"
                  >
                    <FaPhone />
                    TALK
                  </button>
                ) : (
                  <button
                    type="button"
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 border border-[#00ffff]/30 text-[#00ffff] font-bold text-sm tracking-wider rounded-xl transition-all duration-300 hover:bg-[#00ffff]/10 hover:border-[#00ffff]/50 font-display"
                  >
                    <FaComment />
                    MESSAGE
                  </button>
                )}
              </div>
            ) : (
              <div className="mb-8 p-6 rounded-xl border border-gray-700/50 bg-gray-900/20">
                <div className="flex items-center justify-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-gray-500" />
                  <span className="text-gray-500 font-medium tracking-wider font-body text-sm uppercase">
                    Not Available
                  </span>
                </div>
              </div>
            )}

            <div className="mb-8">
              <h2 className="text-sm font-bold text-gray-500 tracking-wider mb-3 uppercase">Looking For</h2>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#00ffff]/20 bg-[#00ffff]/5">
                <HiBolt className="text-[#00ffff] text-sm" />
                <span className="text-[#00ffff] text-sm font-medium font-body">{profile.looking_for}</span>
              </div>
            </div>

            <div className="mb-8">
              <h2 className="text-sm font-bold text-gray-500 tracking-wider mb-3 uppercase">About</h2>
              <p className="text-gray-300 font-body leading-relaxed">{profile.bio}</p>
            </div>

            <div>
              <h2 className="text-sm font-bold text-gray-500 tracking-wider mb-3 uppercase">Interests</h2>
              <div className="flex flex-wrap gap-2">
                {profile.interests.map((interest) => (
                  <span
                    key={interest}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-full border border-[#ff0080]/25 bg-[#ff0080]/5 text-sm text-[#ff0080] font-medium font-body transition-all hover:bg-[#ff0080]/10 hover:border-[#ff0080]/40"
                  >
                    <HiSparkles className="text-xs" />
                    {interest}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-6 sm:p-8">
            <h2 className="text-lg font-bold text-white mb-6">COMPATIBILITY BREAKDOWN</h2>
            <div className="space-y-4">
              {[
                { label: "Interests Alignment", value: Math.min(profile.compatibility_score + 3, 100) },
                { label: "Communication Style", value: Math.max(profile.compatibility_score - 5, 60) },
                { label: "Values Match", value: Math.min(profile.compatibility_score + 1, 100) },
                { label: "Lifestyle Sync", value: Math.max(profile.compatibility_score - 8, 55) },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-sm text-gray-400 font-body">{item.label}</span>
                    <span className="text-sm font-bold text-[#00ffff] font-display">{item.value}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#0a0b1a] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${item.value}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, ease: "easeOut" }}
                      className="h-full bg-gradient-to-r from-[#00ffff] to-[#0099cc] rounded-full"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
