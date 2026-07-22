import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { FaMapMarkerAlt, FaHeart } from "react-icons/fa";
import { HiSparkles } from "react-icons/hi2";
import type { Profile } from "@/lib/types";
import { ImageSlideshow } from "@/components/ImageSlideshow";
interface ProfileCardProps {
  profile: Profile;
}

export function ProfileCard({ profile }: ProfileCardProps) {
  const navigate = useNavigate();

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    navigate(`/profile/${profile.id}`);
  };

  return (
    <div onClick={handleClick}>
      <motion.div
        whileHover={{ y: -6, scale: 1.02 }}
        transition={{ duration: 0.3 }}
        className="glass-panel rounded-2xl overflow-hidden group cursor-pointer hover:border-[#00ffff]/30 transition-all duration-300"
      >
        <div className="relative h-64 overflow-hidden">
          <ImageSlideshow
            urls={profile.banner_urls ?? (profile.banner_url ? [profile.banner_url] : [])}
            objectX={profile.banner_x}
            objectY={profile.banner_y}
            alt={profile.display_name}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
            fallback={
              <div className="w-full h-full bg-gradient-to-br from-[#0a0b1a] to-[#1a0b2e] flex items-center justify-center">
                <span className="text-5xl font-bold text-[#00ffff]/30 font-display select-none">
                  {profile.display_name?.[0]?.toUpperCase() ?? "?"}
                </span>
              </div>
            }
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#050714] via-[#050714]/20 to-transparent" />

          <div className="absolute top-4 left-4 flex flex-col gap-2">
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full backdrop-blur-sm border ${
              profile.type === "ai"
                ? "bg-[#ff0080]/90 border-[#ff0080]/50"
                : "bg-[#00ffff]/90 border-[#00ffff]/50"
            }`}>
              <span className="text-[10px] text-black font-bold tracking-wider font-body uppercase">
                {profile.type === "ai" ? "🤖 AI" : "👤 Human"}
              </span>
            </div>
            {profile.online_status && (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#050714]/80 backdrop-blur-sm border border-[#00ff88]/30">
                <span className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse" />
                <span className="text-[10px] text-[#00ff88] font-medium tracking-wider font-body uppercase">Online</span>
              </div>
            )}
          </div>

          <div className="absolute top-4 right-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#050714]/80 backdrop-blur-sm border border-[#00ffff]/30">
            <HiSparkles className="text-[#00ffff] text-xs" />
            <span className="text-sm font-bold text-[#00ffff] font-display">{profile.compatibility_score}%</span>
          </div>

          <div className="absolute bottom-4 left-4 right-4">
            <h3 className="text-xl font-bold text-white mb-1">
              {profile.display_name}, {profile.age}
            </h3>
            <div className="flex items-center gap-1.5 text-gray-400 text-sm font-body">
              <FaMapMarkerAlt className="text-[#ff0080] text-xs" />
              {profile.location}
            </div>
          </div>
        </div>

        <div className="p-4">
          <p className="text-gray-400 text-sm font-body line-clamp-2 mb-3 leading-relaxed">
            {profile.bio}
          </p>

          <div className="flex flex-wrap gap-1.5 mb-4">
            {profile.interests.slice(0, 3).map((interest) => (
              <span
                key={interest}
                className="px-2.5 py-1 text-[10px] rounded-full border border-[#ff0080]/30 text-[#ff0080] bg-[#ff0080]/5 font-medium tracking-wider font-body uppercase"
              >
                {interest}
              </span>
            ))}
            {profile.interests.length > 3 && (
              <span className="px-2.5 py-1 text-[10px] rounded-full border border-gray-700 text-gray-500 font-medium font-body">
                +{profile.interests.length - 3}
              </span>
            )}
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500 font-body tracking-wider uppercase">{profile.looking_for}</span>
            <div className="w-8 h-8 rounded-full border border-[#ff0080]/30 flex items-center justify-center hover:bg-[#ff0080]/10 transition-colors">
              <FaHeart className="text-[#ff0080] text-xs" />
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
